from typing import Optional, Dict, Any
from app.database.connection import get_db_connection

class CustomerRepository:
    """
    Repository class handling SQLite queries for Customer profiles.
    """
    def get_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            row = conn.execute("SELECT id, name, email FROM customers WHERE id = ?;", (customer_id,)).fetchone()
            return dict(row) if row else None
