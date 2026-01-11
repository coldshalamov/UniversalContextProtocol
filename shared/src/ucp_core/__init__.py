"""UCP Core - Shared core abstractions and interfaces

This package contains shared data models, configuration, exceptions,
and abstract interfaces used by both local MVP and cloud versions.
"""

from .models import (
    ToolSchema,
    SessionState,
    RoutingDecision,
    ToolCallResult,
    Message,
)
from .config import UCPConfig
from .exceptions import (
    UCPError,
    ConfigurationError,
    RoutingError,
    ToolNotFoundError,
    SessionError,
    TransportError,
)

__all__ = [
    # Models
    "ToolSchema",
    "SessionState",
    "RoutingDecision",
    "ToolCallResult",
    "Message",
    # Configuration
    "UCPConfig",
    # Exceptions
    "UCPError",
    "ConfigurationError",
    "RoutingError",
    "ToolNotFoundError",
    "SessionError",
    "TransportError",
]

__version__ = "0.1.0"
