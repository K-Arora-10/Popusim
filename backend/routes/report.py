from fastapi import APIRouter, HTTPException
import json
import logging
from datetime import datetime
from typing import List, Any


from backend.db import get_db
from backend.models import ReportResponse, BugSchema, ChatRequest, ChatMessageSchema
from backend.config import settings


logger = logging.getLogger("popusim.routes.report")
router = APIRouter()

@router.get("/simulation/{simulation_id}/report", response_model=ReportResponse)
async def get_simulation_report(simulation_id: str):
    """
    Fetches the synthesized report for a simulation.
    """
    db_conn = await get_db()
    try:
        # Check if report exists
        async with db_conn.execute("SELECT * FROM reports WHERE simulation_id = ?", (simulation_id,)) as cursor:
            report_row = await cursor.fetchone()
            
        if not report_row:
            # Check if simulation exists and is completed. If not completed, return 400
            async with db_conn.execute("SELECT status FROM simulations WHERE id = ?", (simulation_id,)) as cursor:
                sim_row = await cursor.fetchone()
            if not sim_row:
                raise HTTPException(status_code=404, detail="Simulation session not found.")
            if sim_row["status"] != "completed":
                raise HTTPException(status_code=400, detail=f"Report is not ready. Simulation status: {sim_row['status']}")
                
            raise HTTPException(status_code=404, detail="Report row missing despite simulation completion.")
            
        # Parse bugs JSON
        try:
            bugs_list = json.loads(report_row["bugs"])
        except Exception:
            bugs_list = []
            
        bugs = []
        for b in bugs_list:
            bugs.append(BugSchema(
                severity=b.get("severity", "Minor"),
                description=b.get("description", "Unknown issue"),
                selector=b.get("selector"),
                url=b.get("url"),
                screenshot=b.get("screenshot")
            ))
            
        return ReportResponse(
            id=report_row["id"],
            simulation_id=report_row["simulation_id"],
            nps=report_row["nps"],
            churn_rate=report_row["churn_rate"],
            wtp=report_row["wtp"],
            bugs=bugs,
            summary=report_row["summary"],
            created_at=datetime.fromisoformat(report_row["created_at"])
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching report: {e}")
        raise HTTPException(status_code=500, detail="Database error retrieving report.")
    finally:
        await db_conn.close()

@router.get("/simulation/{simulation_id}/chat/history")
async def get_chat_history(simulation_id: str):
    """
    Retrieves previous chat conversations with SimGPT about the simulation results.
    """
    db_conn = await get_db()
    try:
        async with db_conn.execute(
            "SELECT * FROM chat_messages WHERE simulation_id = ? ORDER BY timestamp ASC",
            (simulation_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            
        history = []
        for r in rows:
            history.append({
                "id": r["id"],
                "role": r["role"],
                "content": r["content"],
                "timestamp": r["timestamp"]
            })
        return history
    except Exception as e:
        logger.error(f"Error reading chat history: {e}")
        raise HTTPException(status_code=500, detail="Database read error.")
    finally:
        await db_conn.close()

@router.post("/simulation/{simulation_id}/chat")
async def chat_with_analyst(simulation_id: str, request: ChatRequest):
    """
    Queries details about a completed simulation via an AI assistant.
    Combines agent execution logs and bugs database context.
    """
    user_message = request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
        
    db_conn = await get_db()
    try:
        # 1. Fetch simulation, personas, and logs context
        async with db_conn.execute("SELECT * FROM simulations WHERE id = ?", (simulation_id,)) as cursor:
            sim_row = await cursor.fetchone()
        if not sim_row:
            raise HTTPException(status_code=404, detail="Simulation session not found.")
            
        async with db_conn.execute("SELECT * FROM personas WHERE simulation_id = ?", (simulation_id,)) as cursor:
            persona_rows = await cursor.fetchall()
            
        async with db_conn.execute("SELECT * FROM agent_logs WHERE simulation_id = ? ORDER BY timestamp ASC", (simulation_id,)) as cursor:
            log_rows = await cursor.fetchall()
            
        # Compile logs summary
        persona_map = {p["id"]: dict(p) for p in persona_rows}
        logs_by_agent = {}

        for l in log_rows:
            p_id = l["persona_id"]
            if p_id not in logs_by_agent:
                p_name = persona_map.get(p_id, {}).get("name", "Unknown User")
                p_arch = persona_map.get(p_id, {}).get("archetype", "Explorer")
                logs_by_agent[p_id] = {
                    "name": p_name,
                    "archetype": p_arch,
                    "status": persona_map.get(p_id, {}).get("status", "pending"),
                    "steps": []
                }
            logs_by_agent[p_id]["steps"].append(
                f"Step {l['step_number']}: {l['action']} on {l['url']} -> {l['description']} (Reason: {l['reason']})"
            )
            
        # Get chat history
        async with db_conn.execute(
            "SELECT role, content FROM chat_messages WHERE simulation_id = ? ORDER BY timestamp ASC",
            (simulation_id,)
        ) as cursor:
            chat_history_rows = await cursor.fetchall()
            
        chat_history = [{"role": r["role"], "content": r["content"]} for r in chat_history_rows]
        
        # 2. Add user message to DB
        timestamp = datetime.now().isoformat()
        await db_conn.execute(
            "INSERT INTO chat_messages (simulation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (simulation_id, "user", user_message, timestamp)
        )
        await db_conn.commit()
        
        # 3. Generate Answer
        assistant_content = ""
        
        if settings.GEMINI_API_KEY:
            # Query Gemini
            history_text = ""
            for name, data in logs_by_agent.items():
                history_text += f"\nAgent: {data['name']} ({data['archetype']}) - Status: {data['status']}\n"
                history_text += "\n".join(data["steps"]) + "\n"
                
            chat_history_text = "\n".join([f"{h['role'].capitalize()}: {h['content']}" for h in chat_history])
            
            prompt = f"""
            You are "SimGPT", the PopuSim AI Analyst. You have full visibility into a simulation run on {sim_row['url']}.
            NPS Score: {sim_row['nps']}
            Churn Rate: {sim_row['churn_rate']}%
            Willingness to Pay: {sim_row['wtp']}
            
            Here are the exact step-by-step logs of all autonomous users:
            {history_text}
            
            Analyze this data and answer the user's question. Focus on why specific users churned, friction patterns in the site design, and how to improve the UX. Keep the tone professional, analytical, and highly actionable.
            
            Here is the conversation history:
            {chat_history_text}
            
            User: {user_message}
            Assistant:
            """
            
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                
                async with client.aio as aclient:
                    response = await aclient.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        contents=prompt
                    )
                assistant_content = response.text
            except Exception as e:
                logger.error(f"Gemini chat failed: {e}. Falling back to smart mock chat assistant.")
                assistant_content = get_mock_chat_response(user_message, logs_by_agent, sim_row)
        else:
            # Sandbox Mock mode chat response
            assistant_content = get_mock_chat_response(user_message, logs_by_agent, sim_row)
            
        # 4. Save assistant reply in DB
        await db_conn.execute(
            "INSERT INTO chat_messages (simulation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (simulation_id, "assistant", assistant_content, datetime.now().isoformat())
        )
        await db_conn.commit()
        
        return {"response": assistant_content}
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error answering chat message.")
    finally:
        await db_conn.close()

def get_mock_chat_response(message: str, logs_by_agent: dict, sim_row: Any) -> str:
    """
    Locally processes chat queries using rule-based parsing of the simulation state.
    Provides context-aware analysis even without API keys.
    """
    msg = message.lower()
    
    # 1. Look for persona name mentions
    matching_agent = None
    for agent_id, data in logs_by_agent.items():
        if data["name"].lower() in msg or data["archetype"].lower() in msg:
            matching_agent = data
            break
            
    if matching_agent:
        name = matching_agent["name"]
        arch = matching_agent["archetype"]
        status = matching_agent["status"]
        steps = matching_agent["steps"]
        
        step_details = "\n".join([f"- {s}" for s in steps])
        
        if status == "churned":
            return f"**Analysis of {name} ({arch}):**\n\n{name} had a status of **Churned**. According to the agent logs, they abandoned the flow because of high impatience or errors encountered. Here is their step history:\n\n{step_details}\n\n**Recommendation:** To retain users like {name}, simplify the interactive elements on pages they got stuck on."
        else:
            return f"**Analysis of {name} ({arch}):**\n\n{name} had a status of **Completed**. They navigated the product successfully. Here is their browsing history:\n\n{step_details}\n\nThis user successfully converted, showing that the flow is usable for tech-savvy/patient users, but may still contain micro-friction."

    # 2. General queries about churn
    if "churn" in msg or "abandon" in msg or "leave" in msg:
        churned_agents = [d["name"] + f" ({d['archetype']})" for d in logs_by_agent.values() if d["status"] == "churned"]
        if churned_agents:
            return f"The simulation recorded a **{sim_row['churn_rate']}% Churn Rate**. The users who abandoned were:\n\n" + \
                   "\n".join([f"- {name}" for name in churned_agents]) + \
                   "\n\nCommon drop-off reasons: High impatience, confusing form inputs, and slow UI navigation response times."
        else:
            return "No users churned during this simulation. All generated personas successfully completed their goals!"

    # 3. Queries about bugs
    if "bug" in msg or "error" in msg or "broken" in msg:
        return "Bugs were detected by users during natural exploration. The most common issues are console runtime exceptions and unresponsive DOM selectors. You can review the full details and selectors in the **Bug Feed** tab of the dashboard."

    # 4. Fallback response
    return f"Hello! I am the PopuSim Analyst. Based on this simulation of **{sim_row['url']}**:\n" + \
           f"- NPS Score is **{sim_row['nps']}**\n" + \
           f"- Churn Rate is **{sim_row['churn_rate']}%**\n" + \
           f"- Willingness to Pay is **{sim_row['wtp']}**\n\n" + \
           "Ask me about a specific user (e.g. *'Why did Sarah Jenkins churn?'*) or general UX recommendation queries."
