import sqlite3
import os
from app.core.config import settings

def get_db_connection() -> sqlite3.Connection:
    """
    Returns a connection to the application SQLite database with row_factory enabled
    and performance-optimized journal settings.
    """
    db_dir = os.path.dirname(settings.DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(settings.DATABASE_PATH, timeout=30.0, check_same_thread=False)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass
    conn.row_factory = sqlite3.Row
    return conn
