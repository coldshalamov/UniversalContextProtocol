"""
Connection Pool for Downstream MCP Servers.

Manages persistent connections to multiple MCP servers, handling:
- Stdio subprocess spawning
- SSE/HTTP connections
- Connection lifecycle and health checks
- Tool discovery and caching
- Circuit breaker pattern for fault tolerance
- Retry logic with exponential backoff
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from enum import Enum

import structlog
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool

from ucp.config import DownstreamServerConfig, UCPConfig
from ucp.models import DownstreamServer, ServerStatus, ToolSchema

logger = structlog.get_logger(__name__)


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Circuit is open, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service has recovered


class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance.

    Prevents cascading failures by temporarily stopping requests
    to a failing server after a threshold of consecutive failures.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: datetime | None = None
        self.half_open_calls = 0

    def record_success(self) -> None:
        """Record a successful operation."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                # Service has recovered, close circuit
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.half_open_calls = 0
                logger.info(
                    "circuit_breaker_closed",
                    reason="Service recovered",
                    half_open_calls=self.half_open_calls,
                )
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitBreakerState.HALF_OPEN:
            # Failed during half-open test, reopen circuit
            self.state = CircuitBreakerState.OPEN
            self.half_open_calls = 0
            logger.warning(
                "circuit_breaker_reopened",
                reason="Half-open test failed",
                failure_count=self.failure_count,
            )
        elif self.failure_count >= self.failure_threshold:
            # Threshold reached, open circuit
            self.state = CircuitBreakerState.OPEN
            logger.warning(
                "circuit_breaker_opened",
                failure_count=self.failure_count,
                threshold=self.failure_threshold,
            )

    def can_attempt(self) -> bool:
        """
        Check if a request can be attempted.

        Returns True if circuit is closed or half-open,
        or if timeout has elapsed for open circuit.
        """
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls

        # Circuit is open - check if timeout has elapsed
        if self.last_failure_time:
            elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
            if elapsed >= self.timeout_seconds:
                # Timeout elapsed, transition to half-open
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                logger.info(
                    "circuit_breaker_half_open",
                    elapsed_seconds=elapsed,
                    timeout=self.timeout_seconds,
                )
                return True

        return False

    def get_state(self) -> dict[str, Any]:
        """Get current circuit breaker state for monitoring."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "can_attempt": self.can_attempt(),
        }


class ConnectionPool:
    """
    Manages connections to all downstream MCP servers.

    The pool maintains a registry of connected servers, their tools,
    and handles the routing of tool calls to the correct server.

    Enhanced with circuit breaker pattern and retry logic for fault tolerance.
    """

    def __init__(self, config: UCPConfig) -> None:
        self.config = config
        self._servers: dict[str, DownstreamServer] = {}
        self._sessions: dict[str, ClientSession] = {}
        self._stdio_tasks: dict[str, asyncio.Task[None]] = {}
        self._stdio_stop_events: dict[str, asyncio.Event] = {}
        self._tool_to_server: dict[str, str] = {}  # tool_name -> server_name   
        self._lock = asyncio.Lock()
        # Circuit breakers for each server
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        # Retry configuration
        self._max_retries = 3
        self._retry_delay_base = 1.0  # seconds

    @property
    def all_tools(self) -> list[ToolSchema]:
        """Get all tools from all connected servers."""
        tools = []
        for server in self._servers.values():
            tools.extend(server.tools)
        return tools

    def get_tool_server(self, tool_name: str) -> str | None:
        """Get server name that owns a specific tool."""
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
        # Initialize circuit breaker for this server
        self._circuit_breakers[server_config.name] = CircuitBreaker()

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
        Route a tool call to the appropriate downstream server with retry logic.

        Args:
            tool_name: Fully qualified tool name (server.tool) or just tool name
            arguments: Arguments to pass to the tool

        Returns:
            The result from the tool execution

        Raises:
            ValueError: If the tool is not found
            RuntimeError: If the server is not connected or circuit is open
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
        if not server:
            raise RuntimeError(f"Server not found: {server_name}")

        # Check circuit breaker state
        circuit_breaker = self._circuit_breakers.get(server_name)
        if circuit_breaker and not circuit_breaker.can_attempt():
            raise RuntimeError(
                f"Circuit breaker is open for server {server_name}. "
                f"Too many consecutive failures. Will retry after timeout."
            )

        # Execute with retry logic
        last_exception = None
        for attempt in range(self._max_retries):
            try:
                # Check server status before attempting
                if server.status != ServerStatus.CONNECTED:
                    # Try to reconnect
                    logger.info(
                        "server_not_connected_attempting_reconnect",
                        server=server_name,
                        attempt=attempt + 1,
                    )
                    await self._reconnect_server(server_name)
                    if server.status != ServerStatus.CONNECTED:
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
                    attempt=attempt + 1,
                )

                # Execute the tool call with timeout
                result = await asyncio.wait_for(
                    session.call_tool(downstream_tool_name, arguments),
                    timeout=30.0  # 30 second timeout
                )

                # Record success in circuit breaker
                if circuit_breaker:
                    circuit_breaker.record_success()

                return result

            except asyncio.TimeoutError as e:
                last_exception = e
                logger.warning(
                    "tool_call_timeout",
                    tool=tool_name,
                    server=server_name,
                    attempt=attempt + 1,
                )
                # Mark server as potentially unhealthy
                server.status = ServerStatus.ERROR
                server.error_message = f"Tool call timeout: {str(e)}"
                if circuit_breaker:
                    circuit_breaker.record_failure()

            except Exception as e:
                last_exception = e
                logger.warning(
                    "tool_call_failed",
                    tool=tool_name,
                    server=server_name,
                    error=str(e),
                    attempt=attempt + 1,
                )
                # Mark server as unhealthy
                server.status = ServerStatus.ERROR
                server.error_message = str(e)
                if circuit_breaker:
                    circuit_breaker.record_failure()

            # Exponential backoff before retry
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt)
                logger.info(
                    "retrying_tool_call",
                    tool=tool_name,
                    delay=delay,
                    next_attempt=attempt + 2,
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        raise RuntimeError(
            f"Tool call failed after {self._max_retries} attempts: {requested_name}"
        ) from last_exception

    async def _reconnect_server(self, server_name: str) -> None:
        """Attempt to reconnect to a disconnected server."""
        server = self._servers.get(server_name)
        if not server:
            return

        # Find the server config
        server_config = None
        for config in self.config.downstream_servers:
            if config.name == server_name:
                server_config = config
                break

        if not server_config:
            logger.error("server_config_not_found", server=server_name)
            return

        # Clean up existing connection
        if server_name in self._stdio_stop_events:
            self._stdio_stop_events[server_name].set()

        if server_name in self._stdio_tasks:
            try:
                await self._stdio_tasks[server_name]
            except Exception:
                pass
            finally:
                self._stdio_tasks.pop(server_name, None)

        # Attempt reconnection
        server.status = ServerStatus.CONNECTING
        server.error_message = None
        try:
            if server_config.transport == "stdio":
                await self._connect_stdio(server_config, server)
            server.status = ServerStatus.CONNECTED
            server.last_connected = datetime.utcnow()
            logger.info("server_reconnected", server=server_name)
        except Exception as e:
            server.status = ServerStatus.ERROR
            server.error_message = str(e)
            logger.error("server_reconnection_failed", server=server_name, error=str(e))

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
        self._circuit_breakers.clear()
        logger.info("connection_pool_shutdown")

    def get_server_status(self) -> dict[str, Any]:
        """Get status of all servers for debugging."""
        status = {}
        for name, server in self._servers.items():
            server_info = {
                "status": server.status.value,
                "tool_count": len(server.tools),
                "last_connected": server.last_connected.isoformat() if server.last_connected else None,
                "error": server.error_message,
            }
            # Add circuit breaker state if available
            if name in self._circuit_breakers:
                server_info["circuit_breaker"] = self._circuit_breakers[name].get_state()
            status[name] = server_info
        return status


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
