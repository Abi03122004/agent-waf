from typing import List, Dict, Any
from datetime import datetime
from app.database.connection import get_db_connection

class TransactionRepository:
    """
    Repository class handling SQLite queries and inserts for Transactions.
    """
    def get_history(self, account_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT id, account_id, type, amount, description, timestamp FROM transactions WHERE account_id = ? ORDER BY timestamp DESC LIMIT ?;",
                (account_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    def create_transaction(self, account_id: int, type: str, amount: float, description: str) -> None:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO transactions (account_id, type, amount, description, timestamp) VALUES (?, ?, ?, ?, ?);",
                (account_id, type, amount, description, datetime.utcnow().isoformat())
            )
            conn.commit()
