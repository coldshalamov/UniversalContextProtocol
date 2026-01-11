"""
Configuration management for UCP.

Supports loading from YAML config files and environment variables.
"""

from __future__ import annotations

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
        default="hybrid", description="Routing strategy for candidate retrieval"
    )
    strategy: Literal["baseline", "sota"] = Field(
        default="baseline", description="Selection strategy: baseline (heuristic) or sota (learned)"
    )
    rerank: bool = Field(default=True, description="Whether to apply re-ranking")
    max_tools: int = Field(default=10, description="Maximum tools to inject")
    min_tools: int = Field(default=1, description="Minimum tools to always include")
    fallback_tools: list[str] = Field(
        default_factory=list, description="Tools to always include as fallback"
    )
    
    # SOTA pipeline options
    use_cross_encoder: bool = Field(
        default=False, description="Use cross-encoder reranker (slower but more accurate)"
    )
    cross_encoder_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Cross-encoder model name for reranking"
    )
    candidate_pool_size: int = Field(
        default=50, description="Number of candidates to retrieve before reranking"
    )
    max_context_tokens: int = Field(
        default=8000, description="Maximum token budget for injected tool schemas"
    )
    max_per_server: int = Field(
        default=15, description="Maximum tools from a single server (diversity)"
    )
    exploration_rate: float = Field(
        default=0.1, description="Epsilon for exploration (0.0 to 1.0)"
    )
    exploration_type: Literal["epsilon", "thompson"] = Field(
        default="epsilon", description="Exploration strategy for bandit"
    )


class TelemetryConfig(BaseModel):
    """Configuration for telemetry and event logging."""
    
    enabled: bool = Field(default=True, description="Enable telemetry logging")
    db_path: str = Field(
        default="./data/telemetry.db", description="SQLite database path for telemetry"
    )
    log_query_text: bool = Field(
        default=False, description="Log raw query text (privacy-sensitive)"
    )
    cleanup_hours: int = Field(
        default=168, description="Delete events older than this (hours)"
    )
    
    # Reward calculation parameters
    latency_scale: float = Field(
        default=0.001, description="Latency penalty scale (per ms)"
    )
    latency_cap: float = Field(
        default=0.3, description="Maximum latency penalty"
    )
    context_scale: float = Field(
        default=0.0001, description="Context cost penalty scale (per token)"
    )
    context_cap: float = Field(
        default=0.2, description="Maximum context cost penalty"
    )


class BanditConfig(BaseModel):
    """Configuration for the shared bandit scorer."""
    
    enabled: bool = Field(default=True, description="Enable bandit scoring")
    db_path: str = Field(
        default="./data/bandit_weights.db", description="Path to persist bandit weights"
    )
    feature_dim: int = Field(default=7, description="Number of input features")
    learning_rate: float = Field(default=0.01, description="SGD learning rate")
    l2_regularization: float = Field(default=0.001, description="L2 regularization weight")
    persist_every_n_updates: int = Field(
        default=10, description="Persist weights every N updates"
    )


class BiasLearningConfig(BaseModel):
    """Configuration for per-tool bias learning."""
    
    enabled: bool = Field(default=True, description="Enable per-tool bias learning")
    db_path: str = Field(
        default="./data/tool_biases.db", description="Path to persist tool biases"
    )
    learning_rate: float = Field(default=0.05, description="Bias learning rate")
    decay_rate: float = Field(default=0.001, description="Decay rate toward zero")
    max_bias: float = Field(default=0.5, description="Maximum bias magnitude")
    enable_delta_vectors: bool = Field(
        default=False, description="Enable embedding delta vectors (higher capacity)"
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
    
    # SOTA pipeline configurations
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    bandit: BanditConfig = Field(default_factory=BanditConfig)
    bias_learning: BiasLearningConfig = Field(default_factory=BiasLearningConfig)

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
        
        # Create directories for SOTA pipeline
        if self.telemetry.enabled:
            Path(self.telemetry.db_path).parent.mkdir(parents=True, exist_ok=True)
        if self.bandit.enabled:
            Path(self.bandit.db_path).parent.mkdir(parents=True, exist_ok=True)
        if self.bias_learning.enabled:
            Path(self.bias_learning.db_path).parent.mkdir(parents=True, exist_ok=True)

