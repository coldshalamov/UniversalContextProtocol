"""
Shared exceptions for UCP Core

This module defines all custom exceptions used across the UCP system.
"""


class UCPError(Exception):
    """Base exception for all UCP-related errors."""
    pass


class ConfigurationError(UCPError):
    """Raised when there's an error in configuration."""
    pass


class RoutingError(UCPError):
    """Raised when routing fails or produces invalid results."""
    pass


class ToolNotFoundError(UCPError):
    """Raised when a requested tool is not found."""
    pass


class SessionError(UCPError):
    """Raised when session operations fail."""
    pass


class TransportError(UCPError):
    """Raised when transport layer operations fail."""
    pass


class ToolCallError(UCPError):
    """Raised when a tool call fails."""
    pass


class ConnectionError(UCPError):
    """Raised when connection to downstream server fails."""
    pass


class ValidationError(UCPError):
    """Raised when data validation fails."""
    pass
Shared exceptions for UCP Core

This module defines all custom exceptions used across the UCP system.
"""


class UCPError(Exception):
    """Base exception for all UCP-related errors."""
    pass


class ConfigurationError(UCPError):
    """Raised when there's an error in configuration."""
    pass


class RoutingError(UCPError):
    """Raised when routing fails or produces invalid results."""
    pass


class ToolNotFoundError(UCPError):
    """Raised when a requested tool is not found."""
    pass


class SessionError(UCPError):
    """Raised when session operations fail."""
    pass


class TransportError(UCPError):
    """Raised when transport layer operations fail."""
    pass


class ToolCallError(UCPError):
    """Raised when a tool call fails."""
    pass


class ConnectionError(UCPError):
    """Raised when connection to downstream server fails."""
    pass


class ValidationError(UCPError):
    """Raised when data validation fails."""
    pass

