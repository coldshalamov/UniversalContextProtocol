"""
UCP Server - The Virtual MCP Gateway.

This is main entry point. UCP presents itself as a single MCP server
to upstream clients (Claude, Cursor, etc.) while internally orchestrating
a fleet of downstream MCP servers.

Key behaviors:
- Intercepts tools/list: Returns dynamically selected tools based on context
- Intercepts tools/call: Routes to the correct downstream server
- Maintains session state for context continuity
"""

from __future__ import annotations

import time
from typing import Any, Sequence

import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

from .config import UCPConfig
from .connection_pool import ConnectionPool, LazyConnectionPool
from .models import RoutingDecision, SessionState, ToolCallResult
from .router import AdaptiveRouter, Router
from .session import SessionManager
from .tool_zoo import HybridToolZoo, ToolZoo
from .telemetry import (
    get_telemetry_store,
    get_jsonl_exporter,
    get_prometheus_metrics,
    RoutingEvent,
    ToolCallEvent,
    hash_query,
)

logger = structlog.get_logger(__name__)


class UCPServer:
    """
    The Universal Context Protocol Server.

    Presents as a single MCP server while orchestrating multiple
    downstream servers with intelligent tool selection.
    """

    def __init__(self, config: UCPConfig | None = None) -> None:
        self.config = config or UCPConfig.load()

        # Initialize components
        self.tool_zoo: ToolZoo = HybridToolZoo(self.config.tool_zoo)
        self.router: Router = AdaptiveRouter(self.config.router, self.tool_zoo)
        self.session_manager = SessionManager(self.config.session)
        self.connection_pool: ConnectionPool = LazyConnectionPool(self.config)

        # Telemetry integration
        self._telemetry_store = get_telemetry_store()
        self._jsonl_exporter = get_jsonl_exporter()
        self._prometheus_metrics = get_prometheus_metrics()

        # MCP Server instance
        self._server = Server(self.config.server.name)

        # Current session (for single-client mode)
        self._current_session: SessionState | None = None
        self._last_routing: RoutingDecision | None = None

        # Register MCP handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self._server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """
            Handle tools/list request.

            This is the magic of UCP - instead of returning all tools,
            we return only the tools predicted to be relevant.
            """
            return await self._list_tools()

        @self._server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> Sequence[TextContent]:
            """
            Handle tools/call request.

            Routes the call to the appropriate downstream server.
            """
            result = await self._call_tool(name, arguments or {})

            if result.success:
                return [TextContent(type="text", text=str(result.result))]
            else:
                return [TextContent(type="text", text=f"Error: {result.error}")]

    async def _list_tools(self) -> list[Tool]:
        """
        Generate a dynamic tool list based on current context.

        This implements the core UCP innovation: context-aware tool injection.
        """
        # Ensure we have a session
        if not self._current_session:
            self._current_session = self.session_manager.create_session()

        # Generate a new request ID for this operation
        start_time = time.time()
        
        # Route to get relevant tools
        self._last_routing = await self.router.route(self._current_session)
        selection_time_ms = (time.time() - start_time) * 1000
        
        # Log routing event to telemetry
        routing_event = RoutingEvent(
            session_id=self._current_session.session_id,
            request_id=self.session_manager._current_request_id,
            trace_id=self.session_manager._current_trace_id,
            query_hash=hash_query(self._last_routing.query_used),
            query_text=self._last_routing.query_used,
            selected_tools=self._last_routing.selected_tools,
            total_candidates=len(self._last_routing.selected_tools),
            selection_time_ms=selection_time_ms,
            strategy=self._last_routing.reasoning,
        )
        self._telemetry_store.log_routing_event(routing_event)
        self._jsonl_exporter.export_routing_event(routing_event)
        self._prometheus_metrics.observe_router_latency(selection_time_ms)

        # Convert to MCP Tool format
        tools: list[Tool] = []

        for tool_name in self._last_routing.selected_tools:
            tool_schema = self.tool_zoo.get_tool(tool_name)
            if tool_schema:
                tools.append(Tool(
                    name=tool_schema.name,
                    description=tool_schema.description,
                    inputSchema=tool_schema.input_schema,
                ))

        logger.info(
            "tools_listed",
            count=len(tools),
            session_id=str(self._current_session.session_id),
            reasoning=self._last_routing.reasoning,
        )

        return tools

    async def _call_tool(self, name: str, arguments: dict[str, Any]) -> ToolCallResult:
        """
        Execute a tool call by routing to the appropriate server.
        """
        start_time = time.time()

        try:
            # Route to connection pool
            result = await self.connection_pool.call_tool(name, arguments)

            execution_time = (time.time() - start_time) * 1000

            # Record usage
            if self._current_session:
                self._current_session.record_tool_use(name)
                self.session_manager.log_tool_usage(
                    self._current_session.session_id,
                    name,
                    success=True,
                    execution_time_ms=execution_time,
                )

            # Log tool call to telemetry
            tool_call_event = ToolCallEvent(
                session_id=self._current_session.session_id,
                request_id=self.session_manager._current_request_id,
                routing_event_id=self._last_routing.event_id if self._last_routing else None,
                trace_id=self.session_manager._current_trace_id,
                tool_name=name,
                success=True,
                execution_time_ms=execution_time,
                was_selected=name in self._last_routing.selected_tools if self._last_routing else [],
                selection_rank=self._last_routing.selected_tools.index(name) if self._last_routing and name in self._last_routing.selected_tools else -1,
            )
            self._telemetry_store.log_tool_call(tool_call_event)
            self._jsonl_exporter.export_tool_call(tool_call_event)
            self._prometheus_metrics.inc_tool_invocation(name, success=True)

            # Update router with actual usage
            if isinstance(self.router, AdaptiveRouter) and self._last_routing:
                self.router.record_usage(self._last_routing, [name])

            logger.info(
                "tool_called",
                tool=name,
                success=True,
                time_ms=execution_time,
            )

            return ToolCallResult(
                tool_name=name,
                success=True,
                result=result,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000

            if self._current_session:
                self.session_manager.log_tool_usage(
                    self._current_session.session_id,
                    name,
                    success=False,
                    execution_time_ms=execution_time,
                    error=str(e),
                )

            # Log failed tool call to telemetry
            tool_call_event = ToolCallEvent(
                session_id=self._current_session.session_id if self._current_session else None,
                request_id=self.session_manager._current_request_id,
                routing_event_id=self._last_routing.event_id if self._last_routing else None,
                trace_id=self.session_manager._current_trace_id,
                tool_name=name,
                success=False,
                error_class=type(e).__name__,
                error_message=str(e),
                execution_time_ms=execution_time,
                was_selected=name in self._last_routing.selected_tools if self._last_routing else [],
                selection_rank=self._last_routing.selected_tools.index(name) if self._last_routing and name in self._last_routing.selected_tools else -1,
            )
            self._telemetry_store.log_tool_call(tool_call_event)
            self._jsonl_exporter.export_tool_call(tool_call_event)
            self._prometheus_metrics.inc_tool_invocation(name, success=False)

            logger.error(
                "tool_call_failed",
                tool=name,
                error=str(e),
            )

            return ToolCallResult(
                tool_name=name,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )

    async def update_context(self, message: str, role: str = "user") -> None:
        """
        Update session context with a new message.

        Call this to inform UCP of conversation updates so it can
        adjust tool selection accordingly.
        """
        if not self._current_session:
            self._current_session = self.session_manager.create_session()

        self._current_session.add_message(role, message)

        # Check if we should archive old messages
        if len(self._current_session.messages) > self.config.session.max_messages:
            self.session_manager.archive_messages(
                self._current_session,
                keep_recent=self.config.session.max_messages // 2,
            )

        self.session_manager.save_session(self._current_session)

    async def initialize(self) -> None:
        """
        Initialize UCP - connect to downstream servers and index tools.
        """
        logger.info("ucp_initializing")

        # Ensure directories exist
        self.config.ensure_directories()

        # Initialize tool zoo
        self.tool_zoo.initialize()

        # Connect to downstream servers
        await self.connection_pool.connect_all()

        # Index all discovered tools
        all_tools = self.connection_pool.all_tools
        if all_tools:
            self.tool_zoo.add_tools(all_tools)

        logger.info(
            "ucp_initialized",
            downstream_servers=len(self.config.downstream_servers),
            total_tools=len(all_tools),
        )

    async def shutdown(self) -> None:
        """Gracefully shutdown UCP."""
        logger.info("ucp_shutting_down")

        try:
            await self.connection_pool.disconnect_all()
        except Exception as e:
            logger.warning("shutdown_error", component="connection_pool", error=str(e))

        try:
            self.tool_zoo.close()
        except Exception as e:
            logger.warning("shutdown_error", component="tool_zoo", error=str(e))

        try:
            self.session_manager.close()
        except Exception as e:
            logger.warning("shutdown_error", component="session_manager", error=str(e))

        # Close telemetry store
        try:
            self._telemetry_store.close()
        except Exception as e:
            logger.warning("shutdown_error", component="telemetry_store", error=str(e))

        logger.info("ucp_shutdown_complete")

    async def run_stdio(self) -> None:
        """Run UCP as a stdio MCP server."""
        await self.initialize()

        try:
            async with stdio_server() as (read_stream, write_stream):
                await self._server.run(
                    read_stream,
                    write_stream,
                    self._server.create_initialization_options(),
                )
        finally:
            await self.shutdown()

    def get_status(self) -> dict[str, Any]:
        """Get current UCP status for debugging."""
        return {
            "server": {
                "name": self.config.server.name,
                "version": self.config.server.version,
            },
            "downstream_servers": self.connection_pool.get_server_status(),
            "tool_zoo": self.tool_zoo.get_stats(),
            "router": (
                self.router.get_learning_stats()
                if isinstance(self.router, AdaptiveRouter)
                else {}
            ),
            "current_session": (
                str(self._current_session.session_id)
                if self._current_session
                else None
            ),
            "last_routing": (
                {
                    "selected_tools": self._last_routing.selected_tools,
                    "reasoning": self._last_routing.reasoning,
                }
                if self._last_routing
                else None
            ),
        }


class UCPServerBuilder:
    """
    Builder pattern for constructing UCP servers with custom components.
    """

    def __init__(self) -> None:
        self._config: UCPConfig | None = None
        self._tool_zoo: ToolZoo | None = None
        self._router: Router | None = None
        self._session_manager: SessionManager | None = None
        self._connection_pool: ConnectionPool | None = None

    def with_config(self, config: UCPConfig) -> UCPServerBuilder:
        self._config = config
        return self

    def with_config_file(self, path: str) -> UCPServerBuilder:
        self._config = UCPConfig.from_yaml(path)
        return self

    def with_tool_zoo(self, tool_zoo: ToolZoo) -> UCPServerBuilder:
        self._tool_zoo = tool_zoo
        return self

    def with_router(self, router: Router) -> UCPServerBuilder:
        self._router = router
        return self

    def with_session_manager(self, session_manager: SessionManager) -> UCPServerBuilder:
        self._session_manager = session_manager
        return self

    def with_connection_pool(self, pool: ConnectionPool) -> UCPServerBuilder:
        self._connection_pool = pool
        return self

    def build(self) -> UCPServer:
        """Build UCP server with configured components."""
        config = self._config or UCPConfig.load()

        server = UCPServer(config)

        if self._tool_zoo:
            server.tool_zoo = self._tool_zoo
        if self._router:
            server.router = self._router
        if self._session_manager:
            server.session_manager = self._session_manager
        if self._connection_pool:
            server.connection_pool = self._connection_pool

        return server
