import sqlite3
from app.core.config import settings

def get_db_connection() -> sqlite3.Connection:
    """
    Returns a connection to the application SQLite database with row_factory enabled
    and performance-optimized journal settings.
    """
    conn = sqlite3.connect(settings.DATABASE_PATH, timeout=30.0, check_same_thread=False)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass
    conn.row_factory = sqlite3.Row
    return conn
