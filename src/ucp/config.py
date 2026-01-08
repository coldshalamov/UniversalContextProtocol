"""
Configuration management for UCP.

Supports loading from YAML config files and environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DownstreamServerConfig(BaseModel):
    """Configuration for a single downstream MCP server."""

    name: str = Field(description="Unique identifier for this server")
    transport: Literal["stdio", "sse", "streamable-http"] = Field(
        default="stdio", description="Transport protocol"
    )
    # For stdio transport
    command: str | None = Field(default=None, description="Command to spawn the server")
    args: list[str] = Field(default_factory=list, description="Arguments for the command")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    # For HTTP transports
    url: str | None = Field(default=None, description="URL for SSE/HTTP transport")
    # Metadata
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    description: str = Field(default="", description="Human-readable description")


class ToolZooConfig(BaseModel):
    """Configuration for the Tool Zoo (vector index)."""

    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", description="Sentence transformer model for embeddings"
    )
    collection_name: str = Field(default="ucp_tools", description="ChromaDB collection name")
    persist_directory: str = Field(
        default="./data/chromadb", description="Directory to persist ChromaDB"
    )
    top_k: int = Field(default=5, description="Default number of tools to retrieve")
    similarity_threshold: float = Field(
        default=0.3, description="Minimum similarity score to include a tool"
    )


class RouterConfig(BaseModel):
    """Configuration for the semantic router."""

    mode: Literal["semantic", "keyword", "hybrid"] = Field(
        default="semantic", description="Routing strategy"
    )
    rerank: bool = Field(default=True, description="Whether to apply re-ranking")
    max_tools: int = Field(default=10, description="Maximum tools to inject")
    min_tools: int = Field(default=1, description="Minimum tools to always include")
    fallback_tools: list[str] = Field(
        default_factory=list, description="Tools to always include as fallback"
    )


class SessionConfig(BaseModel):
    """Configuration for session management."""

    persistence: Literal["memory", "sqlite", "redis"] = Field(
        default="sqlite", description="Where to persist session state"
    )
    sqlite_path: str = Field(
        default="./data/sessions.db", description="SQLite database path"
    )
    ttl_seconds: int = Field(default=3600, description="Session time-to-live")
    max_messages: int = Field(default=100, description="Max messages to keep in context")


class ServerConfig(BaseModel):
    """Configuration for the UCP server itself."""

    host: str = Field(default="127.0.0.1", description="Host to bind to")
    port: int = Field(default=8765, description="Port to bind to")
    transport: Literal["stdio", "sse", "streamable-http"] = Field(
        default="stdio", description="Transport for upstream clients"
    )
    name: str = Field(default="UCP Gateway", description="Server name")
    version: str = Field(default="0.1.0", description="Server version")


class UCPConfig(BaseSettings):
    """Root configuration for UCP."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    tool_zoo: ToolZooConfig = Field(default_factory=ToolZooConfig)
    router: RouterConfig = Field(default_factory=RouterConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    downstream_servers: list[DownstreamServerConfig] = Field(default_factory=list)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    model_config = {"env_prefix": "UCP_", "env_nested_delimiter": "__"}

    @classmethod
    def from_yaml(cls, path: str | Path) -> UCPConfig:
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(**data)

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> UCPConfig:
        """
        Load configuration from multiple sources with precedence:
        1. Environment variables (highest)
        2. Config file (if provided)
        3. Defaults (lowest)
        """
        # Start with defaults
        config_data: dict = {}

        # Load from file if provided
        if config_path:
            path = Path(config_path)
            if path.exists():
                with open(path) as f:
                    config_data = yaml.safe_load(f) or {}

        # Check standard locations
        if not config_data:
            standard_paths = [
                Path("ucp_config.yaml"),
                Path("ucp_config.yml"),
                Path.home() / ".config" / "ucp" / "config.yaml",
            ]
            for std_path in standard_paths:
                if std_path.exists():
                    with open(std_path) as f:
                        config_data = yaml.safe_load(f) or {}
                    break

        return cls(**config_data)

    def ensure_directories(self) -> None:
        """Create necessary directories for persistence."""
        Path(self.tool_zoo.persist_directory).mkdir(parents=True, exist_ok=True)
        Path(self.session.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
