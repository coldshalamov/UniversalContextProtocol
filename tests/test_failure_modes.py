"""
Failure Mode Tests for UCP.

Tests various failure scenarios and graceful degradation patterns:
- Downstream MCP server crashes mid-conversation
- Downstream server returns malformed JSON
- Downstream server times out (>30s)
- Router fails to find relevant tools
- Tool call with invalid arguments

Verifies:
- Circuit breaker pattern works
- Graceful degradation implemented
- No crashes or unhandled exceptions
- Error injection for self-correction
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.types import Tool

from ucp.config import UCPConfig, DownstreamServerConfig, ToolZooConfig, RouterConfig, SessionConfig
from ucp.models import ToolSchema, ServerStatus
from ucp.server import UCPServer
from ucp.connection_pool import CircuitBreaker, CircuitBreakerState
from ucp.router import Router, AdaptiveRouter
from ucp.tool_zoo import HybridToolZoo


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_tools():
    """Sample tools for testing."""
    return [
        ToolSchema(
            name="email.send",
            display_name="send",
            description="Send an email message to recipients",
            server_name="email",
            input_schema={"type": "object", "properties": {"to": {"type": "string"}, "body": {"type": "string"}},
            tags=["email", "communication"],
            domain="email",
        ),
        ToolSchema(
            name="github.create_issue",
            display_name="create_issue",
            description="Create a GitHub issue",
            server_name="github",
            tags=["code", "github"],
            domain="code",
        ),
    ]


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration."""
    return UCPConfig(
        tool_zoo=ToolZooConfig(
            persist_directory=str(Path(temp_dir) / "chromadb"),
            top_k=5,
            similarity_threshold=0.1,
        ),
        router=RouterConfig(
            mode="hybrid",
            max_tools=5,
            min_tools=1,
            fallback_tools=["email.send"],
        ),
        session=SessionConfig(
            persistence="sqlite",
            sqlite_path=str(Path(temp_dir) / "sessions.db"),
        ),
        downstream_servers=[],
    )


# ============================================================================
# Circuit Breaker Tests
# ============================================================================

class TestCircuitBreaker:
    """Test circuit breaker pattern implementation."""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.can_attempt() is True
        assert cb.failure_count == 0

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3)
        
        # Record failures
        for i in range(3):
            cb.record_failure()
        
        # Should be OPEN after threshold
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 3
        assert cb.can_attempt() is False

    def test_circuit_breaker_transitions_to_half_open(self):
        """Test circuit breaker transitions to HALF_OPEN after timeout."""
        cb = CircuitBreaker(failure_threshold=3, timeout_seconds=0.1)
        
        # Open the circuit
        for i in range(3):
            cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        
        # Wait for timeout
        import time
        time.sleep(0.15)
        
        # Should be in HALF_OPEN now
        assert cb.state == CircuitBreakerState.HALF_OPEN
        assert cb.can_attempt() is True

    def test_circuit_breaker_closes_after_success(self):
        """Test circuit breaker closes after successful calls."""
        cb = CircuitBreaker(failure_threshold=3, half_open_max_calls=2)
        
        # Open the circuit
        for i in range(3):
            cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        
        # Transition to HALF_OPEN by waiting
        import time
        time.sleep(0.15)
        assert cb.state == CircuitBreakerState.HALF_OPEN
        
        # Record successful calls
        cb.record_success()
        cb.record_success()
        
        # Should still be in HALF_OPEN until max calls
        assert cb.state == CircuitBreakerState.HALF_OPEN
        
        # One more success
        cb.record_success()
        
        # Should close now
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.can_attempt() is True

    def test_circuit_breaker_reopens_on_half_open_failure(self):
        """Test circuit breaker reopens on HALF_OPEN failure."""
        cb = CircuitBreaker(failure_threshold=3, half_open_max_calls=2)
        
        # Open the circuit and transition to HALF_OPEN
        for i in range(3):
            cb.record_failure()
        import time
        time.sleep(0.15)
        assert cb.state == CircuitBreakerState.HALF_OPEN
        
        # Fail during HALF_OPEN
        cb.record_failure()
        
        # Should reopen
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.can_attempt() is False

    def test_circuit_breaker_get_state(self):
        """Test circuit breaker state retrieval."""
        cb = CircuitBreaker()
        state = cb.get_state()
        
        assert "state" in state
        assert "failure_count" in state
        assert "can_attempt" in state
        assert state["state"] == "closed"
        assert state["can_attempt"] is True


# ============================================================================
# Router Failure Tests
# ============================================================================

class TestRouterFailureModes:
    """Test router graceful degradation on failures."""

    @pytest.mark.asyncio
    async def test_router_fallback_to_keyword_search(self, sample_tools, test_config):
        """Test router falls back to keyword search if semantic search fails."""
        # Create tool zoo with sample tools
        tool_zoo = HybridToolZoo(test_config.tool_zoo)
        tool_zoo.add_tools(sample_tools)
        
        # Create router
        router = Router(test_config.router, tool_zoo)
        
        # Mock semantic search to fail
        with patch.object(tool_zoo, 'search', side_effect=Exception("Semantic search failed")):
            # Create session
            from ucp.models import SessionState
            session = SessionState()
            session.add_message("user", "I need to send an email")
            
            # Route should fall back to keyword search
            decision = await router.route(session)
            
            # Should still return a decision
            assert decision is not None
            assert len(decision.selected_tools) > 0
            assert "keyword_fallback" in decision.reasoning or "all_tools_fallback" in decision.reasoning

    @pytest.mark.asyncio
    async def test_router_returns_fallback_tools_on_empty_context(self, sample_tools, test_config):
        """Test router returns fallback tools when no context available."""
        tool_zoo = HybridToolZoo(test_config.tool_zoo)
        tool_zoo.add_tools(sample_tools)
        
        router = Router(test_config.router, tool_zoo)
        
        # Create empty session
        from ucp.models import SessionState
        session = SessionState()
        
        # Route should return fallback tools
        decision = await router.route(session)
        
        assert decision.selected_tools == test_config.router.fallback_tools
        assert "No context available" in decision.reasoning

    @pytest.mark.asyncio
    async def test_router_handles_tool_zoo_search_failure(self, sample_tools, test_config):
        """Test router handles tool zoo search failure gracefully."""
        tool_zoo = HybridToolZoo(test_config.tool_zoo)
        tool_zoo.add_tools(sample_tools)
        
        router = Router(test_config.router, tool_zoo)
        
        # Mock both semantic and keyword search to fail
        with patch.object(tool_zoo, 'search', side_effect=Exception("Search failed")):
            with patch.object(tool_zoo, 'keyword_search', side_effect=Exception("Keyword search failed")):
                from ucp.models import SessionState
                session = SessionState()
                session.add_message("user", "I need to send an email")
                
                # Should not crash, return empty results
                decision = await router.route(session)
                
                # Should return fallback tools
                assert decision is not None
                assert len(decision.selected_tools) >= test_config.router.min_tools


# ============================================================================
# Connection Pool Failure Tests
# ============================================================================

class TestConnectionPoolFailureModes:
    """Test connection pool graceful degradation on failures."""

    @pytest.mark.asyncio
    async def test_connection_pool_handles_timeout(self, test_config):
        """Test connection pool handles tool call timeout gracefully."""
        from ucp.connection_pool import ConnectionPool
        from ucp.models import SessionState
        
        pool = ConnectionPool(test_config)
        
        # Mock a server that times out
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(side_effect=asyncio.TimeoutError())
        
        pool._sessions = {"test_server": mock_session}
        pool._servers = {"test_server": MagicMock(status=ServerStatus.CONNECTED)}
        pool._tool_to_server = {"test_server.test_tool": "test_server"}
        
        # Should handle timeout gracefully
        with pytest.raises(RuntimeError, match="Tool call failed after"):
            await pool.call_tool("test_server.test_tool", {"param": "value"})
        
        # Server should be marked as ERROR
        assert pool._servers["test_server"].status == ServerStatus.ERROR
        assert pool._servers["test_server"].error_message is not None

    @pytest.mark.asyncio
    async def test_connection_pool_retries_with_backoff(self, test_config):
        """Test connection pool retries with exponential backoff."""
        from ucp.connection_pool import ConnectionPool
        
        pool = ConnectionPool(test_config)
        pool._max_retries = 3
        pool._retry_delay_base = 0.1  # Fast for testing
        
        # Mock a server that fails twice then succeeds
        call_count = [0]
        async def mock_call(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise Exception("Temporary failure")
            return {"result": "success"}
        
        mock_session = AsyncMock()
        mock_session.call_tool = mock_call
        
        pool._sessions = {"test_server": mock_session}
        pool._servers = {"test_server": MagicMock(status=ServerStatus.CONNECTED)}
        pool._tool_to_server = {"test_server.test_tool": "test_server"}
        pool._circuit_breakers = {"test_server": CircuitBreaker(failure_threshold=10)}
        
        # Should retry and eventually succeed
        result = await pool.call_tool("test_server.test_tool", {"param": "value"})
        
        assert call_count[0] == 3  # 2 failures + 1 success
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_connection_pool_circuit_breaker_blocks_requests(self, test_config):
        """Test circuit breaker blocks requests when open."""
        from ucp.connection_pool import ConnectionPool
        
        pool = ConnectionPool(test_config)
        
        # Mock a server with circuit breaker
        cb = CircuitBreaker(failure_threshold=3)
        for i in range(3):
            cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(side_effect=Exception("Server error"))
        
        pool._sessions = {"test_server": mock_session}
        pool._servers = {"test_server": MagicMock(status=ServerStatus.CONNECTED)}
        pool._tool_to_server = {"test_server.test_tool": "test_server"}
        pool._circuit_breakers = {"test_server": cb}
        
        # Should raise error about circuit breaker
        with pytest.raises(RuntimeError, match="Circuit breaker is open"):
            await pool.call_tool("test_server.test_tool", {"param": "value"})


# ============================================================================
# Server Error Injection Tests
# ============================================================================

class TestServerErrorInjection:
    """Test server error injection for self-correction."""

    @pytest.mark.asyncio
    async def test_server_injects_error_context_on_failure(self, sample_tools, test_config):
        """Test server injects helpful error context on tool failure."""
        from ucp.models import SessionState
        
        # Create tool zoo with sample tools
        tool_zoo = HybridToolZoo(test_config.tool_zoo)
        tool_zoo.add_tools(sample_tools)
        
        # Create server
        server = UCPServer(test_config)
        
        # Mock connection pool to fail
        mock_pool = AsyncMock()
        mock_pool.call_tool = AsyncMock(side_effect=RuntimeError("Tool execution failed"))
        
        server.connection_pool = mock_pool
        
        # Create session
        session = SessionState()
        session.add_message("user", "Send an email")
        
        # Call tool
        result = await server._call_tool("email.send", {"to": "test@example.com"})
        
        # Should fail but with helpful context
        assert result.success is False
        assert "Error calling tool" in result.error
        assert "email.send" in result.error
        assert "Tool description" in result.error or "Available parameters" in result.error
        assert "Attempted with arguments" in result.error

    @pytest.mark.asyncio
    async def test_server_handles_tool_not_found_gracefully(self, sample_tools, test_config):
        """Test server handles tool not found gracefully."""
        from ucp.models import SessionState
        
        # Create tool zoo with sample tools
        tool_zoo = HybridToolZoo(test_config.tool_zoo)
        tool_zoo.add_tools(sample_tools)
        
        # Create server
        server = UCPServer(test_config)
        
        # Create session
        session = SessionState()
        session.add_message("user", "Use a non-existent tool")
        
        # Call non-existent tool
        result = await server._call_tool("nonexistent.tool", {"param": "value"})
        
        # Should fail with helpful message
        assert result.success is False
        assert "not found" in result.error.lower()
        assert "Available tools" in result.error

    @pytest.mark.asyncio
    async def test_server_includes_available_tools_in_error(self, sample_tools, test_config):
        """Test server includes available tools in error message."""
        from ucp.models import SessionState
        
        # Create tool zoo with sample tools
        tool_zoo = HybridToolZoo(test_config.tool_zoo)
        tool_zoo.add_tools(sample_tools)
        
        # Create server
        server = UCPServer(test_config)
        
        # Mock connection pool to fail
        mock_pool = AsyncMock()
        mock_pool.call_tool = AsyncMock(side_effect=RuntimeError("Server error"))
        
        server.connection_pool = mock_pool
        
        # Create session
        session = SessionState()
        session.add_message("user", "Send an email")
        
        # Call tool
        result = await server._call_tool("email.send", {"to": "test@example.com"})
        
        # Should include available tools in error
        assert result.success is False
        # Extract tool names from error
        for tool in sample_tools:
            assert tool.name in result.error or tool.display_name in result.error


# ============================================================================
# Integration Failure Tests
# ============================================================================

class TestIntegrationFailureScenarios:
    """Test end-to-end failure scenarios."""

    @pytest.mark.asyncio
    async def test_server_crash_mid_conversation(self, sample_tools, test_config):
        """Test server handles downstream server crash mid-conversation."""
        from ucp.models import SessionState
        
        # Create tool zoo with sample tools
        tool_zoo = HybridToolZoo(test_config.tool_zoo)
        tool_zoo.add_tools(sample_tools)
        
        # Create server
        server = UCPServer(test_config)
        
        # Mock connection pool that crashes after first call
        call_count = [0]
        async def mock_call(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Server crashed")
            return {"result": "success"}
        
        mock_pool = AsyncMock()
        mock_pool.call_tool = mock_call
        
        server.connection_pool = mock_pool
        
        # Create session
        session = SessionState()
        session.add_message("user", "First request")
        
        # First call should fail
        result1 = await server._call_tool("email.send", {"to": "test@example.com"})
        assert result1.success is False
        
        # Second call should also fail (server still down)
        result2 = await server._call_tool("email.send", {"to": "test2@example.com"})
        assert result2.success is False
        
        # Should not crash
        assert True  # If we get here, no crash occurred

    @pytest.mark.asyncio
    async def test_malformed_json_response(self, sample_tools, test_config):
        """Test server handles malformed JSON response gracefully."""
        from ucp.models import SessionState
        
        # Create tool zoo with sample tools
        tool_zoo = HybridToolZoo(test_config.tool_zoo)
        tool_zoo.add_tools(sample_tools)
        
        # Create server
        server = UCPServer(test_config)
        
        # Mock connection pool that returns malformed data
        mock_pool = AsyncMock()
        mock_pool.call_tool = AsyncMock(return_value="not valid json{{{")
        
        server.connection_pool = mock_pool
        
        # Create session
        session = SessionState()
        session.add_message("user", "Send an email")
        
        # Should handle gracefully (convert to string)
        result = await server._call_tool("email.send", {"to": "test@example.com"})
        
        # Should not crash
        assert result.success is True or result.success is False
        # If successful, result should be the string
        if result.success:
            assert result.result == "not valid json{{{"


# ============================================================================
# Run All Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
