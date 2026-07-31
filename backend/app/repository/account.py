from typing import Optional, Dict, Any
from app.database.connection import get_db_connection

class AccountRepository:
    """
    Repository class handling SQLite queries and updates for Account records.
    """
    def get_by_customer_id(self, customer_id: int, account_type: str) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT id, customer_id, account_number, account_type, balance FROM accounts WHERE customer_id = ? AND account_type = ? COLLATE NOCASE;",
                (customer_id, account_type)
            ).fetchone()
            return dict(row) if row else None

    def get_by_account_number(self, account_number: str) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT id, customer_id, account_number, account_type, balance FROM accounts WHERE account_number = ?;",
                (account_number,)
            ).fetchone()
            return dict(row) if row else None

    def update_balance(self, account_id: int, new_balance: float) -> None:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE accounts SET balance = ? WHERE id = ?;",
                (new_balance, account_id)
            )
            conn.commit()
