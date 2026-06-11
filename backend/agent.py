import asyncio
import base64
import json
import logging
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Callable
from playwright.async_api import Page, Browser, Error as PlaywrightError
from backend.config import settings

logger = logging.getLogger("popusim.agent")

# Javascript selector to find interactive elements in page
DOM_EXTRACTOR_JS = """
() => {
    const elements = [];
    
    // Helper to get CSS selector
    const getSelector = (el) => {
        if (el.id) return `#${el.id}`;
        let selector = el.tagName.toLowerCase();
        if (el.name) {
            selector += `[name="${el.name}"]`;
        } else if (el.getAttribute('href')) {
            selector += `[href="${el.getAttribute('href')}"]`;
        } else if (el.className) {
            const cleanClasses = Array.from(el.classList).filter(c => !c.includes(':')).join('.');
            if (cleanClasses) selector += `.${cleanClasses}`;
        }
        return selector;
    };

    // Find all potential interactive elements
    const candidates = document.querySelectorAll('a, button, input, select, textarea, [role="button"], [onclick]');
    let count = 0;
    
    for (const el of candidates) {
        if (count >= 30) break; // Limit elements for token management
        
        // Visibility check
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        if (rect.width === 0 || rect.height === 0 || style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
            continue;
        }
        
        elements.push({
            tag: el.tagName.toLowerCase(),
            text: (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().substring(0, 60),
            placeholder: el.getAttribute('placeholder') || '',
            selector: getSelector(el),
            type: el.getAttribute('type') || ''
        });
        count++;
    }
    return elements;
}
"""

class AutonomousAgent:
    def __init__(
        self,
        simulation_id: str,
        persona: Dict[str, Any],
        db_conn,
        log_callback: Callable[[Dict[str, Any]], Any],
        use_shared_session: bool = False
    ):
        self.simulation_id = simulation_id
        self.persona = persona
        self.persona_id = persona["id"]
        self.db_conn = db_conn
        self.log_callback = log_callback
        self.use_shared_session = use_shared_session
        
        self.step = 0
        self.status = "running"
        self.history = []
        self.bugs_detected = []
        self.screenshot_paths = []
        
        # State tracking for mock mode
        self.mock_visited_pages = ["/"]
        
    async def run(self, browser: Browser):
        logger.info(f"Starting agent: {self.persona['name']} ({self.persona['archetype']})")
        
        context_args = {
            "viewport": {"width": 1280, "height": 800},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        session_file = settings.SESSIONS_DIR / "shared.json"
        if self.use_shared_session and session_file.exists():
            context_args["storage_state"] = str(session_file)
            logger.info(f"Loaded shared login session state from {session_file}")
        else:
            logger.info(f"Clean login session state for {self.persona['name']}")
            
        context = await browser.new_context(**context_args)
        page = await context.new_page()
        
        # Set up page-level error listeners
        page.on("pageerror", self._handle_page_error)
        page.on("requestfailed", self._handle_request_failed)
        
        try:
            # Step 0: Initial Page Load
            await self._record_log(
                action="Navigate",
                url=self.persona["simulation_id"], # will navigate to target url
                description=f"Opening target site: {self.persona['name']} lands on homepage.",
                reason="Landed on website to start goals: " + ", ".join(self.persona["goals"])
            )
            
            # Target URL
            target_url = await self._get_target_url()
            await page.goto(target_url, wait_until="networkidle", timeout=20000)
            await page.wait_for_timeout(1000) # extra wait for transition animations
            
            # Start navigation loop
            while self.step < settings.MAX_STEPS_PER_AGENT and self.status == "running":
                self.step += 1
                await page.wait_for_timeout(1500) # pacing simulation
                
                # Take page screenshot
                screenshot_filename = f"{self.simulation_id}_{self.persona_id}_step_{self.step}.png"
                screenshot_path = settings.SCREENSHOTS_DIR / screenshot_filename
                try:
                    await page.screenshot(path=str(screenshot_path))
                    self.screenshot_paths.append(screenshot_filename)
                except Exception as screenshot_err:
                    logger.error(f"Failed to capture screenshot: {screenshot_err}")
                    screenshot_filename = None
                
                # Extract interactive elements
                elements = []
                try:
                    elements = await page.evaluate(DOM_EXTRACTOR_JS)
                except Exception as dom_err:
                    logger.error(f"DOM extraction failed: {dom_err}")
                    
                current_url = page.url
                
                # Make navigation decision
                decision = await self._decide_next_action(page, current_url, elements, screenshot_path)
                
                # Execute action
                action = decision.get("action", "").lower()
                selector = decision.get("selector", "")
                text_to_type = decision.get("text", "")
                reason = decision.get("reason", "")
                description = ""
                
                if action == "click" and selector:
                    try:
                        # Attempt to scroll element into view and click
                        await page.scroll_to_element(selector) if hasattr(page, 'scroll_to_element') else None
                        await page.click(selector, timeout=5000)
                        description = f"Clicked element: '{decision.get('element_text', selector)}'"
                    except PlaywrightError as e:
                        # Failed to click - mark as a UX bug
                        description = f"Failed to click element: '{selector}'"
                        self._add_bug(
                            severity="Major",
                            description=f"Click interaction failed on selector {selector}: {e}",
                            selector=selector,
                            url=current_url,
                            screenshot=screenshot_filename
                        )
                        # Back off and wait
                        action = "wait"
                        
                elif action == "type" and selector:
                    try:
                        await page.click(selector, timeout=5000)
                        await page.fill(selector, text_to_type)
                        description = f"Typed value in field: {selector}"
                    except PlaywrightError as e:
                        description = f"Failed to type in field: {selector}"
                        self._add_bug(
                            severity="Major",
                            description=f"Input type interaction failed on selector {selector}: {e}",
                            selector=selector,
                            url=current_url,
                            screenshot=screenshot_filename
                        )
                        action = "wait"
                        
                elif action == "wait":
                    await page.wait_for_timeout(3000)
                    description = "Waited for 3 seconds to let content load."
                    
                elif action == "back":
                    try:
                        await page.go_back()
                        description = "Navigated back to the previous page."
                    except Exception:
                        description = "Attempted to navigate back, but no history was available."
                        action = "wait"
                        
                elif action in ["complete", "convert", "finish"]:
                    self.status = "completed"
                    description = "Completed goals successfully and signed off."
                    
                elif action in ["churn", "abandon", "leave"]:
                    self.status = "churned"
                    description = f"Churned and abandoned the site. Reason: {reason}"
                    
                else:
                    # Fallback wait if LLM returned invalid action
                    await page.wait_for_timeout(2000)
                    description = "Undetermined action taken, waiting for state resolution."
                    action = "wait"
                
                # Check for high impatience trigger
                if self.persona["impatience"] > 0.8 and len(self.bugs_detected) > 0 and self.status == "running":
                    self.status = "churned"
                    reason = f"Impatient user encountered bugs/errors and churned immediately."
                    description = f"Churned. User has low tolerance (impatience {self.persona['impatience']}) and hit errors."
                    action = "churn"
                    
                # Save step log in DB and broadcast to front-end
                await self._record_log(
                    action=action.capitalize(),
                    url=current_url,
                    description=description,
                    reason=reason,
                    screenshot_filename=screenshot_filename
                )
                
            # Loop ended, force complete if still running
            if self.status == "running":
                self.status = "completed"
                await self._record_log(
                    action="Complete",
                    url=page.url,
                    description="Simulation ended naturally (max steps reached).",
                    reason="Completed browsing loop."
                )
                
        except Exception as sim_err:
            logger.error(f"Agent simulation crashed: {sim_err}")
            self.status = "failed"
            await self._record_log(
                action="Failed",
                url=page.url if 'page' in locals() else "",
                description=f"Simulation crashed due to script error: {sim_err}",
                reason="System crash error"
            )
        finally:
            await context.close()
            
        # Update final status of persona in DB
        await self._update_persona_status()
        logger.info(f"Agent finished: {self.persona['name']} with status {self.status}")

    async def _decide_next_action(self, page: Page, current_url: str, elements: List[Dict[str, Any]], screenshot_path: Path) -> Dict[str, Any]:
        """
        Decides the next action using Google Gemini (with screenshot) or deterministic mock mode.
        """
        if not settings.GEMINI_API_KEY:
            return self._decide_mock_action(current_url, elements)
            
        try:
            from google import genai
            from google.genai import types
            
            # Read screenshot bytes
            with open(screenshot_path, "rb") as image_file:
                image_bytes = image_file.read()
                
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            # Construct history log context
            history_context = "\n".join([
                f"Step {h['step']}: Action {h['action']} on URL {h['url']}. Result: {h['desc']}"
                for h in self.history[-5:]
            ])
            
            prompt = f"""
            You are simulating the mind of a real website user:
            NAME: {self.persona['name']}
            ARCHETYPE: {self.persona['archetype']}
            GOALS: {", ".join(self.persona['goals'])}
            TRAITS: Impatience={self.persona['impatience']}, Tech Savviness={self.persona['tech_savviness']}, Price Sensitivity={self.persona['price_sensitivity']}, Support Reliance={self.persona['support_reliance']}

            Currently you are at URL: {current_url}
            Here is your recent browsing history:
            {history_context}

            Here is a list of interactive elements found on the screen:
            {json.dumps(elements, indent=2)}

            Analyze the user attributes and goals, inspect the screenshot image provided, and decide what this user would do next.
            Confused users (low tech comfort) might click wrong links or seek help.
            Impatient users (high impatience) will churn (action: "churn") if they get stuck, see errors, or can't find what they need in 4-5 steps.
            Price sensitive users (high sensitivity) will navigate to pricing, search for details, compare.
            
            Return a JSON object:
            {{
              "action": "click" | "type" | "wait" | "back" | "complete" | "churn",
              "selector": "CSS selector to interact with",
              "text": "text to type if action is type, else empty",
              "element_text": "text of element selected",
              "reason": "short explanation of user reasoning"
            }}
            """
            
            async with client.aio as aclient:
                response = await aclient.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type="image/png"
                        ),
                        prompt
                    ]
                )
            
            text_content = response.text
            if "```json" in text_content:
                text_content = text_content.split("```json")[1].split("```")[0].strip()
            elif "```" in text_content:
                text_content = text_content.split("```")[1].split("```")[0].strip()
                
            return json.loads(text_content.strip())
            
        except Exception as e:
            logger.error(f"Gemini agent decision failed: {e}. Falling back to mock decision.")
            return self._decide_mock_action(current_url, elements)

    def _decide_mock_action(self, current_url: str, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Deterministic mock action planner based on persona goals and attributes.
        Implements realistic conversion funnel and churn mechanics.
        """
        # Goal checks
        goals = self.persona["goals"]
        tech = self.persona["tech_savviness"]
        impatience = self.persona["impatience"]
        price_sens = self.persona["price_sensitivity"]
        
        # Check if we should complete simulation
        if self.step >= 5:
            # Power users / patient users have a higher conversion rate
            success_threshold = 0.45 + (tech * 0.3) - (impatience * 0.2)
            import random
            if random.random() < success_threshold:
                return {
                    "action": "complete",
                    "selector": "",
                    "text": "",
                    "element_text": "",
                    "reason": "Achieved all tasks and felt satisfied with the flow."
                }
            else:
                return {
                    "action": "churn",
                    "selector": "",
                    "text": "",
                    "element_text": "",
                    "reason": "Got frustrated with the slow loading times and lack of clear labels."
                }
                
        # Impatient user churn check
        if self.step >= 3 and impatience > 0.8:
            return {
                "action": "churn",
                "selector": "",
                "text": "",
                "element_text": "",
                "reason": "Page took too long to load or steps were too confusing. Abandoning site."
            }

        # Analyze elements to find matches related to goals
        # Example goal keywords: price, signup, login, features, doc, help
        for el in elements:
            text = el.get("text", "").lower()
            tag = el.get("tag", "")
            
            # Form field fill logic
            if tag in ["input", "textarea"] and el.get("type") != "submit":
                placeholder = el.get("placeholder", "").lower()
                name = el.get("selector", "").lower()
                typed_value = "test@example.com"
                if "name" in placeholder or "name" in name:
                    typed_value = self.persona["name"]
                elif "pass" in placeholder or "pass" in name:
                    typed_value = "SecurePassword123!"
                elif "phone" in placeholder or "phone" in name:
                    typed_value = "+1-555-0199"
                elif "search" in placeholder or "search" in name:
                    typed_value = "pricing plans"
                    
                return {
                    "action": "type",
                    "selector": el["selector"],
                    "text": typed_value,
                    "element_text": el["text"],
                    "reason": f"Needs to fill out inputs to proceed with site registration."
                }
            
            # Click buttons/links matching archetype interests
            # 1. Price Sensitive -> click pricing
            if price_sens > 0.7 and ("price" in text or "pricing" in text or "plan" in text or "cost" in text):
                return {
                    "action": "click",
                    "selector": el["selector"],
                    "text": "",
                    "element_text": el["text"],
                    "reason": "Price sensitive buyer wants to compare plans and features."
                }
            
            # 2. General signup/register goals
            if any(g in text for g in ["sign up", "signup", "register", "create account", "get started", "join"]):
                return {
                    "action": "click",
                    "selector": el["selector"],
                    "text": "",
                    "element_text": el["text"],
                    "reason": "Ready to sign up and test the platform onboarding flow."
                }
                
            # 3. Help/FAQ goals
            if self.persona["support_reliance"] > 0.7 and any(g in text for g in ["help", "faq", "contact", "support", "docs"]):
                return {
                    "action": "click",
                    "selector": el["selector"],
                    "text": "",
                    "element_text": el["text"],
                    "reason": "Confused novice is looking for assistance or product support."
                }
                
            # 4. Features/Explore goals
            if any(g in text for g in ["feature", "product", "demo", "tour", "learn more"]):
                return {
                    "action": "click",
                    "selector": el["selector"],
                    "text": "",
                    "element_text": el["text"],
                    "reason": "Wants to explore what features are included."
                }

        # Fallback: Click first link/button we haven't visited or just click any interactive element
        import random
        valid_clickable = [el for el in elements if el.get("tag") in ["a", "button"] and el.get("selector")]
        if valid_clickable:
            target = random.choice(valid_clickable)
            return {
                "action": "click",
                "selector": target["selector"],
                "text": "",
                "element_text": target["text"],
                "reason": f"Exploring site structure by checking {target['text']} links."
            }
            
        return {
            "action": "wait",
            "selector": "",
            "text": "",
            "element_text": "",
            "reason": "No clear navigation elements visible. Waiting."
        }

    def _handle_page_error(self, err: PlaywrightError):
        """Captures page-level Javascript execution crashes."""
        logger.warning(f"Browser Page Error caught: {err}")
        self._add_bug(
            severity="Critical" if "referenceerror" in str(err).lower() or "syntaxerror" in str(err).lower() else "Major",
            description=f"Client-side Javascript runtime exception: {err}",
            url=self.history[-1]["url"] if self.history else self.persona["simulation_id"]
        )

    def _handle_request_failed(self, request):
        """Captures network-level HTTP resource failed requests."""
        # Filter static assets like images, css, favicon failures unless they are critical
        url = request.url
        failure = request.failure
        if failure:
            reason = failure.error_text if hasattr(failure, "error_text") else str(failure)
        else:
            reason = "Unknown Network Error"

        
        # Only log main resources or APIs as bugs
        if any(api_indicator in url for api_indicator in ["/api/", "/v1/", "/graphql"]) or request.resource_type in ["document", "xhr", "fetch"]:
            logger.warning(f"Network Request Failed: {url} | Reason: {reason}")
            self._add_bug(
                severity="Critical" if request.resource_type == "document" else "Major",
                description=f"API/Resource call failed to load: {url} ({reason})",
                url=self.history[-1]["url"] if self.history else self.persona["simulation_id"]
            )

    def _add_bug(self, severity: str, description: str, selector: str = None, url: str = None, screenshot: str = None):
        """Appends unique bugs to the agent session memory."""
        # De-duplicate identical bugs
        for b in self.bugs_detected:
            if b["description"] == description and b["url"] == url:
                return
        self.bugs_detected.append({
            "severity": severity,
            "description": description,
            "selector": selector,
            "url": url,
            "screenshot": screenshot
        })

    async def _record_log(
        self,
        action: str,
        url: str,
        description: str,
        reason: str = None,
        screenshot_filename: str = None
    ):
        """Saves step metadata to local history, database, and fires WebSocket broadcaster."""
        timestamp = datetime.now()
        
        # Keep track of history in RAM
        self.history.append({
            "step": self.step,
            "action": action,
            "url": url,
            "desc": description,
            "reason": reason,
            "timestamp": timestamp.isoformat()
        })
        
        # Write to SQLite
        try:
            await self.db_conn.execute(
                """
                INSERT INTO agent_logs (simulation_id, persona_id, timestamp, step_number, action, url, description, screenshot_filename, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.simulation_id,
                    self.persona_id,
                    timestamp.isoformat(),
                    self.step,
                    action,
                    url,
                    description,
                    screenshot_filename,
                    reason
                )
            )
            await self.db_conn.commit()
        except Exception as db_err:
            logger.error(f"Failed to save agent log to database: {db_err}")
            
        # Fire WebSocket callback
        if self.log_callback:
            event_payload = {
                "type": "agent_step",
                "simulation_id": self.simulation_id,
                "persona_id": self.persona_id,
                "persona_name": self.persona["name"],
                "persona_archetype": self.persona["archetype"],
                "step": self.step,
                "action": action,
                "url": url,
                "description": description,
                "reason": reason,
                "screenshot": screenshot_filename,
                "status": self.status,
                "bugs_count": len(self.bugs_detected)
            }
            # Execute callback asynchronously
            asyncio.create_task(self.log_callback(event_payload))

    async def _update_persona_status(self):
        """Updates the final simulation outcome of the user in the SQLite store."""
        try:
            await self.db_conn.execute(
                "UPDATE personas SET status = ? WHERE id = ?",
                (self.status, self.persona_id)
            )
            await self.db_conn.commit()
        except Exception as db_err:
            logger.error(f"Failed to update persona status: {db_err}")

    async def _get_target_url(self) -> str:
        """Helper to resolve website entry URL."""
        # Read from simulation db record
        async with self.db_conn.execute("SELECT url FROM simulations WHERE id = ?", (self.simulation_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "https://example.com"
