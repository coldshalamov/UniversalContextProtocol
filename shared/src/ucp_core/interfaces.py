"""
Abstract interfaces for UCP Core

This module defines abstract interfaces that both local MVP and cloud versions
must implement. This ensures compatibility and allows for easy swapping
of implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .models import (
    ToolSchema,
    SessionState,
    RoutingDecision,
    Message,
)


class Router(ABC):
    """Abstract interface for routing logic."""

    @abstractmethod
    async def route(
        self,
        session: SessionState,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        """
        Route a query to the appropriate tools.

        Args:
            session: Current session state
            query: User query or context
            context: Additional context for routing

        Returns:
            RoutingDecision with selected tools and scores
        """
        pass

    @abstractmethod
    async def index_tools(self, tools: List[ToolSchema]) -> None:
        """
        Index tools for routing.

        Args:
            tools: List of tools to index
        """
        pass


class ToolZoo(ABC):
    """Abstract interface for tool storage and retrieval."""

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ToolSchema]:
        """
        Search for tools matching the query.

        Args:
            query: Search query
            top_k: Maximum number of results
            filters: Optional filters to apply

        Returns:
            List of matching tools
        """
        pass

    @abstractmethod
    async def add_tool(self, tool: ToolSchema) -> None:
        """
        Add a tool to the zoo.

        Args:
            tool: Tool schema to add
        """
        pass

    @abstractmethod
    async def remove_tool(self, tool_id: str) -> None:
        """
        Remove a tool from the zoo.

        Args:
            tool_id: ID of tool to remove
        """
        pass

    @abstractmethod
    async def get_tool(self, tool_id: str) -> Optional[ToolSchema]:
        """
        Get a tool by ID.

        Args:
            tool_id: ID of tool to retrieve

        Returns:
            Tool schema or None if not found
        """
        pass


class SessionManager(ABC):
    """Abstract interface for session management."""

    @abstractmethod
    async def create_session(
        self,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionState:
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
            metadata: Optional session metadata

        Returns:
            New session state
        """
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session state or None if not found
        """
        pass

    @abstractmethod
    async def save_session(self, session: SessionState) -> None:
        """
        Save a session.

        Args:
            session: Session state to save
        """
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session.

        Args:
            session_id: Session identifier
        """
        pass

    @abstractmethod
    async def list_sessions(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SessionState]:
        """
        List all sessions.

        Args:
            limit: Maximum number of sessions to return
            offset: Offset for pagination

        Returns:
            List of session states
        """
        pass


class ConnectionPool(ABC):
    """Abstract interface for managing connections to downstream servers."""

    @abstractmethod
    async def get_connection(self, server_id: str) -> Any:
        """
        Get a connection to a downstream server.

        Args:
            server_id: Identifier for the downstream server

        Returns:
            Connection object
        """
        pass

    @abstractmethod
    async def release_connection(self, server_id: str, connection: Any) -> None:
        """
        Release a connection back to the pool.

        Args:
            server_id: Identifier for the downstream server
            connection: Connection object to release
        """
        pass

    @abstractmethod
    async def close_all(self) -> None:
        """Close all connections in the pool."""
        pass
Abstract interfaces for UCP Core

This module defines abstract interfaces that both local MVP and cloud versions
must implement. This ensures compatibility and allows for easy swapping
of implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .models import (
    ToolSchema,
    SessionState,
    RoutingDecision,
    Message,
)


class Router(ABC):
    """Abstract interface for routing logic."""

    @abstractmethod
    async def route(
        self,
        session: SessionState,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        """
        Route a query to the appropriate tools.

        Args:
            session: Current session state
            query: User query or context
            context: Additional context for routing

        Returns:
            RoutingDecision with selected tools and scores
        """
        pass

    @abstractmethod
    async def index_tools(self, tools: List[ToolSchema]) -> None:
        """
        Index tools for routing.

        Args:
            tools: List of tools to index
        """
        pass


class ToolZoo(ABC):
    """Abstract interface for tool storage and retrieval."""

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ToolSchema]:
        """
        Search for tools matching the query.

        Args:
            query: Search query
            top_k: Maximum number of results
            filters: Optional filters to apply

        Returns:
            List of matching tools
        """
        pass

    @abstractmethod
    async def add_tool(self, tool: ToolSchema) -> None:
        """
        Add a tool to the zoo.

        Args:
            tool: Tool schema to add
        """
        pass

    @abstractmethod
    async def remove_tool(self, tool_id: str) -> None:
        """
        Remove a tool from the zoo.

        Args:
            tool_id: ID of tool to remove
        """
        pass

    @abstractmethod
    async def get_tool(self, tool_id: str) -> Optional[ToolSchema]:
        """
        Get a tool by ID.

        Args:
            tool_id: ID of tool to retrieve

        Returns:
            Tool schema or None if not found
        """
        pass


class SessionManager(ABC):
    """Abstract interface for session management."""

    @abstractmethod
    async def create_session(
        self,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionState:
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
            metadata: Optional session metadata

        Returns:
            New session state
        """
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session state or None if not found
        """
        pass

    @abstractmethod
    async def save_session(self, session: SessionState) -> None:
        """
        Save a session.

        Args:
            session: Session state to save
        """
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session.

        Args:
            session_id: Session identifier
        """
        pass

    @abstractmethod
    async def list_sessions(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SessionState]:
        """
        List all sessions.

        Args:
            limit: Maximum number of sessions to return
            offset: Offset for pagination

        Returns:
            List of session states
        """
        pass


class ConnectionPool(ABC):
    """Abstract interface for managing connections to downstream servers."""

    @abstractmethod
    async def get_connection(self, server_id: str) -> Any:
        """
        Get a connection to a downstream server.

        Args:
            server_id: Identifier for the downstream server

        Returns:
            Connection object
        """
        pass

    @abstractmethod
    async def release_connection(self, server_id: str, connection: Any) -> None:
        """
        Release a connection back to the pool.

        Args:
            server_id: Identifier for the downstream server
            connection: Connection object to release
        """
        pass

    @abstractmethod
    async def close_all(self) -> None:
        """Close all connections in the pool."""
        pass

