"""UCP MVP - Local-first implementation

This package contains local-first MVP implementation of UCP,
designed for privacy, simplicity, and immediate user value.
"""

from .server import UCPServer
from .router import Router
from .tool_zoo import ToolZoo, HybridToolZoo
from .session import SessionManager
from .connection_pool import ConnectionPool
from .cli import main as cli_main

__all__ = [
    "UCPServer",
    "Router",
    "ToolZoo",
    "HybridToolZoo",
    "SessionManager",
    "ConnectionPool",
    "cli_main",
]

__version__ = "0.1.0"
