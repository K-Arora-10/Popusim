import sys
import asyncio

if sys.platform == "win32":
    # Set the event loop policy to ProactorEventLoop on Windows to support subprocesses (Playwright)
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
from contextlib import asynccontextmanager

from backend.config import settings
from backend.db import init_db
from backend.routes import simulation, report, ws, session

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("popusim")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing SQLite database tables...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    # Shutdown actions
    logger.info("Shutting down PopuSim Application Server.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    version="1.0.0"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow React dev server or production hosting
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve agent session screenshots statically
app.mount("/screenshots", StaticFiles(directory=str(settings.SCREENSHOTS_DIR)), name="screenshots")

# Wire Routers
app.include_router(simulation.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(session.router, prefix="/api")
app.include_router(ws.router)

@app.get("/")
async def root():
    return {"name": "PopuSim API Server", "status": "running"}

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
