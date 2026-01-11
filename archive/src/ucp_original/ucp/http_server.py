"""
HTTP/SSE Server for UCP.

Provides HTTP-based access to UCP for web applications and
non-stdio clients. Supports both SSE (Server-Sent Events) for
streaming and REST endpoints for simple requests.
"""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import uuid4

import structlog
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from ucp.config import UCPConfig
from ucp.server import UCPServer

logger = structlog.get_logger(__name__)


# Request/Response Models
class InitializeRequest(BaseModel):
    """MCP initialize request."""

    protocol_version: str = "2024-11-05"
    capabilities: dict = {}
    client_info: dict = {}


class InitializeResponse(BaseModel):
    """MCP initialize response."""

    protocol_version: str
    server_info: dict
    capabilities: dict


class ListToolsResponse(BaseModel):
    """MCP tools/list response."""

    tools: list[dict]


class CallToolRequest(BaseModel):
    """MCP tools/call request."""

    name: str
    arguments: dict = {}


class CallToolResponse(BaseModel):
    """MCP tools/call response."""

    content: list[dict]
    is_error: bool = False


class UpdateContextRequest(BaseModel):
    """Request to update conversation context."""

    message: str
    role: str = "user"


class UCPHttpServer:
    """
    HTTP server wrapper for UCP.

    Provides REST and SSE endpoints for MCP protocol operations.
    """

    def __init__(self, config: UCPConfig | None = None) -> None:
        self.config = config or UCPConfig.load()
        self.ucp: UCPServer | None = None
        self._sessions: dict[str, str] = {}  # http_session -> ucp_session

        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """Create the FastAPI application."""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Manage server lifecycle."""
            # Startup
            self.ucp = UCPServer(self.config)
            await self.ucp.initialize()
            logger.info("http_server_started")

            yield

            # Shutdown
            if self.ucp:
                await self.ucp.shutdown()
            logger.info("http_server_stopped")

        app = FastAPI(
            title="UCP Gateway",
            description="Universal Context Protocol - Intelligent Tool Gateway",
            version=self.config.server.version,
            lifespan=lifespan,
        )

        # Register routes
        self._register_routes(app)

        return app

    def _register_routes(self, app: FastAPI) -> None:
        """Register HTTP routes."""

        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "server": self.config.server.name}

        @app.get("/status")
        async def get_status():
            """Get UCP status."""
            if not self.ucp:
                raise HTTPException(status_code=503, detail="Server not initialized")
            return self.ucp.get_status()

        @app.post("/mcp/initialize")
        async def initialize(request: InitializeRequest) -> InitializeResponse:
            """MCP initialize endpoint."""
            return InitializeResponse(
                protocol_version="2024-11-05",
                server_info={
                    "name": self.config.server.name,
                    "version": self.config.server.version,
                },
                capabilities={
                    "tools": {"listChanged": True},
                },
            )

        @app.get("/mcp/tools/list")
        async def list_tools(session_id: str | None = None) -> ListToolsResponse:
            """
            MCP tools/list endpoint.

            Returns dynamically selected tools based on session context.
            """
            if not self.ucp:
                raise HTTPException(status_code=503, detail="Server not initialized")

            # Get or create session
            if session_id:
                self.ucp._current_session = self.ucp.session_manager.get_or_create_session(
                    session_id
                )

            tools = await self.ucp._list_tools()

            return ListToolsResponse(
                tools=[
                    {
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": t.inputSchema,
                    }
                    for t in tools
                ]
            )

        @app.post("/mcp/tools/call")
        async def call_tool(
            request: CallToolRequest,
            session_id: str | None = None,
        ) -> CallToolResponse:
            """MCP tools/call endpoint."""
            if not self.ucp:
                raise HTTPException(status_code=503, detail="Server not initialized")

            if session_id:
                self.ucp._current_session = self.ucp.session_manager.get_or_create_session(
                    session_id
                )

            result = await self.ucp._call_tool(request.name, request.arguments)

            if result.success:
                return CallToolResponse(
                    content=[{"type": "text", "text": str(result.result)}],
                    is_error=False,
                )
            else:
                return CallToolResponse(
                    content=[{"type": "text", "text": f"Error: {result.error}"}],
                    is_error=True,
                )

        @app.post("/context/update")
        async def update_context(
            request: UpdateContextRequest,
            session_id: str | None = None,
        ):
            """Update the conversation context."""
            if not self.ucp:
                raise HTTPException(status_code=503, detail="Server not initialized")

            if session_id:
                self.ucp._current_session = self.ucp.session_manager.get_or_create_session(
                    session_id
                )

            await self.ucp.update_context(request.message, request.role)

            return {"status": "ok", "session_id": str(self.ucp._current_session.session_id)}

        @app.get("/mcp/sse")
        async def sse_endpoint(request: Request) -> EventSourceResponse:
            """
            SSE endpoint for real-time MCP communication.

            Clients can subscribe to tool updates and routing decisions.
            """

            async def event_generator() -> AsyncGenerator[dict, None]:
                session_id = str(uuid4())

                # Send initial connection event
                yield {
                    "event": "connected",
                    "data": json.dumps({"session_id": session_id}),
                }

                # Keep connection alive and send updates
                while True:
                    if await request.is_disconnected():
                        break

                    # Check for routing updates
                    if self.ucp and self.ucp._last_routing:
                        yield {
                            "event": "tools_updated",
                            "data": json.dumps({
                                "tools": self.ucp._last_routing.selected_tools,
                                "reasoning": self.ucp._last_routing.reasoning,
                            }),
                        }

                    await asyncio.sleep(1)

            return EventSourceResponse(event_generator())

        @app.post("/session/create")
        async def create_session():
            """Create a new UCP session."""
            if not self.ucp:
                raise HTTPException(status_code=503, detail="Server not initialized")

            session = self.ucp.session_manager.create_session()
            return {"session_id": str(session.session_id)}

        @app.get("/session/{session_id}")
        async def get_session(session_id: str):
            """Get session details."""
            if not self.ucp:
                raise HTTPException(status_code=503, detail="Server not initialized")

            session = self.ucp.session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            return {
                "session_id": str(session.session_id),
                "created_at": session.created_at.isoformat(),
                "message_count": len(session.messages),
                "active_tools": session.active_tools,
                "tool_usage": session.tool_usage,
            }

        @app.get("/tools/search")
        async def search_tools(query: str, top_k: int = 5):
            """Search for tools by query."""
            if not self.ucp:
                raise HTTPException(status_code=503, detail="Server not initialized")

            results = self.ucp.tool_zoo.search(query, top_k=top_k)

            return {
                "query": query,
                "results": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "score": score,
                        "server": tool.server_name,
                        "tags": tool.tags,
                    }
                    for tool, score in results
                ],
            }

        @app.get("/tools/all")
        async def list_all_tools():
            """List all indexed tools."""
            if not self.ucp:
                raise HTTPException(status_code=503, detail="Server not initialized")

            tools = self.ucp.tool_zoo.get_all_tools()

            return {
                "total": len(tools),
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description[:100],
                        "server": t.server_name,
                        "tags": t.tags,
                    }
                    for t in tools
                ],
            }


def create_http_app(config_path: str | None = None) -> FastAPI:
    """
    Factory function to create the HTTP app.

    Usage:
        uvicorn ucp.http_server:create_http_app --factory
    """
    config = UCPConfig.load(config_path) if config_path else UCPConfig.load()
    server = UCPHttpServer(config)
    return server.app


# For direct uvicorn invocation
app = None


def get_app() -> FastAPI:
    """Get or create the app instance."""
    global app
    if app is None:
        server = UCPHttpServer()
        app = server.app
    return app
