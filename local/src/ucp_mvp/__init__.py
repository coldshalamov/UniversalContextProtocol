"""
UCP MVP - Local-first implementation

This package contains local-first MVP implementation of UCP,
designed for privacy, simplicity, and immediate user value.
"""

from .server import UCPServer
from .router import Router
from .tool_zoo import LocalToolZoo
from .session import SQLiteSessionManager
from .connection_pool import ConnectionPool
from .cli import main as cli_main
from .dashboard import run_dashboard

__all__ = [
    "UCPServer",
    "Router",
    "LocalToolZoo",
    "SQLiteSessionManager",
    "ConnectionPool",
    "cli_main",
    "run_dashboard",
]

__version__ = "0.1.0"
