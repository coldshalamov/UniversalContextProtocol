import pytest
import asyncio
import sys
import os
import tempfile
from ucp.server import UCPServer
from ucp.config import UCPConfig, DownstreamServerConfig, ToolZooConfig, RouterConfig, SessionConfig
from ucp.models import SessionState
from ucp.connection_pool import ConnectionPool

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
    temp_dir = tempfile.mkdtemp()
    return UCPConfig(
        server={"name": "test-ucp", "transport": "stdio"},
        tool_zoo=ToolZooConfig(top_k=2, similarity_threshold=0.0, persist_directory=temp_dir), # Low k to test filtering
        router=RouterConfig(mode="keyword", max_tools=2), # Keyword mode for deterministic testing
        session=SessionConfig(persistence="memory"),
        downstream_servers=[mock_downstream_config]
    )

@pytest.fixture
async def ucp_server(ucp_config):
    server = UCPServer(ucp_config)
    # FORCE EAGER CONNECTION POOL for tests
    server.connection_pool = ConnectionPool(ucp_config)
    await server.initialize()
    return server

@pytest.mark.asyncio
async def test_tools_list_protocol(ucp_server):
    """Verify tools/list returns valid MCP response and respects top_k."""
    
    # Update context to "prime" the router (keyword match 'echo')
    await ucp_server.update_context("I want to echo something")
    
    # We test the internal logic method
    tools = await ucp_server._list_tools()
    
    # Should be limited by top_k=2
    assert len(tools) <= 2
    
    # Should contain 'mock.echo' because of keyword match
    names = [t.name for t in tools]
    assert "mock.echo" in names

@pytest.mark.asyncio
async def test_tools_call_proxy(ucp_server):
    """Verify tools/call proxies to downstream server."""
    
    # Call the mock tool
    result_obj = await ucp_server._call_tool("mock.echo", {"message": "hello world"})
    
    assert result_obj.success is True
    # The result content structure depends on how downstream returns it.
    # The mock server returns {"content": [{"type": "text", "text": "..."}]}
    # ConnectionPool returns the 'result' part of JSON-RPC response.
    # So result_obj.result should contain 'content'
    
    assert "content" in result_obj.result
    assert result_obj.result["content"][0]["text"] == "Executed mock.echo with {'message': 'hello world'}"

@pytest.mark.asyncio
async def test_tools_call_error_proxy(ucp_server):
    """Verify error propagation from downstream."""
    
    # _call_tool returns a ToolCallResult with success=False on error, it does not raise usually, 
    # unless connection fails.
    # But let's check the implementation. It catches Exception and returns success=False.
    
    result_obj = await ucp_server._call_tool("mock.fail", {})
    
    assert result_obj.success is False
    assert "failed" in result_obj.error or "intentionally" in result_obj.error

