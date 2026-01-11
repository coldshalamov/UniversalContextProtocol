"""
Universal Context Protocol (UCP)

An intelligent gateway that solves "Tool Overload" by dynamically injecting
relevant tool schemas based on conversation context.

UCP presents itself as a single MCP server while internally orchestrating
a fleet of downstream MCP servers, using predictive routing to inject
only the most relevant subset of tools.

Quick Start:
    from ucp import UCPServer, UCPConfig

    config = UCPConfig.load("ucp_config.yaml")
    server = UCPServer(config)
    await server.initialize()
    await server.run_stdio()
"""

__version__ = "0.1.0"

# Core classes
from ucp.server import UCPServer, UCPServerBuilder
from ucp.config import UCPConfig, DownstreamServerConfig

# Components
from ucp.tool_zoo import ToolZoo, HybridToolZoo
from ucp.router import Router, AdaptiveRouter
from ucp.session import SessionManager
from ucp.connection_pool import ConnectionPool, LazyConnectionPool

# Models
from ucp.models import (
    ToolSchema,
    SessionState,
    RoutingDecision,
    ToolCallResult,
)

# LangGraph integration
from ucp.graph import UCPGraph, create_ucp_graph

# RAFT training
from ucp.raft import RAFTDataGenerator, RAFTTrainer, create_raft_pipeline

__all__ = [
    # Version
    "__version__",
    # Core
    "UCPServer",
    "UCPServerBuilder",
    "UCPConfig",
    "DownstreamServerConfig",
    # Components
    "ToolZoo",
    "HybridToolZoo",
    "Router",
    "AdaptiveRouter",
    "SessionManager",
    "ConnectionPool",
    "LazyConnectionPool",
    # Models
    "ToolSchema",
    "SessionState",
    "RoutingDecision",
    "ToolCallResult",
    # LangGraph
    "UCPGraph",
    "create_ucp_graph",
    # RAFT
    "RAFTDataGenerator",
    "RAFTTrainer",
    "create_raft_pipeline",
]
