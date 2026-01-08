"""
Connection Pool for Downstream MCP Servers.

Manages persistent connections to multiple MCP servers, handling:
- Stdio subprocess spawning
- SSE/HTTP connections
- Connection lifecycle and health checks
- Tool discovery and caching
"""

from __future__ import annotations

import asyncio
import subprocess
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncIterator

import structlog
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool

from ucp.config import DownstreamServerConfig, UCPConfig
from ucp.models import DownstreamServer, ServerStatus, ToolSchema

logger = structlog.get_logger(__name__)


class ConnectionPool:
    """
    Manages connections to all downstream MCP servers.

    The pool maintains a registry of connected servers, their tools,
    and handles the routing of tool calls to the correct server.
    """

    def __init__(self, config: UCPConfig) -> None:
        self.config = config
        self._servers: dict[str, DownstreamServer] = {}
        self._sessions: dict[str, ClientSession] = {}
        self._tool_to_server: dict[str, str] = {}  # tool_name -> server_name
        self._lock = asyncio.Lock()

    @property
    def all_tools(self) -> list[ToolSchema]:
        """Get all tools from all connected servers."""
        tools = []
        for server in self._servers.values():
            tools.extend(server.tools)
        return tools

    def get_tool_server(self, tool_name: str) -> str | None:
        """Get the server name that owns a specific tool."""
        return self._tool_to_server.get(tool_name)

    async def connect_all(self) -> None:
        """Connect to all configured downstream servers."""
        tasks = [
            self._connect_server(server_config)
            for server_config in self.config.downstream_servers
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        connected = sum(1 for s in self._servers.values() if s.status == ServerStatus.CONNECTED)
        logger.info(
            "connection_pool_initialized",
            total_servers=len(self.config.downstream_servers),
            connected=connected,
            total_tools=len(self._tool_to_server),
        )

    async def _connect_server(self, server_config: DownstreamServerConfig) -> None:
        """Connect to a single downstream server."""
        server = DownstreamServer(
            name=server_config.name,
            status=ServerStatus.CONNECTING,
            transport_type=server_config.transport,
        )
        self._servers[server_config.name] = server

        try:
            if server_config.transport == "stdio":
                await self._connect_stdio(server_config, server)
            else:
                # TODO: Implement SSE and HTTP transports
                logger.warning(
                    "transport_not_implemented",
                    transport=server_config.transport,
                    server=server_config.name,
                )
                server.status = ServerStatus.ERROR
                server.error_message = f"Transport {server_config.transport} not yet implemented"
                return

            server.status = ServerStatus.CONNECTED
            server.last_connected = datetime.utcnow()

            logger.info(
                "server_connected",
                server=server_config.name,
                tool_count=len(server.tools),
            )

        except Exception as e:
            server.status = ServerStatus.ERROR
            server.error_message = str(e)
            logger.error(
                "server_connection_failed",
                server=server_config.name,
                error=str(e),
            )

    async def _connect_stdio(
        self, server_config: DownstreamServerConfig, server: DownstreamServer
    ) -> None:
        """Connect to a stdio-based MCP server."""
        if not server_config.command:
            raise ValueError(f"No command specified for stdio server: {server_config.name}")

        server_params = StdioServerParameters(
            command=server_config.command,
            args=server_config.args,
            env={**server_config.env} if server_config.env else None,
        )

        # Create the stdio client connection
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()

                # Discover tools
                tools_result = await session.list_tools()
                server.tools = self._convert_tools(
                    tools_result.tools, server_config.name, server_config.tags
                )

                # Register tool -> server mapping
                for tool in server.tools:
                    self._tool_to_server[tool.name] = server_config.name

                # Store session for later use
                self._sessions[server_config.name] = session

    def _convert_tools(
        self, mcp_tools: list[Tool], server_name: str, tags: list[str]
    ) -> list[ToolSchema]:
        """Convert MCP Tool objects to our normalized ToolSchema."""
        schemas = []
        for tool in mcp_tools:
            schema = ToolSchema(
                name=f"{server_name}.{tool.name}",
                display_name=tool.name,
                description=tool.description or "",
                server_name=server_name,
                input_schema=tool.inputSchema if tool.inputSchema else {},
                tags=tags,
            )
            schemas.append(schema)
        return schemas

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        Route a tool call to the appropriate downstream server.

        Args:
            tool_name: Fully qualified tool name (server.tool) or just tool name
            arguments: Arguments to pass to the tool

        Returns:
            The result from the tool execution

        Raises:
            ValueError: If the tool is not found
            RuntimeError: If the server is not connected
        """
        # Find the server for this tool
        server_name = self._tool_to_server.get(tool_name)

        # If not found, try stripping server prefix
        if not server_name and "." in tool_name:
            parts = tool_name.split(".", 1)
            server_name = parts[0]
            tool_name = parts[1]
        elif not server_name:
            # Search all servers
            for srv_name, srv in self._servers.items():
                for t in srv.tools:
                    if t.display_name == tool_name:
                        server_name = srv_name
                        break
                if server_name:
                    break

        if not server_name:
            raise ValueError(f"Tool not found: {tool_name}")

        server = self._servers.get(server_name)
        if not server or server.status != ServerStatus.CONNECTED:
            raise RuntimeError(f"Server not connected: {server_name}")

        session = self._sessions.get(server_name)
        if not session:
            raise RuntimeError(f"No session for server: {server_name}")

        # Extract just the tool name without server prefix
        simple_name = tool_name.split(".")[-1] if "." in tool_name else tool_name

        logger.debug(
            "routing_tool_call",
            tool=simple_name,
            server=server_name,
            arguments=arguments,
        )

        # Execute the tool call
        result = await session.call_tool(simple_name, arguments)
        return result

    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        for server_name, server in self._servers.items():
            try:
                if server_name in self._sessions:
                    # Session cleanup is handled by context manager
                    del self._sessions[server_name]
                server.status = ServerStatus.DISCONNECTED
            except Exception as e:
                logger.warning(
                    "disconnect_error",
                    server=server_name,
                    error=str(e),
                )

        self._tool_to_server.clear()
        logger.info("connection_pool_shutdown")

    def get_server_status(self) -> dict[str, Any]:
        """Get status of all servers for debugging."""
        return {
            name: {
                "status": server.status.value,
                "tool_count": len(server.tools),
                "last_connected": server.last_connected.isoformat() if server.last_connected else None,
                "error": server.error_message,
            }
            for name, server in self._servers.items()
        }


class LazyConnectionPool(ConnectionPool):
    """
    A connection pool that connects to servers on-demand.

    This is more efficient when you have many servers but only
    use a few at a time.
    """

    def __init__(self, config: UCPConfig) -> None:
        super().__init__(config)
        self._config_by_name: dict[str, DownstreamServerConfig] = {
            s.name: s for s in config.downstream_servers
        }

    async def connect_all(self) -> None:
        """For lazy pool, we only index tools without connecting."""
        # We could pre-fetch tool lists via a lightweight probe
        # For now, we require explicit connection
        logger.info(
            "lazy_pool_initialized",
            available_servers=list(self._config_by_name.keys()),
        )

    async def ensure_connected(self, server_name: str) -> None:
        """Ensure a specific server is connected."""
        if server_name in self._servers:
            server = self._servers[server_name]
            if server.status == ServerStatus.CONNECTED:
                return

        config = self._config_by_name.get(server_name)
        if not config:
            raise ValueError(f"Unknown server: {server_name}")

        await self._connect_server(config)

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool, connecting to the server if needed."""
        # Determine server name
        if "." in tool_name:
            server_name = tool_name.split(".")[0]
        else:
            server_name = self._tool_to_server.get(tool_name)

        if server_name:
            await self.ensure_connected(server_name)

        return await super().call_tool(tool_name, arguments)
