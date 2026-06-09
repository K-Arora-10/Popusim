from fastapi import APIRouter, HTTPException
import logging
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright
from backend.config import settings

logger = logging.getLogger("popusim.routes.session")
router = APIRouter()

# Global dictionary to track active browser instance for bootstrapping
# It holds: {"playwright": p, "browser": browser, "context": context, "page": page}
active_session = {}

class BootstrapStartRequest(BaseModel):
    url: str = Field(..., description="Target website login page URL to navigate to")

@router.post("/session/bootstrap/start")
async def start_bootstrap(request: BootstrapStartRequest):
    global active_session
    
    # If there is already an active session, close it first
    if active_session:
        try:
            await cleanup_active_session()
        except Exception as e:
            logger.error(f"Error cleaning up existing session: {e}")
            
    try:
        url = request.url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            
        p = await async_playwright().start()
        # Launch non-headless browser so user can interact with it
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Navigate to target login page
        await page.goto(url, wait_until="load", timeout=30000)
        
        # Save references
        active_session["playwright"] = p
        active_session["browser"] = browser
        active_session["context"] = context
        active_session["page"] = page
        
        return {"status": "started", "message": "Browser opened. Please log in manually."}
    except Exception as e:
        logger.error(f"Failed to start bootstrap browser: {e}")
        # Make sure to clean up if it failed halfway
        await cleanup_active_session()
        raise HTTPException(status_code=500, detail=f"Failed to launch browser: {str(e)}")

@router.post("/session/bootstrap/save")
async def save_bootstrap():
    global active_session
    if not active_session:
        raise HTTPException(status_code=400, detail="No active browser session to save.")
        
    try:
        context = active_session["context"]
        session_file = settings.SESSIONS_DIR / "shared.json"
        
        # Save storage state
        await context.storage_state(path=str(session_file))
        logger.info(f"Saved shared session state to {session_file}")
        
        # Clean up
        await cleanup_active_session()
        return {"status": "saved", "message": "Session saved successfully."}
    except Exception as e:
        logger.error(f"Failed to save bootstrap session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save session state: {str(e)}")

@router.post("/session/bootstrap/cancel")
async def cancel_bootstrap():
    global active_session
    if not active_session:
        return {"status": "no_active_session"}
        
    await cleanup_active_session()
    return {"status": "cancelled", "message": "Browser session closed without saving."}

@router.get("/session/bootstrap/status")
async def get_bootstrap_status():
    session_file = settings.SESSIONS_DIR / "shared.json"
    return {
        "active": len(active_session) > 0,
        "has_saved_session": session_file.exists()
    }

async def cleanup_active_session():
    global active_session
    if not active_session:
        return
        
    try:
        if "browser" in active_session:
            await active_session["browser"].close()
        if "playwright" in active_session:
            await active_session["playwright"].stop()
    except Exception as e:
        logger.error(f"Error during bootstrap browser cleanup: {e}")
    finally:
        active_session.clear()
