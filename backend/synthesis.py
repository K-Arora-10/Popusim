import json
import logging
from typing import List, Dict, Any
from backend.config import settings


logger = logging.getLogger("popusim.synthesis")

async def synthesize_report(
    simulation_id: str,
    url: str,
    personas: List[Dict[str, Any]],
    agents: List[Any],
    bugs: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Synthesizes the final intelligence report.
    If ANTHROPIC_API_KEY is available, queries Claude.
    Otherwise, executes a local rule-based analysis.
    """
    logger.info(f"Synthesizing report for simulation {simulation_id}...")
    
    # 1. Prepare raw logs for LLM context
    logs_summary = []
    for agent in agents:
        agent_steps = []
        for step in agent.history:
            agent_steps.append(f"Step {step['step']}: Action={step['action']} | URL={step['url']} | Desc={step['desc']} | Reason={step.get('reason', '')}")
            
        logs_summary.append({
            "persona_name": agent.persona["name"],
            "archetype": agent.persona["archetype"],
            "status": agent.status,
            "goals": agent.persona["goals"],
            "traits": {
                "impatience": agent.persona["impatience"],
                "tech_savviness": agent.persona["tech_savviness"],
                "price_sensitivity": agent.persona["price_sensitivity"]
            },
            "steps": agent_steps,
            "bugs_encountered": len(agent.bugs_detected)
        })

    # De-duplicate bugs
    unique_bugs = []
    seen_bug_descriptions = set()
    for b in bugs:
        desc = b.get("description", "")
        if desc not in seen_bug_descriptions:
            seen_bug_descriptions.add(desc)
            unique_bugs.append(b)

    # 2. Rule-based analysis for sandbox fallback (or direct computation)
    # This also acts as backup if Anthropic API throws quota/rate errors
    nps_ratings = []
    churned_count = 0
    completed_count = 0
    
    for agent in agents:
        if agent.status == "churned":
            churned_count += 1
            # Churned agents rating range 2-6
            rating = max(2, min(6, int(8 - (agent.persona["impatience"] * 5) - len(agent.bugs_detected))))
        else:
            completed_count += 1
            # Completed agents rating range 7-10
            rating = max(6, min(10, int(9 + (agent.persona["tech_savviness"] * 2) - len(agent.bugs_detected) - (agent.persona["price_sensitivity"] * 2))))
        nps_ratings.append(rating)
        
    promoters = sum(1 for r in nps_ratings if r >= 9)
    detractors = sum(1 for r in nps_ratings if r <= 6)
    total_agents = len(agents) if agents else 1
    computed_nps = int(((promoters - detractors) / total_agents) * 100)
    computed_churn = float((churned_count / total_agents) * 100)
    
    # Evaluate WTP
    avg_price_sensitivity = sum(p["price_sensitivity"] for p in personas) / len(personas) if personas else 0.5
    if completed_count > churned_count:
        wtp_level = "High" if avg_price_sensitivity < 0.5 else "Medium"
    else:
        wtp_level = "Low"
        
    wtp_summary = f"{wtp_level} - Based on {completed_count} user sessions completing goals out of {total_agents} total users. Price sensitivity averaged {avg_price_sensitivity:.2f}."

    # Build local markdown report summary
    local_summary = f"""# PopuSim UX Intelligence Report: {url}

## Executive Summary
Our autonomous user swarm simulated **{total_agents} sessions** navigating your product to discover conversion friction, UI bugs, and product-market fit signals.

* **Net Promoter Score (NPS):** `{computed_nps}`
* **Goal Completion (Conversion):** `{completed_count} / {total_agents} ({100 - computed_churn:.1f}%)`
* **Abandonment Rate (Churn):** `{computed_churn:.1f}%`
* **Willingness-to-pay (WTP) Signals:** `{wtp_level}`

---

## Funnel & Behavior Logs Analysis

### Archetype Performance Grid

"""
    for log in logs_summary:
        outcome_emoji = "✅ Completed" if log["status"] == "completed" else "❌ Churned"
        local_summary += f"""* **{log['persona_name']}** ({log['archetype']}): {outcome_emoji}
  * *Goals:* {", ".join(log['goals'])}
  * *Impatience:* `{log['traits']['impatience']}`, *Tech comfort:* `{log['traits']['tech_savviness']}`
  * *Bugs encountered:* {log['bugs_encountered']}
  * *Abandonment details:* {"Completed flow successfully." if log['status'] == 'completed' else "Felt confused or hit friction and left."}
"""

    local_summary += """
---

## QA Bug Log
We detected the following issues through natural page navigation:
"""
    if not unique_bugs:
        local_summary += "\n*No fatal bugs or console errors detected during natural navigation. Your page code appears stable.*\n"
    else:
        for idx, b in enumerate(unique_bugs):
            local_summary += f"""
### {idx+1}. [{b['severity']}] {b['description']}
* **Page URL:** `{b['url']}`
* **CSS Selector:** `{b.get('selector', 'N/A')}`
"""

    local_summary += """
---

## Actionable Recommendations
1. **Reduce form input fields:** Confused Novice and Impatient Scanner archetypes dropped off during forms. Streamline registration to single-click auth if possible.
2. **Optimize Load Times:** Fast load times keep high-impatience scanners engaged. Double check chunk sizes.
3. **Stabilize DOM clickables:** Ensure selectors correspond to button coordinates. Check error logs for failed interactions.
"""

    # If Gemini Key is present, leverage Gemini to synthesize a far more intelligent report
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            prompt = f"""
            You are a Senior Product Architect and UX Research Lead. Below are the execution logs of an autonomous user agent swarm navigating a target product URL:
            Target URL: {url}
            
            Swarm Behavior Summary:
            {json.dumps(logs_summary, indent=2)}

            Bugs Caught:
            {json.dumps(unique_bugs, indent=2)}

            Perform a deep synthesis of this behavioral and QA data to produce a comprehensive report.
            Your output must calculate:
            1. NPS score (rating based on satisfaction levels, from -100 to 100).
            2. Churn Analysis: For each persona, outline if they completed their goals or abandoned, and pinpoint the exact friction point where they dropped off. Calculate the overall Churn Rate percentage.
            3. Willingness-to-pay (WTP) signals: Output rating: "Low", "Medium", or "High" and a short explanation based on price sensitivity.
            4. De-duplicated bug report: Prioritized by severity (Critical, Major, Minor), detailing what is broken and where (selectors/URL).
            5. Comprehensive Markdown Executive Summary: Highlight conversion improvements and actionable product recommendations.

            Return ONLY a JSON object:
            {{
              "nps": {computed_nps},
              "churn_rate": {computed_churn},
              "wtp": "Medium - price-sensitive user felt value was clear...",
              "bugs": [
                 {{
                   "severity": "Major",
                   "description": "...",
                   "selector": "...",
                   "url": "..."
                 }}
              ],
              "summary": "### Executive Summary\\n..."
            }}
            """
            
            async with client.aio as aclient:
                response = await aclient.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )
            
            text_content = response.text
            if "```json" in text_content:
                text_content = text_content.split("```json")[1].split("```")[0].strip()
            elif "```" in text_content:
                text_content = text_content.split("```")[1].split("```")[0].strip()
                
            report_json = json.loads(text_content.strip())
            return {
                "nps": report_json.get("nps", computed_nps),
                "churn_rate": report_json.get("churn_rate", computed_churn),
                "wtp": report_json.get("wtp", wtp_summary),
                "bugs": report_json.get("bugs", unique_bugs),
                "summary": report_json.get("summary", local_summary)
            }
        except Exception as e:
            logger.error(f"Gemini report synthesis failed: {e}. Falling back to rule-based synthesis.")
            
    return {
        "nps": computed_nps,
        "churn_rate": computed_churn,
        "wtp": wtp_summary,
        "bugs": unique_bugs,
        "summary": local_summary
    }
