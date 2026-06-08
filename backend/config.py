import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get workspace directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "PopuSim"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/popusim.db"
    
    # Google Gemini Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Screenshots
    SCREENSHOTS_DIR: Path = BASE_DIR / "screenshots"
    
    # Sessions
    SESSIONS_DIR: Path = BASE_DIR / "sessions"
    
    # Simulation settings
    MAX_STEPS_PER_AGENT: int = 12
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure screenshots and sessions folders exist
settings.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
settings.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
