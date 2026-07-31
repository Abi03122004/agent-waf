import logging
from app.database.connection import get_db_connection

logger = logging.getLogger("agent_waf")

def init_banking_schema() -> None:
    """
    Initializes the banking tables (customers, accounts, transactions)
    and seeds them with initial dummy data if they are empty.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                account_number TEXT UNIQUE NOT NULL,
                account_type TEXT NOT NULL,
                balance REAL NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            );
        """)
        
        conn.commit()

        # 2. Seed data if empty
        cursor.execute("SELECT COUNT(*) FROM customers;")
        if cursor.fetchone()[0] == 0:
            logger.info("Seeding customers data...")
            cursor.executemany("""
                INSERT INTO customers (id, name, email) VALUES (?, ?, ?);
            """, [
                (1, "John Doe", "john.doe@email.com"),
                (2, "Ravi", "ravi.sharma@email.com")
            ])
            conn.commit()

        cursor.execute("SELECT COUNT(*) FROM accounts;")
        if cursor.fetchone()[0] == 0:
            logger.info("Seeding accounts data...")
            cursor.executemany("""
                INSERT INTO accounts (id, customer_id, account_number, account_type, balance)
                VALUES (?, ?, ?, ?, ?);
            """, [
                (1, 1, "12345", "Savings", 125450.00),
                (2, 1, "54321", "Current", 15000.00),
                (3, 2, "67890", "Savings", 10000.00)
            ])
            conn.commit()

        cursor.execute("SELECT COUNT(*) FROM transactions;")
        if cursor.fetchone()[0] == 0:
            logger.info("Seeding transaction history...")
            cursor.executemany("""
                INSERT INTO transactions (account_id, type, amount, description, timestamp)
                VALUES (?, ?, ?, ?, ?);
            """, [
                (1, "CREDIT", 1500.0, "Cash Deposit", "2026-07-24T12:00:00"),
                (1, "DEBIT", 5000.0, "Rent Payment", "2026-07-25T14:30:00"),
                (1, "DEBIT", 1200.0, "Supermarket", "2026-07-28T09:15:00"),
                (1, "CREDIT", 25000.0, "Salary Credited", "2026-07-29T08:00:00"),
                (1, "DEBIT", 500.0, "Electricity Bill", "2026-07-30T10:45:00")
            ])
            conn.commit()
            
    logger.info("Banking schema check and initialization completed successfully.")
