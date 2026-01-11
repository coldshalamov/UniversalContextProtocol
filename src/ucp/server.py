"""
UCP Server - The Virtual MCP Gateway.

This is the main entry point. UCP presents itself as a single MCP server
to upstream clients (Claude, Cursor, etc.) while internally orchestrating
a fleet of downstream MCP servers.

Key behaviors:
- Intercepts tools/list: Returns dynamically selected tools based on context
- Intercepts tools/call: Routes to correct downstream server
- Maintains session state for context continuity

Enhanced with error injection for self-correction and graceful degradation.
"""

from __future__ import annotations

from typing import Any, Sequence

import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

from ucp.config import UCPConfig
from ucp.connection_pool import ConnectionPool, LazyConnectionPool
from ucp.models import RoutingDecision, SessionState, ToolCallResult
from ucp.router import AdaptiveRouter, Router
from ucp.session import SessionManager
from ucp.tool_zoo import HybridToolZoo, ToolZoo

logger = structlog.get_logger(__name__)


class UCPServer:
    """
    The Universal Context Protocol Server.

    Presents as a single MCP server while orchestrating multiple
    downstream servers with intelligent tool selection.
    
    Enhanced with error injection for self-correction.
    """

    def __init__(self, config: UCPConfig | None = None) -> None:
        self.config = config or UCPConfig.load()

        # Initialize components
        self.tool_zoo: ToolZoo = HybridToolZoo(self.config.tool_zoo)
        self.router: Router = AdaptiveRouter(self.config.router, self.tool_zoo)
        self.session_manager = SessionManager(self.config.session)
        self.connection_pool: ConnectionPool = LazyConnectionPool(self.config)

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
            Enhanced with error injection for self-correction.
            """
            result = await self._call_tool(name, arguments or {})

            if result.success:
                return [TextContent(type="text", text=str(result.result))]
            else:
                # Return error message with context for self-correction
                error_msg = self._format_error_for_self_correction(name, arguments, result.error)
                return [TextContent(type="text", text=error_msg)]

    def _format_error_for_self_correction(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        error: str,
    ) -> str:
        """
        Format error message to enable self-correction.

        Injects the error into context with helpful information
        for the AI to potentially retry with different parameters or tools.
        """
        # Get tool schema for context
        tool_schema = self.tool_zoo.get_tool(tool_name)
        
        error_parts = [
            f"Error calling tool '{tool_name}':",
            f"  {error}",
        ]
        
        # Add tool information for context
        if tool_schema:
            error_parts.append(f"  Tool description: {tool_schema.description}")
            if tool_schema.input_schema and tool_schema.input_schema.get("properties"):
                params = list(tool_schema.input_schema["properties"].keys())
                error_parts.append(f"  Available parameters: {', '.join(params)}")
        
        # Add what was attempted
        if arguments:
            error_parts.append(f"  Attempted with arguments: {arguments}")
        
        # Suggest potential fixes
        error_parts.append("  Please try again with:")
        error_parts.append("    - Different or corrected arguments")
        error_parts.append("    - A different tool if this one is unavailable")
        
        return "\n".join(error_parts)

    async def _list_tools(self) -> list[Tool]:
        """
        Generate a dynamic tool list based on the current context.

        This implements the core UCP innovation: context-aware tool injection.
        """
        # Ensure we have a session
        if not self._current_session:
            self._current_session = self.session_manager.create_session()

        # Route to get relevant tools
        self._last_routing = await self.router.route(self._current_session)

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
        
        Enhanced with error injection for self-correction.
        """
        import time
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

        except ValueError as e:
            # Tool not found - provide helpful error
            execution_time = (time.time() - start_time) * 1000
            
            error_msg = f"Tool '{name}' not found. Available tools: {[t.name for t in self.tool_zoo.all_tools[:10]]}"
            
            if self._current_session:
                self.session_manager.log_tool_usage(
                    self._current_session.session_id,
                    name,
                    success=False,
                    execution_time_ms=execution_time,
                    error=str(e),
                )

            logger.error(
                "tool_not_found",
                tool=name,
                error=str(e),
            )

            return ToolCallResult(
                tool_name=name,
                success=False,
                error=error_msg,
                execution_time_ms=execution_time,
            )

        except RuntimeError as e:
            # Server not connected or circuit breaker open
            execution_time = (time.time() - start_time) * 1000
            
            if self._current_session:
                self.session_manager.log_tool_usage(
                    self._current_session.session_id,
                    name,
                    success=False,
                    execution_time_ms=execution_time,
                    error=str(e),
                )

            logger.error(
                "tool_call_server_error",
                tool=name,
                error=str(e),
            )

            # Inject error with context for self-correction
            formatted_error = self._format_error_for_self_correction(name, arguments, str(e))
            
            return ToolCallResult(
                tool_name=name,
                success=False,
                error=formatted_error,
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

            logger.error(
                "tool_call_failed",
                tool=name,
                error=str(e),
            )

            # Inject error with context for self-correction
            formatted_error = self._format_error_for_self_correction(name, arguments, str(e))
            
            return ToolCallResult(
                tool_name=name,
                success=False,
                error=formatted_error,
                execution_time_ms=execution_time,
            )

    async def update_context(self, message: str, role: str = "user") -> None:
        """
        Update the session context with a new message.

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
