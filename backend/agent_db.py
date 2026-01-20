"""
Agent Database - SQLite persistence for XAGENT registry
Stores agent URLs, upload status, and active state
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "agents.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema"""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            agent_id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            drive_url TEXT,
            google_email TEXT,
            created_at TIMESTAMP,
            last_active TIMESTAMP,
            files_uploaded BOOLEAN DEFAULT 0,
            active BOOLEAN DEFAULT 0
        )
    """)
    # Add google_email column if not exists (migration for existing DBs)
    try:
        conn.execute("ALTER TABLE agents ADD COLUMN google_email TEXT")
    except:
        pass  # Column already exists
    conn.commit()
    conn.close()

def get_agent(agent_id: str) -> dict | None:
    """Get agent by ID"""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM agents WHERE agent_id = ?", (agent_id,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def save_agent(agent_id: str, name: str = "", description: str = "", 
               drive_url: str = None, files_uploaded: bool = False,
               google_email: str = None):
    """Save or update agent"""
    conn = get_connection()
    existing = get_agent(agent_id)
    now = datetime.now().isoformat()
    
    if existing:
        # Update existing
        conn.execute("""
            UPDATE agents SET 
                drive_url = COALESCE(?, drive_url),
                files_uploaded = ?,
                last_active = ?,
                google_email = COALESCE(?, google_email),
                active = 1
            WHERE agent_id = ?
        """, (drive_url, files_uploaded, now, google_email, agent_id))
    else:
        # Insert new
        conn.execute("""
            INSERT INTO agents (agent_id, name, description, drive_url, 
                              google_email, created_at, last_active, files_uploaded, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (agent_id, name, description, drive_url, google_email, now, now, files_uploaded))
    
    conn.commit()
    conn.close()

def set_active(agent_id: str, active: bool):
    """Set agent active status"""
    conn = get_connection()
    now = datetime.now().isoformat()
    conn.execute("""
        UPDATE agents SET active = ?, last_active = ? WHERE agent_id = ?
    """, (active, now, agent_id))
    conn.commit()
    conn.close()

def update_drive_url(agent_id: str, drive_url: str):
    """Update the drive URL after agent creation"""
    conn = get_connection()
    conn.execute("""
        UPDATE agents SET drive_url = ?, files_uploaded = 1 WHERE agent_id = ?
    """, (drive_url, agent_id))
    conn.commit()
    conn.close()

def list_active() -> list[dict]:
    """Get all active agents"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM agents WHERE active = 1"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def list_all() -> list[dict]:
    """Get all agents (active and inactive)"""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM agents").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def deactivate_all():
    """Mark all agents as inactive (on startup)"""
    conn = get_connection()
    conn.execute("UPDATE agents SET active = 0")
    conn.commit()
    conn.close()

# Initialize on import
init_db()
