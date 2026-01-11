"""
Chat session management.

Manages conversation history, persistence, and context capture
for UCP learning.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ucp_chat.providers import Message


class ChatSession(BaseModel):
    """A chat session with history and metadata."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Chat"
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # UCP-specific metadata
    ucp_enabled: bool = False
    tool_predictions: list[dict] = Field(default_factory=list)
    tool_usages: list[dict] = Field(default_factory=list)
    context_snapshots: list[dict] = Field(default_factory=list)
    
    # Statistics
    total_tokens: int = 0
    total_cost: float = 0.0
    
    def add_message(
        self,
        role: str,
        content: str,
        **kwargs: Any,
    ) -> Message:
        """Add a message to the session."""
        msg = Message(role=role, content=content, **kwargs)
        self.messages.append(msg)
        self.updated_at = datetime.utcnow()
        return msg
    
    def record_tool_prediction(
        self,
        query: str,
        predicted_tools: list[str],
        scores: dict[str, float],
    ) -> None:
        """Record a UCP tool prediction (for training data)."""
        self.tool_predictions.append({
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "predicted_tools": predicted_tools,
            "scores": scores,
        })
    
    def record_tool_usage(
        self,
        tool_name: str,
        success: bool,
        latency_ms: float,
    ) -> None:
        """Record actual tool usage (for feedback)."""
        self.tool_usages.append({
            "timestamp": datetime.utcnow().isoformat(),
            "tool_name": tool_name,
            "success": success,
            "latency_ms": latency_ms,
        })
    
    def capture_context_snapshot(self) -> None:
        """Capture current conversation context for UCP learning."""
        self.context_snapshots.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message_count": len(self.messages),
            "active_tools": [u["tool_name"] for u in self.tool_usages[-5:]],
            "last_messages": [
                {"role": m.role, "content": m.content[:500]}
                for m in self.messages[-5:]
            ],
        })
    
    def get_context_for_ucp(self, n_messages: int = 5) -> str:
        """Get formatted context for UCP router."""
        recent = self.messages[-n_messages:]
        parts = []
        for msg in recent:
            if msg.role in ("user", "assistant"):
                parts.append(f"{msg.role}: {msg.content}")
        return "\n".join(parts)
    
    def to_training_format(self) -> dict:
        """Export session data in format suitable for RAFT training."""
        return {
            "session_id": self.id,
            "provider": self.provider,
            "model": self.model,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "tool_calls": m.tool_calls,
                }
                for m in self.messages
            ],
            "tool_predictions": self.tool_predictions,
            "tool_usages": self.tool_usages,
            "context_snapshots": self.context_snapshots,
        }


class SessionManager:
    """Manages saving/loading chat sessions."""
    
    DEFAULT_PATH = Path.home() / ".ucp" / "sessions"
    
    def __init__(self, sessions_dir: Path | None = None):
        self.sessions_dir = sessions_dir or self.DEFAULT_PATH
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._active_session: ChatSession | None = None
    
    @property
    def active_session(self) -> ChatSession:
        """Get or create the active session."""
        if self._active_session is None:
            self._active_session = ChatSession()
        return self._active_session
    
    @active_session.setter
    def active_session(self, session: ChatSession) -> None:
        self._active_session = session
    
    def _session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"
    
    def save(self, session: ChatSession | None = None) -> None:
        """Save a session to disk."""
        session = session or self._active_session
        if session is None:
            return
        
        path = self._session_path(session.id)
        with open(path, "w") as f:
            json.dump(session.model_dump(mode="json"), f, indent=2, default=str)
    
    def load(self, session_id: str) -> ChatSession:
        """Load a session from disk."""
        path = self._session_path(session_id)
        if not path.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")
        
        with open(path, "r") as f:
            data = json.load(f)
        
        # Convert message dicts back to Message objects
        if "messages" in data:
            data["messages"] = [Message(**m) for m in data["messages"]]
        
        return ChatSession(**data)
    
    def list_sessions(self, limit: int = 50) -> list[dict]:
        """List recent sessions with metadata."""
        sessions = []
        for path in sorted(self.sessions_dir.glob("*.json"), reverse=True)[:limit]:
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                sessions.append({
                    "id": data.get("id"),
                    "name": data.get("name", "Untitled"),
                    "provider": data.get("provider"),
                    "model": data.get("model"),
                    "message_count": len(data.get("messages", [])),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                })
            except Exception:
                continue
        return sessions
    
    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        path = self._session_path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def export_training_data(self, output_path: Path | None = None) -> Path:
        """Export all sessions as training data for UCP."""
        output_path = output_path or self.sessions_dir.parent / "training_data.jsonl"
        
        with open(output_path, "w") as f:
            for path in self.sessions_dir.glob("*.json"):
                try:
                    session = self.load(path.stem)
                    training_data = session.to_training_format()
                    f.write(json.dumps(training_data) + "\n")
                except Exception:
                    continue
        
        return output_path


# Global session manager
_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """Get the global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
