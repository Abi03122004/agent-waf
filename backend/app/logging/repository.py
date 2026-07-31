from contextlib import contextmanager
import sqlite3
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AuditLogEntry(BaseModel):
    timestamp: str = Field(description="ISO timestamp of log entry")
    request_id: str = Field(description="Unique request UUID")
    session_id: str = Field(description="Session identifier")
    agent_id: str = Field(description="Agent identifier")
    tool: Optional[str] = Field(default=None, description="Invoked tool name")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameter key-value pairs")
    allowed: bool = Field(description="Whether the request was allowed")
    blocked: bool = Field(description="Whether the request was blocked")
    would_block: bool = Field(default=False, description="True if shadow mode would have blocked this request")
    rule_triggered: Optional[str] = Field(default=None, description="Name of the rule triggered, if any")
    reason: Optional[str] = Field(default=None, description="Interception block reason message")
    execution_time_ms: float = Field(description="Time taken to execute request in milliseconds")
    user_prompt: Optional[str] = Field(default=None, description="Raw user prompt query")
    rule_result: Optional[str] = Field(default=None, description="Result summary of deterministic rule engine")
    ai_risk_score: Optional[str] = Field(default=None, description="Risk level determined by AI WAF")
    ai_reason: Optional[str] = Field(default=None, description="Detailed explanation from AI classifier")
    final_decision: Optional[str] = Field(default=None, description="Final WAF disposition")

class AuditRepository(ABC):
    @abstractmethod
    def save(self, entry: AuditLogEntry) -> None:
        """Save a new audit log entry."""
        pass

    @abstractmethod
    def get_all(self, limit: int = 100) -> List[AuditLogEntry]:
        """Fetch latest audit log entries up to limit."""
        pass

    @abstractmethod
    def clear_all(self) -> None:
        """Clear all audit logs."""
        pass

class SQLiteAuditRepository(AuditRepository):
    def __init__(self, db_path: str) -> None:
        import os
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def clear_all(self) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM audit_logs;")
            try:
                conn.execute("DELETE FROM sqlite_sequence WHERE name = 'audit_logs';")
            except Exception:
                pass
            conn.commit()

    @contextmanager
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            pass
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    tool TEXT,
                    parameters TEXT,
                    allowed INTEGER NOT NULL,
                    blocked INTEGER NOT NULL,
                    would_block INTEGER DEFAULT 0,
                    rule_triggered TEXT,
                    reason TEXT,
                    execution_time_ms REAL NOT NULL
                )
            """)
            
            # Dynamic migration: append new hybrid WAF columns if missing
            new_columns = [
                ("user_prompt", "TEXT"),
                ("rule_result", "TEXT"),
                ("ai_risk_score", "TEXT"),
                ("ai_reason", "TEXT"),
                ("final_decision", "TEXT")
            ]
            for col_name, col_type in new_columns:
                try:
                    conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} {col_type};")
                except sqlite3.OperationalError:
                    # Column already exists, safe to ignore
                    pass
            conn.commit()

    def save(self, entry: AuditLogEntry) -> None:
        try:
            params_str = json.dumps(entry.parameters)
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO audit_logs (
                        timestamp, request_id, session_id, agent_id, tool,
                        parameters, allowed, blocked, would_block, rule_triggered,
                        reason, execution_time_ms, user_prompt, rule_result,
                        ai_risk_score, ai_reason, final_decision
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.timestamp,
                        entry.request_id,
                        entry.session_id,
                        entry.agent_id,
                        entry.tool,
                        params_str,
                        1 if entry.allowed else 0,
                        1 if entry.blocked else 0,
                        1 if entry.would_block else 0,
                        entry.rule_triggered,
                        entry.reason,
                        entry.execution_time_ms,
                        entry.user_prompt,
                        entry.rule_result,
                        entry.ai_risk_score,
                        entry.ai_reason,
                        entry.final_decision
                    )
                )
                conn.commit()
        except Exception as e:
            import logging
            logging.getLogger("agent_waf").error("Failed to save audit log entry: %s", str(e))

    def get_all(self, limit: int = 100) -> List[AuditLogEntry]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            entries = []
            for row in rows:
                try:
                    params_dict = json.loads(row["parameters"])
                except Exception:
                    params_dict = {}
                
                # Fetch row fields safely, falling back to None if not present (helps during migration transition)
                user_prompt = None
                rule_result = None
                ai_risk = None
                ai_reason = None
                final_decision = None
                
                try: user_prompt = row["user_prompt"]
                except Exception: pass
                
                try: rule_result = row["rule_result"]
                except Exception: pass
                
                try: ai_risk = row["ai_risk_score"]
                except Exception: pass
                
                try: ai_reason = row["ai_reason"]
                except Exception: pass
                
                try: final_decision = row["final_decision"]
                except Exception: pass

                entries.append(
                    AuditLogEntry(
                        timestamp=row["timestamp"],
                        request_id=row["request_id"],
                        session_id=row["session_id"],
                        agent_id=row["agent_id"],
                        tool=row["tool"],
                        parameters=params_dict,
                        allowed=bool(row["allowed"]),
                        blocked=bool(row["blocked"]),
                        would_block=bool(row["would_block"]),
                        rule_triggered=row["rule_triggered"],
                        reason=row["reason"],
                        execution_time_ms=row["execution_time_ms"],
                        user_prompt=user_prompt,
                        rule_result=rule_result,
                        ai_risk_score=ai_risk,
                        ai_reason=ai_reason,
                        final_decision=final_decision
                    )
                )
            return entries
