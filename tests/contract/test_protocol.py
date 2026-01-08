import pytest
import asyncio
import sys
import os
from ucp.server import UCPServer
from ucp.config import UCPConfig, DownstreamServerConfig, ToolZooConfig, RouterConfig, SessionConfig
from ucp.models import SessionState

# Ensure we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

@pytest.fixture
def mock_downstream_config():
    return DownstreamServerConfig(
        name="mock-server",
        transport="stdio",
        command=sys.executable,
        args=[os.path.abspath(os.path.join(os.path.dirname(__file__), "../mocks/mock_mcp_server.py"))],
        tags=["mock"],
        description="A mock MCP server for testing"
    )

@pytest.fixture
def ucp_config(mock_downstream_config):
    return UCPConfig(
        server={"name": "test-ucp", "transport": "stdio"},
        tool_zoo=ToolZooConfig(top_k=2, similarity_threshold=0.0, persist_directory=":memory:"), # Low k to test filtering
        router=RouterConfig(mode="keyword", max_tools=2), # Keyword mode for deterministic testing
        session=SessionConfig(persistence="memory"),
        downstream_servers=[mock_downstream_config]
    )

@pytest.fixture
async def ucp_server(ucp_config):
    server = UCPServer(ucp_config)
    await server.initialize()
    return server

@pytest.mark.asyncio
async def test_tools_list_protocol(ucp_server):
    """Verify tools/list returns valid MCP response and respects top_k."""
    
    # Update context to "prime" the router (keyword match 'echo')
    await ucp_server.update_context("I want to echo something")
    
    tools_response = await ucp_server.list_tools()
    
    assert "tools" in tools_response
    tools = tools_response["tools"]
    
    # Should be limited by top_k=2
    assert len(tools) <= 2
    
    # Should contain 'mock.echo' because of keyword match
    names = [t["name"] for t in tools]
    assert "mock.echo" in names

@pytest.mark.asyncio
async def test_tools_call_proxy(ucp_server):
    """Verify tools/call proxies to downstream server."""
    
    # Call the mock tool
    result = await ucp_server.call_tool("mock.echo", {"message": "hello world"})
    
    assert "content" in result
    assert result["content"][0]["text"] == "Executed mock.echo with {'message': 'hello world'}"

@pytest.mark.asyncio
async def test_tools_call_error_proxy(ucp_server):
    """Verify error propagation from downstream."""
    
    with pytest.raises(Exception) as excinfo:
        await ucp_server.call_tool("mock.fail", {})
    
    # The server implementation might raise an exception or return an error dict. 
    # Adjust assertion based on actual server.py implementation behavior.
    # Assuming it raises specific error or returns error structure.
    # For now, generic check.
    assert "failed" in str(excinfo.value) or "intentionally" in str(excinfo.value)

