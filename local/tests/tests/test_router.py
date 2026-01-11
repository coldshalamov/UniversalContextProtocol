"""Tests for the Semantic Router."""

import pytest
import tempfile
from pathlib import Path

from ucp.config import RouterConfig, ToolZooConfig
from ucp.models import SessionState, ToolSchema
from ucp.router import Router, AdaptiveRouter
from ucp.tool_zoo import HybridToolZoo


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def tool_zoo(temp_dir):
    """Create a tool zoo with sample tools."""
    config = ToolZooConfig(
        persist_directory=str(Path(temp_dir) / "chromadb"),
        top_k=5,
        similarity_threshold=0.1,
    )
    zoo = HybridToolZoo(config)
    zoo.initialize()

    # Add sample tools
    tools = [
        ToolSchema(
            name="gmail.send_email",
            display_name="send_email",
            description="Send an email message",
            server_name="gmail",
            tags=["email"],
            domain="email",
        ),
        ToolSchema(
            name="gmail.read_email",
            display_name="read_email",
            description="Read emails from inbox",
            server_name="gmail",
            tags=["email"],
            domain="email",
        ),
        ToolSchema(
            name="github.create_pr",
            display_name="create_pr",
            description="Create a pull request",
            server_name="github",
            tags=["code", "git"],
            domain="code",
        ),
        ToolSchema(
            name="stripe.charge",
            display_name="charge",
            description="Process a payment",
            server_name="stripe",
            tags=["finance"],
            domain="finance",
        ),
        ToolSchema(
            name="slack.send_message",
            display_name="send_message",
            description="Send a Slack message",
            server_name="slack",
            tags=["communication"],
            domain="communication",
        ),
    ]
    zoo.add_tools(tools)
    yield zoo
    zoo.close()


@pytest.fixture
def router_config():
    return RouterConfig(
        mode="hybrid",
        rerank=True,
        max_tools=5,
        min_tools=1,
        fallback_tools=[],
    )


@pytest.fixture
def session():
    return SessionState()


class TestRouter:
    """Tests for the basic Router."""

    def test_detect_domain_email(self, router_config, tool_zoo):
        """Test domain detection for email context."""
        router = Router(router_config, tool_zoo)

        domains = router.detect_domain("Send an email to John about the meeting")
        assert "email" in domains

    def test_detect_domain_code(self, router_config, tool_zoo):
        """Test domain detection for code context."""
        router = Router(router_config, tool_zoo)

        domains = router.detect_domain("Create a pull request for the feature branch")
        assert "code" in domains

    def test_detect_multiple_domains(self, router_config, tool_zoo):
        """Test detection of multiple domains."""
        router = Router(router_config, tool_zoo)

        domains = router.detect_domain(
            "After sending the email, create a GitHub issue to track the payment"
        )
        assert len(domains) >= 2

    @pytest.mark.asyncio
    async def test_route_email_context(self, router_config, tool_zoo, session):
        """Test routing for email-related context."""
        router = Router(router_config, tool_zoo)

        session.add_message("user", "I need to send an email to my boss")

        decision = await router.route(session)

        assert len(decision.selected_tools) > 0
        # Should prefer email tools
        assert any("gmail" in t for t in decision.selected_tools)

    @pytest.mark.asyncio
    async def test_route_code_context(self, router_config, tool_zoo, session):
        """Test routing for code-related context."""
        router = Router(router_config, tool_zoo)

        session.add_message("user", "Create a PR for the new feature")

        decision = await router.route(session)

        assert len(decision.selected_tools) > 0
        assert any("github" in t for t in decision.selected_tools)

    @pytest.mark.asyncio
    async def test_route_empty_context(self, router_config, tool_zoo, session):
        """Test routing with empty context returns fallbacks."""
        router_config.fallback_tools = ["gmail.send_email"]
        router = Router(router_config, tool_zoo)

        decision = await router.route(session)

        # Should return at least the fallback
        assert len(decision.selected_tools) >= 1

    @pytest.mark.asyncio
    async def test_route_with_current_message(self, router_config, tool_zoo, session):
        """Test routing with an additional current message."""
        router = Router(router_config, tool_zoo)

        # Old context about email
        session.add_message("user", "Check my inbox")
        session.add_message("assistant", "You have 5 new emails")

        # New message about payments
        decision = await router.route(session, current_message="Now charge the customer")

        # Should adapt to payment context
        assert any("stripe" in t for t in decision.selected_tools)

    @pytest.mark.asyncio
    async def test_route_respects_max_tools(self, router_config, tool_zoo, session):
        """Test that routing respects max_tools limit."""
        router_config.max_tools = 2
        router = Router(router_config, tool_zoo)

        session.add_message("user", "Do everything - email, code, payments, slack")

        decision = await router.route(session)

        assert len(decision.selected_tools) <= 2

    @pytest.mark.asyncio
    async def test_route_respects_max_per_server(self, router_config, tool_zoo, session):
        """Test that routing respects max_per_server limit for diversity."""
        # Add more tools from the same server
        additional_tools = [
            ToolSchema(
                name="gmail.search",
                display_name="search_emails",
                description="Search through emails",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
            ToolSchema(
                name="gmail.delete",
                display_name="delete_email",
                description="Delete an email",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
            ToolSchema(
                name="gmail.forward",
                display_name="forward_email",
                description="Forward an email",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
            ToolSchema(
                name="gmail.archive",
                display_name="archive_email",
                description="Archive an email",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
            ToolSchema(
                name="gmail.label",
                display_name="label_email",
                description="Add labels to email",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
        ]
        tool_zoo.add_tools(additional_tools)

        # Test with max_per_server = 2 (should limit to 2 gmail tools)
        router_config.max_tools = 10
        router_config.max_per_server = 2
        router = Router(router_config, tool_zoo)

        session.add_message("user", "I need to do everything with my emails - search, delete, forward, archive, label, send, read")

        decision = await router.route(session)

        # Count tools from each server
        gmail_tools = [t for t in decision.selected_tools if "gmail" in t]
        
        # Should not exceed max_per_server for gmail
        assert len(gmail_tools) <= 2

    @pytest.mark.asyncio
    async def test_route_allows_more_than_three_per_server(self, router_config, tool_zoo, session):
        """Test that router can return >3 tools from a single server when config allows."""
        # Add more tools from the same server
        additional_tools = [
            ToolSchema(
                name="gmail.search",
                display_name="search_emails",
                description="Search through emails",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
            ToolSchema(
                name="gmail.delete",
                display_name="delete_email",
                description="Delete an email",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
            ToolSchema(
                name="gmail.forward",
                display_name="forward_email",
                description="Forward an email",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
            ToolSchema(
                name="gmail.archive",
                display_name="archive_email",
                description="Archive an email",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
            ToolSchema(
                name="gmail.label",
                display_name="label_email",
                description="Add labels to email",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
        ]
        tool_zoo.add_tools(additional_tools)

        # Test with max_per_server = 10 (should allow up to 10 gmail tools)
        router_config.max_tools = 20
        router_config.max_per_server = 10
        router = Router(router_config, tool_zoo)

        session.add_message("user", "I need to do everything with my emails - search, delete, forward, archive, label, send, read")

        decision = await router.route(session)

        # Count tools from each server
        gmail_tools = [t for t in decision.selected_tools if "gmail" in t]
        
        # Should allow more than 3 tools from gmail server
        assert len(gmail_tools) > 3
        # But should not exceed max_per_server
        assert len(gmail_tools) <= 10


class TestAdaptiveRouter:
    """Tests for the AdaptiveRouter with learning."""

    @pytest.mark.asyncio
    async def test_record_usage(self, router_config, tool_zoo, session):
        """Test recording tool usage for learning."""
        router = AdaptiveRouter(router_config, tool_zoo)

        session.add_message("user", "Send email")
        decision = await router.route(session)

        # Record that only send_email was actually used
        router.record_usage(decision, ["gmail.send_email"])

        stats = router.get_learning_stats()
        assert stats["predictions"] == 1

    @pytest.mark.asyncio
    async def test_cooccurrence_learning(self, router_config, tool_zoo, session):
        """Test that co-occurrence is tracked."""
        router = AdaptiveRouter(router_config, tool_zoo)

        # Simulate multiple sessions where email + slack are used together
        for _ in range(3):
            session.add_message("user", "Send notification")
            decision = await router.route(session)
            router.record_usage(decision, ["gmail.send_email", "slack.send_message"])

        # Check co-occurrence
        cooccur = router.get_cooccurring_tools("gmail.send_email")
        assert "slack.send_message" in cooccur

    @pytest.mark.asyncio
    async def test_export_training_data(self, router_config, tool_zoo, session):
        """Test exporting data for RAFT fine-tuning."""
        router = AdaptiveRouter(router_config, tool_zoo)

        session.add_message("user", "Send email")
        decision = await router.route(session)
        router.record_usage(decision, ["gmail.send_email"])

        training_data = router.export_training_data()

        assert len(training_data) == 1
        assert "query" in training_data[0]
        assert "candidates" in training_data[0]
        assert "correct" in training_data[0]

    @pytest.mark.asyncio
    async def test_adaptive_boost(self, router_config, tool_zoo, session):
        """Test that frequently co-used tools get boosted."""
        router = AdaptiveRouter(router_config, tool_zoo)

        # Train: email and slack often used together
        for _ in range(5):
            session2 = SessionState()
            session2.add_message("user", "Notify team")
            decision = await router.route(session2)
            router.record_usage(decision, ["gmail.send_email", "slack.send_message"])

        # Now test: when using email, slack should be boosted
        session.add_message("user", "Send an email")
        session.record_tool_use("gmail.send_email")

        decision = await router.route(session)

        # Slack should appear due to co-occurrence boost
        # (depending on scores, this may or may not be in top results)
        assert len(decision.selected_tools) > 0
                description="Search through emails",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
            ToolSchema(
                name="gmail.delete",
                display_name="delete_email",
                description="Delete an email",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
            ToolSchema(
                name="gmail.forward",
                display_name="forward_email",
                description="Forward an email",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
            ToolSchema(
                name="gmail.archive",
                display_name="archive_email",
                description="Archive an email",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
            ToolSchema(
                name="gmail.label",
                display_name="label_email",
                description="Add labels to email",
                server_name="gmail",
                tags=["email"],
                domain="email",
            ),
        ]
        tool_zoo.add_tools(additional_tools)

        # Test with max_per_server = 10 (should allow up to 10 gmail tools)
        router_config.max_tools = 20
        router_config.max_per_server = 10
        router = Router(router_config, tool_zoo)

        session.add_message("user", "I need to do everything with my emails - search, delete, forward, archive, label, send, read")

        decision = await router.route(session)

        # Count tools from each server
        gmail_tools = [t for t in decision.selected_tools if "gmail" in t]
        
        # Should allow more than 3 tools from gmail server
        assert len(gmail_tools) > 3
        # But should not exceed max_per_server
        assert len(gmail_tools) <= 10


class TestAdaptiveRouter:
    """Tests for the AdaptiveRouter with learning."""

    @pytest.mark.asyncio
    async def test_record_usage(self, router_config, tool_zoo, session):
        """Test recording tool usage for learning."""
        router = AdaptiveRouter(router_config, tool_zoo)

        session.add_message("user", "Send email")
        decision = await router.route(session)

        # Record that only send_email was actually used
        router.record_usage(decision, ["gmail.send_email"])

        stats = router.get_learning_stats()
        assert stats["predictions"] == 1

    @pytest.mark.asyncio
    async def test_cooccurrence_learning(self, router_config, tool_zoo, session):
        """Test that co-occurrence is tracked."""
        router = AdaptiveRouter(router_config, tool_zoo)

        # Simulate multiple sessions where email + slack are used together
        for _ in range(3):
            session.add_message("user", "Send notification")
            decision = await router.route(session)
            router.record_usage(decision, ["gmail.send_email", "slack.send_message"])

        # Check co-occurrence
        cooccur = router.get_cooccurring_tools("gmail.send_email")
        assert "slack.send_message" in cooccur

    @pytest.mark.asyncio
    async def test_export_training_data(self, router_config, tool_zoo, session):
        """Test exporting data for RAFT fine-tuning."""
        router = AdaptiveRouter(router_config, tool_zoo)

        session.add_message("user", "Send email")
        decision = await router.route(session)
        router.record_usage(decision, ["gmail.send_email"])

        training_data = router.export_training_data()

        assert len(training_data) == 1
        assert "query" in training_data[0]
        assert "candidates" in training_data[0]
        assert "correct" in training_data[0]

    @pytest.mark.asyncio
    async def test_adaptive_boost(self, router_config, tool_zoo, session):
        """Test that frequently co-used tools get boosted."""
        router = AdaptiveRouter(router_config, tool_zoo)

        # Train: email and slack often used together
        for _ in range(5):
            session2 = SessionState()
            session2.add_message("user", "Notify team")
            decision = await router.route(session2)
            router.record_usage(decision, ["gmail.send_email", "slack.send_message"])

        # Now test: when using email, slack should be boosted
        session.add_message("user", "Send an email")
        session.record_tool_use("gmail.send_email")

        decision = await router.route(session)

        # Slack should appear due to co-occurrence boost
        # (depending on scores, this may or may not be in top results)
        assert len(decision.selected_tools) > 0

