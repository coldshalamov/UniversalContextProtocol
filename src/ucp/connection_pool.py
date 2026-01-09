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
from datetime import datetime
from typing import Any

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
        self._stdio_tasks: dict[str, asyncio.Task[None]] = {}
        self._stdio_stop_events: dict[str, asyncio.Event] = {}
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

        # Keep the stdio client + session open for the lifetime of the pool.
        #
        # `stdio_client()` uses anyio under the hood. Some anyio-based transports require that
        # async context managers are exited in the same asyncio.Task that entered them.
        # Since `connect_all()` can connect in parallel, we run a dedicated background task
        # per server to own the connection lifecycle.
        stop_event = asyncio.Event()
        self._stdio_stop_events[server_config.name] = stop_event

        loop = asyncio.get_running_loop()
        ready: asyncio.Future[None] = loop.create_future()

        async def run_connection() -> None:
            try:
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
                        if not ready.done():
                            ready.set_result(None)

                        await stop_event.wait()
            except Exception as e:
                if not ready.done():
                    ready.set_exception(e)
                raise

        self._stdio_tasks[server_config.name] = asyncio.create_task(run_connection())
        await ready

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
        requested_name = tool_name

        # Find the server for this tool (fully-qualified name preferred)
        server_name = self._tool_to_server.get(tool_name)
        downstream_tool_name: str | None = None

        # If the tool wasn't provided fully-qualified, only treat the prefix as a server name
        # when it matches a configured server. This avoids mis-parsing tool names like
        # "mock.echo" where "mock" is not a server name.
        if not server_name and "." in tool_name:
            prefix, rest = tool_name.split(".", 1)
            if prefix in self._servers:
                server_name = prefix
                downstream_tool_name = rest

        # Search by downstream tool name (display_name) across all servers
        if not server_name:
            for srv_name, srv in self._servers.items():
                for t in srv.tools:
                    if t.display_name == tool_name:
                        server_name = srv_name
                        downstream_tool_name = t.display_name
                        break
                if server_name:
                    break

        if not server_name:
            raise ValueError(f"Tool not found: {requested_name}")

        server = self._servers.get(server_name)
        if not server or server.status != ServerStatus.CONNECTED:
            raise RuntimeError(f"Server not connected: {server_name}")

        session = self._sessions.get(server_name)
        if not session:
            raise RuntimeError(f"No session for server: {server_name}")

        # If the tool name was fully-qualified, strip exactly the server prefix.
        # (Downstream tools are allowed to contain dots.)
        if downstream_tool_name is None:
            prefix = f"{server_name}."
            downstream_tool_name = tool_name[len(prefix):] if tool_name.startswith(prefix) else tool_name

        logger.debug(
            "routing_tool_call",
            tool=downstream_tool_name,
            server=server_name,
            arguments=arguments,
        )

        # Execute the tool call
        result = await session.call_tool(downstream_tool_name, arguments)
        return result

    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        for server_name, server in self._servers.items():
            try:
                if server_name in self._stdio_stop_events:
                    self._stdio_stop_events[server_name].set()

                if server_name in self._sessions:
                    del self._sessions[server_name]
                server.status = ServerStatus.DISCONNECTED
            except Exception as e:
                logger.warning(
                    "disconnect_error",
                    server=server_name,
                    error=str(e),
                )

        # Await background connection tasks so their context managers close cleanly.
        for server_name, task in list(self._stdio_tasks.items()):
            try:
                await task
            except Exception as e:
                logger.warning("disconnect_error", server=server_name, error=str(e))
            finally:
                self._stdio_tasks.pop(server_name, None)
                self._stdio_stop_events.pop(server_name, None)

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
