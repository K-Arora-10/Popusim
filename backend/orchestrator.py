import asyncio
import logging
from datetime import datetime
import json
from typing import Dict, Any, Callable
from playwright.async_api import async_playwright

from backend.config import settings
from backend.db import get_db
from backend.ingestion import ingest_website
from backend.persona_factory import generate_personas
from backend.agent import AutonomousAgent
from backend.synthesis import synthesize_report

logger = logging.getLogger("popusim.orchestrator")

async def run_simulation(
    simulation_id: str,
    url: str,
    num_personas: int,
    log_callback: Callable[[Dict[str, Any]], Any],
    use_shared_session: bool = False
):
    """
    Orchestrates the entire simulation:
    1. Ingestion of the website
    2. Generation of personas
    3. Running Playwright agents concurrently
    4. Collecting behaviors and bugs
    5. Synthesis of report using Claude
    """
    logger.info(f"Starting orchestrator for simulation {simulation_id} on {url} (shared session: {use_shared_session})")
    db_conn = await get_db()
    
    try:
        # 1. Update simulation status to 'ingesting'
        await db_conn.execute(
            "UPDATE simulations SET status = ? WHERE id = ?",
            ("ingesting", simulation_id)
        )
        # Also store the use_shared_session flag in the database
        await db_conn.execute(
            "UPDATE simulations SET use_shared_session = ? WHERE id = ?",
            (1 if use_shared_session else 0, simulation_id)
        )
        await db_conn.commit()
        
        # Broadcast status update
        await log_callback({
            "type": "status_update",
            "simulation_id": simulation_id,
            "status": "ingesting",
            "message": "Ingesting target website content..."
        })
        
        # Crawl site content
        site_data = await ingest_website(url)
        
        # 2. Update status to 'generating_personas'
        await db_conn.execute(
            "UPDATE simulations SET status = ? WHERE id = ?",
            ("generating_personas", simulation_id)
        )
        await db_conn.commit()
        
        await log_callback({
            "type": "status_update",
            "simulation_id": simulation_id,
            "status": "generating_personas",
            "message": "Analyzing layout & generating synthetic personas..."
        })
        
        # Generate user profiles
        personas = await generate_personas(simulation_id, url, site_data, num_personas)
        
        # Save personas to DB
        for p in personas:
            # Goals list is stored as a JSON string in DB
            goals_str = json.dumps(p["goals"])
            await db_conn.execute(
                """
                INSERT INTO personas (id, simulation_id, name, archetype, goals, impatience, tech_savviness, price_sensitivity, support_reliance, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    p["id"],
                    simulation_id,
                    p["name"],
                    p["archetype"],
                    goals_str,
                    p["impatience"],
                    p["tech_savviness"],
                    p["price_sensitivity"],
                    p["support_reliance"],
                    "pending"
                )
            )
        await db_conn.commit()
        
        # Broadcast list of generated personas to frontend
        await log_callback({
            "type": "personas_generated",
            "simulation_id": simulation_id,
            "personas": personas
        })
        
        # 3. Update status to 'running' (Agent Simulation)
        await db_conn.execute(
            "UPDATE simulations SET status = ? WHERE id = ?",
            ("running", simulation_id)
        )
        await db_conn.commit()
        
        await log_callback({
            "type": "status_update",
            "simulation_id": simulation_id,
            "status": "running",
            "message": "Launching headless browser swarm..."
        })
        
        # Launch Playwright Browser and run agents in parallel
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Instantiate agents
            agents = []
            for persona_data in personas:
                agent = AutonomousAgent(
                    simulation_id=simulation_id,
                    persona=persona_data,
                    db_conn=db_conn,
                    log_callback=log_callback,
                    use_shared_session=use_shared_session
                )
                agents.append(agent)
                
            # Run all agents in parallel
            tasks = [agent.run(browser) for agent in agents]
            await asyncio.gather(*tasks)
            await browser.close()
            
        # 4. Compile outcomes, logs, and bugs
        logger.info(f"Gathering logs for synthesis of simulation {simulation_id}")
        
        # Gather bugs
        all_bugs = []
        for agent in agents:
            all_bugs.extend(agent.bugs_detected)
            
        # 5. Update status to 'synthesizing'
        await db_conn.execute(
            "UPDATE simulations SET status = ? WHERE id = ?",
            ("synthesizing", simulation_id)
        )
        await db_conn.commit()
        
        await log_callback({
            "type": "status_update",
            "simulation_id": simulation_id,
            "status": "synthesizing",
            "message": "Synthesizing agent session recordings..."
        })
        
        # Run synthesizer
        report_data = await synthesize_report(simulation_id, url, personas, agents, all_bugs)
        
        # Save Report in DB
        report_id = f"rep_{simulation_id[4:]}" if simulation_id.startswith("sim_") else f"rep_{simulation_id[:8]}"
        await db_conn.execute(
            """
            INSERT INTO reports (id, simulation_id, nps, churn_rate, wtp, bugs, summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                simulation_id,
                report_data["nps"],
                report_data["churn_rate"],
                report_data["wtp"],
                json.dumps(report_data["bugs"]),
                report_data["summary"],
                datetime.now().isoformat()
            )
        )
        
        # Update simulation record with scores
        await db_conn.execute(
            """
            UPDATE simulations 
            SET status = ?, nps = ?, churn_rate = ?, wtp = ?
            WHERE id = ?
            """,
            (
                "completed",
                report_data["nps"],
                report_data["churn_rate"],
                report_data["wtp"],
                simulation_id
            )
        )
        await db_conn.commit()
        
        # Broadcast simulation completion
        await log_callback({
            "type": "simulation_complete",
            "simulation_id": simulation_id,
            "report_id": report_id,
            "nps": report_data["nps"],
            "churn_rate": report_data["churn_rate"],
            "wtp": report_data["wtp"],
            "bugs": report_data["bugs"],
            "summary": report_data["summary"]
        })
        
    except Exception as e:
        logger.error(f"Orchestration failure on simulation {simulation_id}: {e}")
        try:
            await db_conn.execute(
                "UPDATE simulations SET status = ? WHERE id = ?",
                ("failed", simulation_id)
            )
            await db_conn.commit()
            
            await log_callback({
                "type": "status_update",
                "simulation_id": simulation_id,
                "status": "failed",
                "message": f"Simulation failed: {str(e)}"
            })
        except Exception as db_err:
            logger.error(f"Failed to record orchestration error to DB: {db_err}")
    finally:
        await db_conn.close()
