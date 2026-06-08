import aiosqlite
import json
from datetime import datetime
from backend.config import settings

async def get_db():
    # SQLite connection string, stripping out any sqlite+aiosqlite prefix
    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    return conn

async def init_db():
    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    async with aiosqlite.connect(db_path) as conn:
        # 1. Simulations Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS simulations (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                nps INTEGER,
                churn_rate REAL,
                wtp TEXT,
                use_shared_session INTEGER DEFAULT 0
            )
        """)
        
        # Try to add use_shared_session column for backward compatibility with existing databases
        try:
            await conn.execute("ALTER TABLE simulations ADD COLUMN use_shared_session INTEGER DEFAULT 0")
            await conn.commit()
        except Exception:
            # Column already exists or table doesn't exist yet
            pass
        
        # 2. Personas Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS personas (
                id TEXT PRIMARY KEY,
                simulation_id TEXT NOT NULL,
                name TEXT NOT NULL,
                archetype TEXT NOT NULL,
                goals TEXT NOT NULL,
                impatience REAL NOT NULL,
                tech_savviness REAL NOT NULL,
                price_sensitivity REAL NOT NULL,
                support_reliance REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (simulation_id) REFERENCES simulations (id) ON DELETE CASCADE
            )
        """)
        
        # 3. Agent Logs Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulation_id TEXT NOT NULL,
                persona_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                step_number INTEGER NOT NULL,
                action TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT NOT NULL,
                screenshot_filename TEXT,
                reason TEXT,
                FOREIGN KEY (simulation_id) REFERENCES simulations (id) ON DELETE CASCADE,
                FOREIGN KEY (persona_id) REFERENCES personas (id) ON DELETE CASCADE
            )
        """)
        
        # 4. Reports Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                simulation_id TEXT NOT NULL,
                nps INTEGER NOT NULL,
                churn_rate REAL NOT NULL,
                wtp TEXT NOT NULL,
                bugs TEXT NOT NULL,  -- JSON string
                summary TEXT NOT NULL, -- Markdown summary
                created_at DATETIME NOT NULL,
                FOREIGN KEY (simulation_id) REFERENCES simulations (id) ON DELETE CASCADE
            )
        """)

        # 5. Chat Messages Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                FOREIGN KEY (simulation_id) REFERENCES simulations (id) ON DELETE CASCADE
            )
        """)
        
        await conn.commit()
