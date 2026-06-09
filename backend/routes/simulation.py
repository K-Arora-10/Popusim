from fastapi import APIRouter, HTTPException, BackgroundTasks
import uuid
import logging
from datetime import datetime
from typing import List

from backend.db import get_db
from backend.models import SimulationStartRequest, SimulationStatusResponse, PersonaSchema
from backend.orchestrator import run_simulation
from backend.routes.ws import manager

logger = logging.getLogger("popusim.routes.simulation")
router = APIRouter()

@router.post("/simulation/start")
async def start_simulation(request: SimulationStartRequest, background_tasks: BackgroundTasks):
    """
    Submits a new simulation. Spawns background worker execution context.
    """
    # Clean and validate URL
    url = request.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
        
    simulation_id = f"sim_{uuid.uuid4().hex[:8]}"
    created_at = datetime.now().isoformat()
    
    # Save pending simulation entry
    db_conn = await get_db()
    try:
        await db_conn.execute(
            "INSERT INTO simulations (id, url, status, created_at, use_shared_session) VALUES (?, ?, ?, ?, ?)",
            (simulation_id, url, "pending", created_at, 1 if request.use_shared_session else 0)
        )
        await db_conn.commit()
    except Exception as e:
        logger.error(f"Failed to initialize simulation in DB: {e}")
        raise HTTPException(status_code=500, detail="Database error initiating simulation session.")
    finally:
        await db_conn.close()
        
    # Helper log callback to broadcast live events
    async def log_callback(message_payload: dict):
        # Broadcast to WS subscribers
        await manager.broadcast(message_payload, simulation_id)
        
    # Start task in background using FastAPI's background tasks
    background_tasks.add_task(
        run_simulation,
        simulation_id=simulation_id,
        url=url,
        num_personas=request.num_personas,
        use_shared_session=request.use_shared_session,
        log_callback=log_callback
    )
    
    return {"simulation_id": simulation_id, "status": "pending", "url": url}

@router.get("/simulation/history")
async def get_simulation_history():
    """
    Lists past run records.
    """
    db_conn = await get_db()
    try:
        async with db_conn.execute("SELECT * FROM simulations ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
            
        history = []
        for r in rows:
            history.append({
                "id": r["id"],
                "url": r["url"],
                "status": r["status"],
                "created_at": r["created_at"],
                "nps": r["nps"],
                "churn_rate": r["churn_rate"],
                "wtp": r["wtp"]
            })
        return history
    except Exception as e:
        logger.error(f"Error reading history: {e}")
        raise HTTPException(status_code=500, detail="Database read error.")
    finally:
        await db_conn.close()

@router.get("/simulation/{simulation_id}/status", response_model=SimulationStatusResponse)
async def get_simulation_status(simulation_id: str):
    """
    Retrieves current state of a running or finished simulation.
    """
    db_conn = await get_db()
    try:
        # Get simulation
        async with db_conn.execute("SELECT * FROM simulations WHERE id = ?", (simulation_id,)) as cursor:
            sim_row = await cursor.fetchone()
            
        if not sim_row:
            raise HTTPException(status_code=404, detail="Simulation session not found.")
            
        # Get personas
        async with db_conn.execute("SELECT * FROM personas WHERE simulation_id = ?", (simulation_id,)) as cursor:
            persona_rows = await cursor.fetchall()
            
        import json
        personas = []
        for pr in persona_rows:
            try:
                goals_list = json.loads(pr["goals"])
            except Exception:
                goals_list = [pr["goals"]]
                
            personas.append(PersonaSchema(
                id=pr["id"],
                simulation_id=pr["simulation_id"],
                name=pr["name"],
                archetype=pr["archetype"],
                goals=goals_list,
                impatience=pr["impatience"],
                tech_savviness=pr["tech_savviness"],
                price_sensitivity=pr["price_sensitivity"],
                support_reliance=pr["support_reliance"],
                status=pr["status"]
            ))
            
        return SimulationStatusResponse(
            id=sim_row["id"],
            url=sim_row["url"],
            status=sim_row["status"],
            created_at=datetime.fromisoformat(sim_row["created_at"]),
            nps=sim_row["nps"],
            churn_rate=sim_row["churn_rate"],
            wtp=sim_row["wtp"],
            personas=personas,
            use_shared_session=bool(sim_row["use_shared_session"])
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading status: {e}")
        raise HTTPException(status_code=500, detail="Database status query failed.")
    finally:
        await db_conn.close()

@router.delete("/simulation/{simulation_id}")
async def delete_simulation(simulation_id: str):
    """
    Cleans up a simulation run and associated DB records.
    """
    db_conn = await get_db()
    try:
        await db_conn.execute("DELETE FROM simulations WHERE id = ?", (simulation_id,))
        await db_conn.commit()
        return {"status": "deleted", "simulation_id": simulation_id}
    except Exception as e:
        logger.error(f"Failed to delete simulation: {e}")
        raise HTTPException(status_code=500, detail="Database write error during deletion.")
    finally:
        await db_conn.close()

@router.get("/simulation/{simulation_id}/logs")
async def get_simulation_logs(simulation_id: str):
    """
    Retrieves all agent logs sorted by step number for a simulation session.
    Returns format mapping: persona_id -> list of steps.
    """
    db_conn = await get_db()
    try:
        async with db_conn.execute(
            "SELECT * FROM agent_logs WHERE simulation_id = ? ORDER BY step_number ASC",
            (simulation_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            
        logs_by_persona = {}
        for r in rows:
            p_id = r["persona_id"]
            if p_id not in logs_by_persona:
                logs_by_persona[p_id] = []
            
            logs_by_persona[p_id].append({
                "step": r["step_number"],
                "action": r["action"],
                "url": r["url"],
                "description": r["description"],
                "screenshot": r["screenshot_filename"],
                "reason": r["reason"],
                "timestamp": r["timestamp"]
            })
        return logs_by_persona
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail="Database read error.")
    finally:
        await db_conn.close()

