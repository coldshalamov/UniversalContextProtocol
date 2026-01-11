"""
UCP Client - Interface to the Universal Context Protocol server.

Handles tool prediction requests and feedback submission
for the UCP router.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel, Field


class ToolPrediction(BaseModel):
    """A tool prediction from UCP."""
    
    tools: list[dict] = Field(description="Tool schemas to inject")
    reasoning: str | None = None
    scores: dict[str, float] = Field(default_factory=dict)
    query_used: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UCPClient:
    """Client for communicating with the UCP server."""
    
    def __init__(
        self,
        server_url: str = "http://localhost:8765",
        timeout: float = 30.0,
    ):
        self.server_url = server_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=timeout)
        self._connected = False
    
    async def connect(self) -> bool:
        """Test connection to UCP server."""
        try:
            response = await self.client.get(f"{self.server_url}/health")
            self._connected = response.status_code == 200
            return self._connected
        except Exception:
            self._connected = False
            return False
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def predict_tools(
        self,
        context: str,
        recent_tools: list[str] | None = None,
        max_tools: int = 5,
    ) -> ToolPrediction:
        """
        Get tool predictions from UCP based on conversation context.
        
        Args:
            context: Recent conversation context
            recent_tools: Tools used recently in this session
            max_tools: Maximum number of tools to return
        
        Returns:
            ToolPrediction with recommended tools
        """
        try:
            response = await self.client.post(
                f"{self.server_url}/predict",
                json={
                    "context": context,
                    "recent_tools": recent_tools or [],
                    "max_tools": max_tools,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            return ToolPrediction(
                tools=data.get("tools", []),
                reasoning=data.get("reasoning"),
                scores=data.get("scores", {}),
                query_used=data.get("query_used", context[:100]),
            )
        except Exception as e:
            # Return empty prediction on error
            return ToolPrediction(
                tools=[],
                reasoning=f"UCP unavailable: {e}",
            )
    
    async def report_usage(
        self,
        prediction: ToolPrediction,
        actually_used: list[str],
        success: bool = True,
    ) -> bool:
        """
        Report actual tool usage for learning feedback.
        
        Args:
            prediction: The original prediction from UCP
            actually_used: Tools that were actually used
            success: Whether the tool calls succeeded
        
        Returns:
            True if feedback was accepted
        """
        try:
            response = await self.client.post(
                f"{self.server_url}/feedback",
                json={
                    "predicted_tools": [t.get("name", t) for t in prediction.tools],
                    "actually_used": actually_used,
                    "success": success,
                    "query_used": prediction.query_used,
                    "timestamp": prediction.timestamp.isoformat(),
                },
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def get_available_tools(self) -> list[dict]:
        """Get all available tools from UCP."""
        try:
            response = await self.client.get(f"{self.server_url}/tools")
            response.raise_for_status()
            return response.json().get("tools", [])
        except Exception:
            return []
    
    async def search_tools(self, query: str, top_k: int = 10) -> list[dict]:
        """Search for tools by query."""
        try:
            response = await self.client.get(
                f"{self.server_url}/tools/search",
                params={"query": query, "top_k": top_k},
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except Exception:
            return []
    
    async def get_status(self) -> dict[str, Any]:
        """Get UCP server status."""
        try:
            response = await self.client.get(f"{self.server_url}/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}


class MockUCPClient(UCPClient):
    """Mock UCP client for testing without a server."""
    
    def __init__(self, *args: Any, **kwargs: Any):
        # Don't initialize real client
        self.server_url = kwargs.get("server_url", "http://localhost:8765")
        self._connected = True
        self._mock_tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read contents of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"}
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_code",
                    "description": "Execute Python code",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Python code to execute"}
                        },
                        "required": ["code"],
                    },
                },
            },
        ]
    
    async def connect(self) -> bool:
        return True
    
    async def close(self) -> None:
        pass
    
    async def predict_tools(
        self,
        context: str,
        recent_tools: list[str] | None = None,
        max_tools: int = 5,
    ) -> ToolPrediction:
        # Simple keyword-based mock prediction
        tools = []
        context_lower = context.lower()
        
        if any(kw in context_lower for kw in ["search", "find", "look up", "what is"]):
            tools.append(self._mock_tools[0])
        if any(kw in context_lower for kw in ["file", "read", "open", "content"]):
            tools.append(self._mock_tools[1])
        if any(kw in context_lower for kw in ["code", "python", "run", "execute", "calculate"]):
            tools.append(self._mock_tools[2])
        
        return ToolPrediction(
            tools=tools[:max_tools],
            reasoning="Mock prediction based on keywords",
            scores={t["function"]["name"]: 0.8 for t in tools},
            query_used=context[:100],
        )
    
    async def report_usage(
        self,
        prediction: ToolPrediction,
        actually_used: list[str],
        success: bool = True,
    ) -> bool:
        return True
    
    async def get_available_tools(self) -> list[dict]:
        return self._mock_tools
    
    async def search_tools(self, query: str, top_k: int = 10) -> list[dict]:
        return self._mock_tools[:top_k]
    
    async def get_status(self) -> dict[str, Any]:
        return {"status": "mock", "tools_available": len(self._mock_tools)}


def create_ucp_client(
    server_url: str = "http://localhost:8765",
    mock: bool = False,
) -> UCPClient:
    """Create a UCP client, optionally using mock for testing."""
    if mock:
        return MockUCPClient(server_url=server_url)
    return UCPClient(server_url=server_url)
