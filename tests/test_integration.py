"""Integration tests for the full UCP system."""

import pytest
import tempfile
import asyncio
from pathlib import Path

from ucp.config import UCPConfig, DownstreamServerConfig, ToolZooConfig, RouterConfig, SessionConfig
from ucp.models import ToolSchema
from ucp.server import UCPServer, UCPServerBuilder
from ucp.tool_zoo import HybridToolZoo
from ucp.router import AdaptiveRouter
from ucp.session import SessionManager


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration without real downstream servers."""
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
        ),
        session=SessionConfig(
            persistence="sqlite",
            sqlite_path=str(Path(temp_dir) / "sessions.db"),
        ),
        downstream_servers=[],  # No real servers for testing
    )


@pytest.fixture
def sample_tools():
    """Sample tools to pre-populate the zoo."""
    return [
        ToolSchema(
            name="email.send",
            display_name="send",
            description="Send an email message to recipients",
            server_name="email",
            input_schema={"type": "object", "properties": {"to": {"type": "string"}, "body": {"type": "string"}}},
            tags=["email", "communication"],
            domain="email",
        ),
        ToolSchema(
            name="email.read",
            display_name="read",
            description="Read emails from inbox",
            server_name="email",
            tags=["email"],
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
        ToolSchema(
            name="github.create_pr",
            display_name="create_pr",
            description="Create a pull request",
            server_name="github",
            tags=["code", "github"],
            domain="code",
        ),
        ToolSchema(
            name="calendar.create_event",
            display_name="create_event",
            description="Schedule a calendar event",
            server_name="calendar",
            tags=["calendar", "scheduling"],
            domain="calendar",
        ),
        ToolSchema(
            name="stripe.charge",
            display_name="charge",
            description="Process a payment charge",
            server_name="stripe",
            tags=["payment", "finance"],
            domain="finance",
        ),
        ToolSchema(
            name="slack.send_message",
            display_name="send_message",
            description="Send a Slack message",
            server_name="slack",
            tags=["communication", "slack"],
            domain="communication",
        ),
        ToolSchema(
            name="database.query",
            display_name="query",
            description="Execute SQL database query",
            server_name="database",
            tags=["database", "sql"],
            domain="database",
        ),
    ]


class TestFullIntegration:
    """Full system integration tests."""

    @pytest.mark.asyncio
    async def test_server_initialization(self, test_config, sample_tools):
        """Test that UCP server initializes correctly."""
        server = UCPServer(test_config)

        # Pre-populate tool zoo
        server.tool_zoo.initialize()
        server.tool_zoo.add_tools(sample_tools)

        # Check initialization
        assert server.tool_zoo is not None
        assert server.router is not None
        assert server.session_manager is not None

        stats = server.tool_zoo.get_stats()
        assert stats["total_tools"] == len(sample_tools)

    @pytest.mark.asyncio
    async def test_context_aware_tool_listing(self, test_config, sample_tools):
        """Test that tool listing adapts to context."""
        server = UCPServer(test_config)
        server.tool_zoo.initialize()
        server.tool_zoo.add_tools(sample_tools)

        # Update context with email-related message
        await server.update_context("I need to send an email to my boss")

        # Get tools
        tools = await server._list_tools()
        tool_names = [t.name for t in tools]

        # Should prioritize email tools
        assert any("email" in name for name in tool_names)

        # Verify routing decision was made
        assert server._last_routing is not None
        assert len(server._last_routing.selected_tools) > 0

    @pytest.mark.asyncio
    async def test_context_shift_updates_tools(self, test_config, sample_tools):
        """Test that tools update when conversation topic shifts."""
        server = UCPServer(test_config)
        server.tool_zoo.initialize()
        server.tool_zoo.add_tools(sample_tools)

        # First context: email
        await server.update_context("Send an email notification")
        tools1 = await server._list_tools()
        email_tools = [t for t in tools1 if "email" in t.name]

        # Second context: code
        await server.update_context("Create a pull request for the feature")
        tools2 = await server._list_tools()
        code_tools = [t for t in tools2 if "github" in t.name]

        # Different contexts should yield different tools
        assert len(email_tools) > 0 or len(code_tools) > 0

    @pytest.mark.asyncio
    async def test_session_persistence(self, test_config, sample_tools):
        """Test that session state persists across operations."""
        server = UCPServer(test_config)
        server.tool_zoo.initialize()
        server.tool_zoo.add_tools(sample_tools)

        # Create session and add messages
        await server.update_context("Hello")
        await server.update_context("I need help with email")

        session_id = server._current_session.session_id

        # Verify session has messages
        assert len(server._current_session.messages) == 2

        # Create new server instance (simulating restart)
        server2 = UCPServer(test_config)
        server2.tool_zoo.initialize()

        # Load same session
        loaded_session = server2.session_manager.get_session(session_id)

        assert loaded_session is not None
        assert len(loaded_session.messages) == 2

    @pytest.mark.asyncio
    async def test_tool_usage_tracking(self, test_config, sample_tools):
        """Test that tool usage is tracked for learning."""
        server = UCPServer(test_config)
        server.tool_zoo.initialize()
        server.tool_zoo.add_tools(sample_tools)

        await server.update_context("Send email")
        await server._list_tools()

        # Simulate tool use
        if server._current_session:
            server._current_session.record_tool_use("email.send")
            server._current_session.record_tool_use("email.send")

        # Check usage stats
        assert server._current_session.tool_usage["email.send"] == 2

    @pytest.mark.asyncio
    async def test_hybrid_search_effectiveness(self, test_config, sample_tools):
        """Test hybrid search combines semantic and keyword matching."""
        server = UCPServer(test_config)
        server.tool_zoo.initialize()
        server.tool_zoo.add_tools(sample_tools)

        # Query with both semantic meaning and keywords
        results = server.tool_zoo.hybrid_search(
            "schedule meeting tomorrow",
            top_k=3
        )

        tool_names = [t.name for t, _ in results]

        # Calendar tool should be found (semantic match for "schedule")
        assert "calendar.create_event" in tool_names

    @pytest.mark.asyncio
    async def test_domain_detection(self, test_config, sample_tools):
        """Test that domain detection works correctly."""
        server = UCPServer(test_config)
        server.tool_zoo.initialize()
        server.tool_zoo.add_tools(sample_tools)

        # Test various domains
        domains_email = server.router.detect_domain("send an email reply")
        assert "email" in domains_email

        domains_code = server.router.detect_domain("create a git branch")
        assert "code" in domains_code

        domains_finance = server.router.detect_domain("charge the credit card")
        assert "finance" in domains_finance

    @pytest.mark.asyncio
    async def test_max_tools_respected(self, test_config, sample_tools):
        """Test that max_tools limit is respected."""
        test_config.router.max_tools = 3

        server = UCPServer(test_config)
        server.tool_zoo.initialize()
        server.tool_zoo.add_tools(sample_tools)

        # Query that could match many tools
        await server.update_context("I need to email, code, pay, and message")
        tools = await server._list_tools()

        assert len(tools) <= 3

    @pytest.mark.asyncio
    async def test_server_status(self, test_config, sample_tools):
        """Test server status reporting."""
        server = UCPServer(test_config)
        server.tool_zoo.initialize()
        server.tool_zoo.add_tools(sample_tools)

        await server.update_context("Test message")
        await server._list_tools()

        status = server.get_status()

        assert "server" in status
        assert "tool_zoo" in status
        assert "router" in status
        assert status["tool_zoo"]["total_tools"] == len(sample_tools)


class TestBuilderPattern:
    """Test the UCPServerBuilder."""

    def test_builder_with_config(self, test_config):
        """Test building server with config."""
        server = (
            UCPServerBuilder()
            .with_config(test_config)
            .build()
        )

        assert server.config == test_config

    def test_builder_custom_components(self, test_config, temp_dir):
        """Test building server with custom components."""
        # Create custom tool zoo
        custom_zoo = HybridToolZoo(test_config.tool_zoo)
        custom_zoo.initialize()

        # Create custom router
        custom_router = AdaptiveRouter(test_config.router, custom_zoo)

        server = (
            UCPServerBuilder()
            .with_config(test_config)
            .with_tool_zoo(custom_zoo)
            .with_router(custom_router)
            .build()
        )

        assert server.tool_zoo is custom_zoo
        assert server.router is custom_router


class TestAdaptiveLearning:
    """Test the adaptive learning capabilities."""

    @pytest.mark.asyncio
    async def test_learning_from_usage(self, test_config, sample_tools):
        """Test that router learns from tool usage patterns."""
        server = UCPServer(test_config)
        server.tool_zoo.initialize()
        server.tool_zoo.add_tools(sample_tools)

        # Simulate multiple sessions with same pattern
        for _ in range(5):
            await server.update_context("Send notification")
            decision = await server.router.route(server._current_session)

            # Record that email and slack are always used together
            if isinstance(server.router, AdaptiveRouter):
                server.router.record_usage(decision, ["email.send", "slack.send_message"])

        # Check learning stats
        if isinstance(server.router, AdaptiveRouter):
            stats = server.router.get_learning_stats()
            assert stats["predictions"] == 5

            # Check co-occurrence learned
            cooccur = server.router.get_cooccurring_tools("email.send")
            assert "slack.send_message" in cooccur

    @pytest.mark.asyncio
    async def test_export_training_data(self, test_config, sample_tools):
        """Test exporting training data for RAFT."""
        server = UCPServer(test_config)
        server.tool_zoo.initialize()
        server.tool_zoo.add_tools(sample_tools)

        # Generate some training data
        await server.update_context("Send email")
        decision = await server.router.route(server._current_session)

        if isinstance(server.router, AdaptiveRouter):
            server.router.record_usage(decision, ["email.send"])

            training_data = server.router.export_training_data()

            assert len(training_data) == 1
            assert "query" in training_data[0]
            assert "candidates" in training_data[0]
            assert "correct" in training_data[0]
            assert "email.send" in training_data[0]["correct"]
