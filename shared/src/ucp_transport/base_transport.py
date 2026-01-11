"""
Base transport class for MCP protocol communication.

This module provides the abstract base class that all transport implementations
must follow.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ..ucp_core.models import ToolSchema, ToolCallResult


class BaseTransport(ABC):
    """Abstract base class for MCP transport implementations."""

    @abstractmethod
    async def connect(
        self,
        server_config: Dict[str, Any],
    ) -> None:
        """
        Connect to an MCP server.

        Args:
            server_config: Configuration for the server
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        pass

    @abstractmethod
    async def list_tools(self) -> List[ToolSchema]:
        """
        List available tools from the connected server.

        Returns:
            List of tool schemas
        """
        pass

    @abstractmethod
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> ToolCallResult:
        """
        Call a tool on the connected server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Result of the tool call
        """
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """
        Check if transport is connected.

        Returns:
            True if connected, False otherwise
        """
        pass

    @abstractmethod
    async def get_server_info(self) -> Dict[str, Any]:
        """
        Get information about the connected server.

        Returns:
            Server information dictionary
        """
        pass
Base transport class for MCP protocol communication.

This module provides the abstract base class that all transport implementations
must follow.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ..ucp_core.models import ToolSchema, ToolCallResult


class BaseTransport(ABC):
    """Abstract base class for MCP transport implementations."""

    @abstractmethod
    async def connect(
        self,
        server_config: Dict[str, Any],
    ) -> None:
        """
        Connect to an MCP server.

        Args:
            server_config: Configuration for the server
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        pass

    @abstractmethod
    async def list_tools(self) -> List[ToolSchema]:
        """
        List available tools from the connected server.

        Returns:
            List of tool schemas
        """
        pass

    @abstractmethod
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> ToolCallResult:
        """
        Call a tool on the connected server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Result of the tool call
        """
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """
        Check if transport is connected.

        Returns:
            True if connected, False otherwise
        """
        pass

    @abstractmethod
    async def get_server_info(self) -> Dict[str, Any]:
        """
        Get information about the connected server.

        Returns:
            Server information dictionary
        """
        pass

