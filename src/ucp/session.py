"""
Session Manager - State Persistence for UCP.

Implements the MemGPT-style "Operating System" metaphor:
- Context Window = RAM (active tools, recent messages)
- Database = Disk (full history, all tools)

Uses LangGraph-compatible state management with checkpointing.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import structlog

from ucp.config import SessionConfig
from ucp.models import Message, SessionState

logger = structlog.get_logger(__name__)


class SessionManager:
    """
    Manages session state with persistence.

    Sessions track:
    - Conversation history
    - Active toolset
    - Tool usage statistics
    - User context/preferences
    """

    def __init__(self, config: SessionConfig) -> None:
        self.config = config
        self._sessions: dict[UUID, SessionState] = {}
        self._db: sqlite3.Connection | None = None

        if config.persistence == "sqlite":
            self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Initialize SQLite database for persistence."""
        db_path = Path(self.config.sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row

        # Create tables
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                state_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                tool_call_id TEXT,
                tool_name TEXT,
                metadata_json TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session
            ON messages(session_id, timestamp);

            CREATE TABLE IF NOT EXISTS tool_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                success INTEGER NOT NULL,
                execution_time_ms REAL,
                error TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );

            CREATE INDEX IF NOT EXISTS idx_tool_usage_session
            ON tool_usage_log(session_id, timestamp);
        """)
        self._db.commit()

        logger.info("session_db_initialized", path=str(db_path))

    def create_session(self) -> SessionState:
        """Create a new session."""
        session = SessionState()
        self._sessions[session.session_id] = session

        if self._db:
            self._persist_session(session)

        logger.info("session_created", session_id=str(session.session_id))
        return session

    def get_session(self, session_id: UUID | str) -> SessionState | None:
        """Get an existing session by ID."""
        if isinstance(session_id, str):
            session_id = UUID(session_id)

        # Check memory cache first
        if session_id in self._sessions:
            return self._sessions[session_id]

        # Try loading from database
        if self._db:
            session = self._load_session(session_id)
            if session:
                self._sessions[session_id] = session
                return session

        return None

    def get_or_create_session(self, session_id: UUID | str | None = None) -> SessionState:
        """Get existing session or create new one."""
        if session_id:
            existing = self.get_session(session_id)
            if existing:
                return existing

        return self.create_session()

    def save_session(self, session: SessionState) -> None:
        """Save session state to persistence."""
        session.updated_at = datetime.utcnow()
        self._sessions[session.session_id] = session

        if self._db:
            self._persist_session(session)

    def _persist_session(self, session: SessionState) -> None:
        """Write session to SQLite."""
        if not self._db:
            return

        state_dict = session.model_dump(mode="json")
        # Remove messages from state (stored separately)
        state_dict.pop("messages", None)

        self._db.execute(
            """
            INSERT OR REPLACE INTO sessions (session_id, created_at, updated_at, state_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(session.session_id),
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
                json.dumps(state_dict),
            ),
        )

        # Persist messages
        for msg in session.messages:
            self._db.execute(
                """
                INSERT OR REPLACE INTO messages
                (id, session_id, role, content, timestamp, tool_call_id, tool_name, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(msg.id),
                    str(session.session_id),
                    msg.role,
                    msg.content,
                    msg.timestamp.isoformat(),
                    msg.tool_call_id,
                    msg.tool_name,
                    json.dumps(msg.metadata),
                ),
            )

        self._db.commit()

    def _load_session(self, session_id: UUID) -> SessionState | None:
        """Load session from SQLite."""
        if not self._db:
            return None

        row = self._db.execute(
            "SELECT * FROM sessions WHERE session_id = ?",
            (str(session_id),),
        ).fetchone()

        if not row:
            return None

        state_dict = json.loads(row["state_json"])
        state_dict["session_id"] = session_id
        state_dict["created_at"] = datetime.fromisoformat(row["created_at"])
        state_dict["updated_at"] = datetime.fromisoformat(row["updated_at"])

        # Load messages
        msg_rows = self._db.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp",
            (str(session_id),),
        ).fetchall()

        messages = []
        for msg_row in msg_rows:
            messages.append(Message(
                id=UUID(msg_row["id"]),
                role=msg_row["role"],
                content=msg_row["content"],
                timestamp=datetime.fromisoformat(msg_row["timestamp"]),
                tool_call_id=msg_row["tool_call_id"],
                tool_name=msg_row["tool_name"],
                metadata=json.loads(msg_row["metadata_json"]) if msg_row["metadata_json"] else {},
            ))

        state_dict["messages"] = messages
        return SessionState(**state_dict)

    def log_tool_usage(
        self,
        session_id: UUID,
        tool_name: str,
        success: bool,
        execution_time_ms: float = 0,
        error: str | None = None,
    ) -> None:
        """Log a tool usage event."""
        if not self._db:
            return

        self._db.execute(
            """
            INSERT INTO tool_usage_log
            (session_id, tool_name, timestamp, success, execution_time_ms, error)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(session_id),
                tool_name,
                datetime.utcnow().isoformat(),
                1 if success else 0,
                execution_time_ms,
                error,
            ),
        )
        self._db.commit()

    def get_tool_usage_stats(self, session_id: UUID | None = None) -> dict[str, Any]:
        """Get tool usage statistics."""
        if not self._db:
            return {}

        if session_id:
            rows = self._db.execute(
                """
                SELECT tool_name, COUNT(*) as uses, SUM(success) as successes,
                       AVG(execution_time_ms) as avg_time
                FROM tool_usage_log WHERE session_id = ?
                GROUP BY tool_name
                """,
                (str(session_id),),
            ).fetchall()
        else:
            rows = self._db.execute(
                """
                SELECT tool_name, COUNT(*) as uses, SUM(success) as successes,
                       AVG(execution_time_ms) as avg_time
                FROM tool_usage_log
                GROUP BY tool_name
                """
            ).fetchall()

        return {
            row["tool_name"]: {
                "uses": row["uses"],
                "success_rate": row["successes"] / row["uses"] if row["uses"] else 0,
                "avg_time_ms": row["avg_time"],
            }
            for row in rows
        }

    def cleanup_old_sessions(self, max_age_hours: int | None = None) -> int:
        """Delete sessions older than the TTL."""
        if not self._db:
            return 0

        max_age = max_age_hours or (self.config.ttl_seconds // 3600)
        cutoff = datetime.utcnow() - timedelta(hours=max_age)

        # Get sessions to delete
        old_sessions = self._db.execute(
            "SELECT session_id FROM sessions WHERE updated_at < ?",
            (cutoff.isoformat(),),
        ).fetchall()

        session_ids = [row["session_id"] for row in old_sessions]

        if session_ids:
            placeholders = ",".join("?" * len(session_ids))

            self._db.execute(
                f"DELETE FROM messages WHERE session_id IN ({placeholders})",
                session_ids,
            )
            self._db.execute(
                f"DELETE FROM tool_usage_log WHERE session_id IN ({placeholders})",
                session_ids,
            )
            self._db.execute(
                f"DELETE FROM sessions WHERE session_id IN ({placeholders})",
                session_ids,
            )
            self._db.commit()

            # Remove from memory cache
            for sid in session_ids:
                self._sessions.pop(UUID(sid), None)

        logger.info("sessions_cleaned", count=len(session_ids))
        return len(session_ids)

    def archive_messages(self, session: SessionState, keep_recent: int = 20) -> str:
        """
        Archive old messages to reduce context size.

        Returns a summary of archived messages.
        """
        if len(session.messages) <= keep_recent:
            return ""

        # Messages to archive
        to_archive = session.messages[:-keep_recent]
        session.messages = session.messages[-keep_recent:]

        # Generate summary (simple version - could use LLM)
        summary_parts = []
        tool_calls = [m for m in to_archive if m.tool_name]
        user_msgs = [m for m in to_archive if m.role == "user"]

        if tool_calls:
            tools_used = set(m.tool_name for m in tool_calls)
            summary_parts.append(f"Tools used: {', '.join(tools_used)}")

        if user_msgs:
            summary_parts.append(f"User topics: {len(user_msgs)} messages archived")

        summary = " | ".join(summary_parts) if summary_parts else "Previous context archived"

        # Add summary as system message
        session.add_message("system", f"[Archived context] {summary}")

        self.save_session(session)
        logger.info(
            "messages_archived",
            session_id=str(session.session_id),
            archived_count=len(to_archive),
        )

        return summary

    def close(self) -> None:
        """Close database connection."""
        if self._db:
            self._db.close()
            self._db = None
