"""
Transport Implementations for Downstream MCP Servers.

Supports:
- Stdio (subprocess-based servers)
- SSE (Server-Sent Events over HTTP)
- Streamable HTTP
"""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator
from dataclasses import dataclass

import httpx
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MCPMessage:
    """An MCP protocol message."""

    jsonrpc: str = "2.0"
    id: int | str | None = None
    method: str | None = None
    params: dict | None = None
    result: Any = None
    error: dict | None = None


class Transport(ABC):
    """Abstract base class for MCP transports."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        pass

    @abstractmethod
    async def send(self, message: MCPMessage) -> MCPMessage:
        """Send a message and wait for response."""
        pass

    @abstractmethod
    async def subscribe(self) -> AsyncIterator[MCPMessage]:
        """Subscribe to server-initiated messages."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected."""
        pass


class SSETransport(Transport):
    """
    Server-Sent Events transport for MCP.

    Uses HTTP POST for requests and SSE for responses/notifications.
    """

    def __init__(
        self,
        url: str,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.headers = headers or {}
        self._client: httpx.AsyncClient | None = None
        self._message_id = 0
        self._pending_responses: dict[int, asyncio.Future] = {}
        self._connected = False
        self._sse_task: asyncio.Task | None = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """Connect to the SSE server."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers=self.headers,
        )

        # Test connection with initialize
        try:
            # Start SSE listener
            self._sse_task = asyncio.create_task(self._listen_sse())
            self._connected = True
            logger.info("sse_transport_connected", url=self.url)
        except Exception as e:
            logger.error("sse_transport_connect_failed", url=self.url, error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from the server."""
        self._connected = False

        if self._sse_task:
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass

        if self._client:
            await self._client.aclose()
            self._client = None

        logger.info("sse_transport_disconnected", url=self.url)

    async def send(self, message: MCPMessage) -> MCPMessage:
        """Send a request and wait for response."""
        if not self._client or not self._connected:
            raise RuntimeError("Not connected")

        # Assign message ID
        self._message_id += 1
        message.id = self._message_id

        # Create future for response
        response_future: asyncio.Future = asyncio.Future()
        self._pending_responses[message.id] = response_future

        try:
            # Send POST request
            payload = {
                "jsonrpc": message.jsonrpc,
                "id": message.id,
                "method": message.method,
                "params": message.params or {},
            }

            response = await self._client.post(
                f"{self.url}/message",
                json=payload,
            )
            response.raise_for_status()

            # For simple request-response, the result might be in the HTTP response
            if response.headers.get("content-type", "").startswith("application/json"):
                result = response.json()
                if "result" in result or "error" in result:
                    return MCPMessage(
                        jsonrpc=result.get("jsonrpc", "2.0"),
                        id=result.get("id"),
                        result=result.get("result"),
                        error=result.get("error"),
                    )

            # Otherwise, wait for SSE response
            return await asyncio.wait_for(response_future, timeout=self.timeout)

        finally:
            self._pending_responses.pop(message.id, None)

    async def _listen_sse(self) -> None:
        """Listen for SSE messages."""
        if not self._client:
            return

        try:
            async with self._client.stream("GET", f"{self.url}/sse") as response:
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue

                    data = line[5:].strip()
                    if not data:
                        continue

                    try:
                        message = json.loads(data)
                        await self._handle_sse_message(message)
                    except json.JSONDecodeError:
                        logger.warning("sse_invalid_json", data=data[:100])

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("sse_listener_error", error=str(e))
            self._connected = False

    async def _handle_sse_message(self, message: dict) -> None:
        """Handle an incoming SSE message."""
        msg_id = message.get("id")

        if msg_id and msg_id in self._pending_responses:
            # This is a response to a pending request
            future = self._pending_responses.pop(msg_id)
            if not future.done():
                future.set_result(MCPMessage(
                    jsonrpc=message.get("jsonrpc", "2.0"),
                    id=msg_id,
                    result=message.get("result"),
                    error=message.get("error"),
                ))
        else:
            # This is a notification
            logger.debug("sse_notification", method=message.get("method"))

    async def subscribe(self) -> AsyncIterator[MCPMessage]:
        """Subscribe to server notifications."""
        # The SSE listener handles notifications internally
        # This would be used for streaming responses
        while self._connected:
            await asyncio.sleep(0.1)
            yield MCPMessage()  # Placeholder


class StreamableHTTPTransport(Transport):
    """
    Streamable HTTP transport for MCP.

    Uses HTTP with streaming responses for efficient communication.
    This is the recommended transport for new deployments.
    """

    def __init__(
        self,
        url: str,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.headers = headers or {}
        self._client: httpx.AsyncClient | None = None
        self._message_id = 0
        self._connected = False
        self._session_id: str | None = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """Connect and initialize session."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                **self.headers,
                "Accept": "application/json, text/event-stream",
            },
        )

        # Initialize session
        init_message = MCPMessage(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "UCP", "version": "0.1.0"},
            },
        )

        response = await self.send(init_message)

        if response.error:
            raise RuntimeError(f"Initialize failed: {response.error}")

        self._connected = True
        logger.info("streamable_http_connected", url=self.url)

    async def disconnect(self) -> None:
        """Disconnect from the server."""
        self._connected = False

        if self._client:
            await self._client.aclose()
            self._client = None

        logger.info("streamable_http_disconnected", url=self.url)

    async def send(self, message: MCPMessage) -> MCPMessage:
        """Send a message using streamable HTTP."""
        if not self._client:
            raise RuntimeError("Not connected")

        self._message_id += 1
        message.id = self._message_id

        payload = {
            "jsonrpc": message.jsonrpc,
            "id": message.id,
            "method": message.method,
            "params": message.params or {},
        }

        response = await self._client.post(
            f"{self.url}/mcp",
            json=payload,
        )
        response.raise_for_status()

        result = response.json()

        return MCPMessage(
            jsonrpc=result.get("jsonrpc", "2.0"),
            id=result.get("id"),
            result=result.get("result"),
            error=result.get("error"),
        )

    async def subscribe(self) -> AsyncIterator[MCPMessage]:
        """Subscribe to server notifications via streaming."""
        if not self._client:
            return

        async with self._client.stream("GET", f"{self.url}/mcp/events") as response:
            async for line in response.aiter_lines():
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    yield MCPMessage(
                        jsonrpc=data.get("jsonrpc", "2.0"),
                        id=data.get("id"),
                        method=data.get("method"),
                        params=data.get("params"),
                        result=data.get("result"),
                        error=data.get("error"),
                    )
                except json.JSONDecodeError:
                    continue


def create_transport(
    transport_type: str,
    **kwargs: Any,
) -> Transport:
    """
    Factory function to create a transport instance.

    Args:
        transport_type: One of "sse", "streamable-http"
        **kwargs: Transport-specific configuration
    """
    if transport_type == "sse":
        return SSETransport(**kwargs)
    elif transport_type == "streamable-http":
        return StreamableHTTPTransport(**kwargs)
    else:
        raise ValueError(f"Unknown transport type: {transport_type}")
