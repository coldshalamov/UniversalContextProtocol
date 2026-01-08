"""Tests for the Tool Zoo (vector index)."""

import pytest
import tempfile
from pathlib import Path

from ucp.config import ToolZooConfig
from ucp.models import ToolSchema
from ucp.tool_zoo import ToolZoo, HybridToolZoo


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def tool_zoo_config(temp_dir):
    """Create a test config with temporary directory."""
    return ToolZooConfig(
        embedding_model="all-MiniLM-L6-v2",
        collection_name="test_tools",
        persist_directory=str(Path(temp_dir) / "chromadb"),
        top_k=5,
        similarity_threshold=0.1,
    )


@pytest.fixture
def sample_tools():
    """Create sample tools for testing."""
    return [
        ToolSchema(
            name="gmail.send_email",
            display_name="send_email",
            description="Send an email to a recipient with subject and body",
            server_name="gmail",
            input_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
            },
            tags=["email", "communication"],
            domain="email",
        ),
        ToolSchema(
            name="gmail.list_messages",
            display_name="list_messages",
            description="List recent email messages from inbox",
            server_name="gmail",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
            },
            tags=["email"],
            domain="email",
        ),
        ToolSchema(
            name="github.create_issue",
            display_name="create_issue",
            description="Create a new issue in a GitHub repository",
            server_name="github",
            input_schema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                },
            },
            tags=["code", "git"],
            domain="code",
        ),
        ToolSchema(
            name="stripe.create_charge",
            display_name="create_charge",
            description="Create a payment charge for a customer",
            server_name="stripe",
            input_schema={
                "type": "object",
                "properties": {
                    "amount": {"type": "integer"},
                    "currency": {"type": "string"},
                    "customer_id": {"type": "string"},
                },
            },
            tags=["finance", "payment"],
            domain="finance",
        ),
        ToolSchema(
            name="calendar.create_event",
            display_name="create_event",
            description="Create a calendar event with date, time, and attendees",
            server_name="calendar",
            input_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start_time": {"type": "string"},
                    "attendees": {"type": "array"},
                },
            },
            tags=["calendar", "scheduling"],
            domain="calendar",
        ),
    ]


class TestToolZoo:
    """Tests for the basic ToolZoo."""

    def test_initialize(self, tool_zoo_config):
        """Test zoo initialization."""
        zoo = ToolZoo(tool_zoo_config)
        zoo.initialize()

        assert zoo._initialized
        assert zoo._collection is not None

    def test_add_tools(self, tool_zoo_config, sample_tools):
        """Test adding tools to the zoo."""
        zoo = ToolZoo(tool_zoo_config)
        zoo.initialize()

        count = zoo.add_tools(sample_tools)
        assert count == len(sample_tools)
        assert len(zoo.get_all_tools()) == len(sample_tools)

    def test_search_semantic(self, tool_zoo_config, sample_tools):
        """Test semantic search for tools."""
        zoo = ToolZoo(tool_zoo_config)
        zoo.initialize()
        zoo.add_tools(sample_tools)

        # Search for email-related tools
        results = zoo.search("send an email to john", top_k=3)

        assert len(results) > 0
        tool_names = [t.name for t, _ in results]
        assert "gmail.send_email" in tool_names

    def test_search_payment(self, tool_zoo_config, sample_tools):
        """Test search for payment tools."""
        zoo = ToolZoo(tool_zoo_config)
        zoo.initialize()
        zoo.add_tools(sample_tools)

        results = zoo.search("charge the customer credit card", top_k=3)

        assert len(results) > 0
        tool_names = [t.name for t, _ in results]
        assert "stripe.create_charge" in tool_names

    def test_get_tool(self, tool_zoo_config, sample_tools):
        """Test getting a specific tool."""
        zoo = ToolZoo(tool_zoo_config)
        zoo.initialize()
        zoo.add_tools(sample_tools)

        tool = zoo.get_tool("gmail.send_email")
        assert tool is not None
        assert tool.server_name == "gmail"

    def test_get_tools_by_server(self, tool_zoo_config, sample_tools):
        """Test filtering tools by server."""
        zoo = ToolZoo(tool_zoo_config)
        zoo.initialize()
        zoo.add_tools(sample_tools)

        gmail_tools = zoo.get_tools_by_server("gmail")
        assert len(gmail_tools) == 2
        assert all(t.server_name == "gmail" for t in gmail_tools)

    def test_remove_tools(self, tool_zoo_config, sample_tools):
        """Test removing tools."""
        zoo = ToolZoo(tool_zoo_config)
        zoo.initialize()
        zoo.add_tools(sample_tools)

        initial_count = len(zoo.get_all_tools())
        removed = zoo.remove_tools(["gmail.send_email"])

        assert removed == 1
        assert len(zoo.get_all_tools()) == initial_count - 1
        assert zoo.get_tool("gmail.send_email") is None

    def test_clear(self, tool_zoo_config, sample_tools):
        """Test clearing all tools."""
        zoo = ToolZoo(tool_zoo_config)
        zoo.initialize()
        zoo.add_tools(sample_tools)

        zoo.clear()
        assert len(zoo.get_all_tools()) == 0


class TestHybridToolZoo:
    """Tests for the HybridToolZoo with keyword search."""

    def test_keyword_search(self, tool_zoo_config, sample_tools):
        """Test keyword-based search."""
        zoo = HybridToolZoo(tool_zoo_config)
        zoo.initialize()
        zoo.add_tools(sample_tools)

        # Keywords should match
        results = zoo.keyword_search("email inbox messages", top_k=3)

        assert len(results) > 0
        tool_names = [t.name for t, _ in results]
        # Should find gmail tools
        assert any("gmail" in name for name in tool_names)

    def test_hybrid_search(self, tool_zoo_config, sample_tools):
        """Test combined semantic + keyword search."""
        zoo = HybridToolZoo(tool_zoo_config)
        zoo.initialize()
        zoo.add_tools(sample_tools)

        results = zoo.hybrid_search(
            "schedule a meeting for tomorrow",
            top_k=3,
            semantic_weight=0.6,
            keyword_weight=0.4,
        )

        assert len(results) > 0
        tool_names = [t.name for t, _ in results]
        # Should find calendar tool
        assert "calendar.create_event" in tool_names

    def test_hybrid_vs_semantic(self, tool_zoo_config, sample_tools):
        """Test that hybrid search can find things semantic might miss."""
        zoo = HybridToolZoo(tool_zoo_config)
        zoo.initialize()
        zoo.add_tools(sample_tools)

        # Query with specific keyword
        query = "github issue bug report"

        semantic_results = zoo.search(query, top_k=3)
        hybrid_results = zoo.hybrid_search(query, top_k=3)

        # Both should find github tool
        semantic_names = [t.name for t, _ in semantic_results]
        hybrid_names = [t.name for t, _ in hybrid_results]

        assert "github.create_issue" in hybrid_names
