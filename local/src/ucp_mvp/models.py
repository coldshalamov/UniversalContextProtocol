"""
Core data models for UCP.

These models represent the internal state and data structures used throughout UCP.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ToolSchema(BaseModel):
    """
    Normalized representation of a tool schema.

    All tools from downstream servers are converted to this format
    for consistent indexing and retrieval.
    """

    name: str = Field(description="Fully qualified tool name (server.tool)")
    display_name: str = Field(description="Human-readable tool name")
    description: str = Field(description="Tool description for embedding")
    server_name: str = Field(description="Name of the owning MCP server")
    input_schema: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for inputs"
    )
    # Metadata for routing
    tags: list[str] = Field(default_factory=list)
    domain: str | None = Field(default=None, description="Domain category (e.g., 'email', 'code')")
    # Embedding vector (populated by Tool Zoo)
    embedding: list[float] | None = Field(default=None, exclude=True)

    @property
    def full_description(self) -> str:
        """Generate a rich description for embedding."""
        parts = [self.description]
        if self.tags:
            parts.append(f"Tags: {', '.join(self.tags)}")
        if self.domain:
            parts.append(f"Domain: {self.domain}")
        # Include parameter names for better semantic matching
        if self.input_schema.get("properties"):
            params = list(self.input_schema["properties"].keys())
            parts.append(f"Parameters: {', '.join(params)}")
        return " | ".join(parts)


class ServerStatus(str, Enum):
    """Status of a downstream MCP server connection."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class DownstreamServer(BaseModel):
    """Runtime state of a downstream MCP server."""

    name: str
    status: ServerStatus = ServerStatus.DISCONNECTED
    tools: list[ToolSchema] = Field(default_factory=list)
    last_connected: datetime | None = None
    error_message: str | None = None
    # Connection metadata
    transport_type: str = "stdio"
    endpoint: str | None = None


class Message(BaseModel):
    """A message in the conversation history."""

    id: UUID = Field(default_factory=uuid4)
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_call_id: str | None = None
    tool_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionState(BaseModel):
    """
    Complete state of a UCP session.

    This is the "RAM" in the MemGPT metaphor - the working context
    that persists across turns.
    """

    session_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Conversation history (working memory)
    messages: list[Message] = Field(default_factory=list)

    # Active toolset (currently injected into context)
    active_tools: list[str] = Field(default_factory=list)

    # Tool usage statistics for this session
    tool_usage: dict[str, int] = Field(default_factory=dict)

    # Scratchpad for reasoning chain
    scratchpad: dict[str, Any] = Field(default_factory=dict)

    # User context (facts about the user, preferences)
    user_context: dict[str, Any] = Field(default_factory=dict)

    def add_message(self, role: str, content: str, **kwargs: Any) -> Message:
        """Add a message to the conversation history."""
        msg = Message(role=role, content=content, **kwargs)
        self.messages.append(msg)
        self.updated_at = datetime.utcnow()
        return msg

    def record_tool_use(self, tool_name: str) -> None:
        """Record that a tool was used."""
        self.tool_usage[tool_name] = self.tool_usage.get(tool_name, 0) + 1
        self.updated_at = datetime.utcnow()

    def get_recent_messages(self, n: int = 10) -> list[Message]:
        """Get the n most recent messages."""
        return self.messages[-n:]

    def get_context_for_routing(self, n_messages: int = 5) -> str:
        """
        Generate a context string for the router.

        Combines recent messages into a single string for embedding.
        """
        recent = self.get_recent_messages(n_messages)
        parts = []
        for msg in recent:
            if msg.role in ("user", "assistant"):
                parts.append(f"{msg.role}: {msg.content}")
        return "\n".join(parts)


class ToolCallRequest(BaseModel):
    """A request to call a tool."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None


class ToolCallResult(BaseModel):
    """Result of a tool call."""

    tool_name: str
    success: bool
    result: Any = None
    error: str | None = None
    execution_time_ms: float = 0


class RoutingDecision(BaseModel):
    """
    The router's decision about which tools to inject.

    Includes confidence scores and reasoning for debugging.
    """

    selected_tools: list[str] = Field(description="Tools to inject into context")
    scores: dict[str, float] = Field(
        default_factory=dict, description="Similarity scores per tool"
    )
    reasoning: str | None = Field(default=None, description="Explanation of selection")
    query_used: str = Field(description="The query used for retrieval")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
