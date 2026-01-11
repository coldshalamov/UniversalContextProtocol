"""Tests for Session Management."""

import pytest
import tempfile
from pathlib import Path
from uuid import uuid4

from ucp.config import SessionConfig
from ucp.models import SessionState
from ucp.session import SessionManager


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def session_config(temp_dir):
    return SessionConfig(
        persistence="sqlite",
        sqlite_path=str(Path(temp_dir) / "sessions.db"),
        ttl_seconds=3600,
        max_messages=50,
    )


@pytest.fixture
def session_manager(session_config):
    manager = SessionManager(session_config)
    yield manager
    manager.close()


class TestSessionManager:
    """Tests for SessionManager."""

    def test_create_session(self, session_manager):
        """Test creating a new session."""
        session = session_manager.create_session()

        assert session is not None
        assert session.session_id is not None
        assert len(session.messages) == 0

    def test_get_session(self, session_manager):
        """Test retrieving an existing session."""
        created = session_manager.create_session()
        retrieved = session_manager.get_session(created.session_id)

        assert retrieved is not None
        assert retrieved.session_id == created.session_id

    def test_get_session_not_found(self, session_manager):
        """Test retrieving non-existent session."""
        fake_id = uuid4()
        result = session_manager.get_session(fake_id)

        assert result is None

    def test_get_or_create(self, session_manager):
        """Test get_or_create behavior."""
        # With None, should create
        session1 = session_manager.get_or_create_session(None)
        assert session1 is not None

        # With existing ID, should retrieve
        session2 = session_manager.get_or_create_session(session1.session_id)
        assert session2.session_id == session1.session_id

        # With fake ID, should create new
        fake_id = uuid4()
        session3 = session_manager.get_or_create_session(fake_id)
        assert session3.session_id != fake_id  # Creates new, doesn't use fake

    def test_save_and_load_session(self, session_manager):
        """Test session persistence."""
        session = session_manager.create_session()
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there!")
        session.active_tools = ["gmail.send_email"]

        session_manager.save_session(session)

        # Clear memory cache
        session_manager._sessions.clear()

        # Load from database
        loaded = session_manager.get_session(session.session_id)

        assert loaded is not None
        assert len(loaded.messages) == 2
        assert loaded.messages[0].content == "Hello"
        assert loaded.messages[1].content == "Hi there!"

    def test_message_persistence(self, session_manager):
        """Test that messages are properly persisted."""
        session = session_manager.create_session()

        # Add various message types
        session.add_message("user", "Send email to John")
        session.add_message("assistant", "I'll help you send that email")
        session.add_message("tool", "Email sent successfully", tool_name="gmail.send_email")

        session_manager.save_session(session)
        session_manager._sessions.clear()

        loaded = session_manager.get_session(session.session_id)

        assert len(loaded.messages) == 3
        assert loaded.messages[2].tool_name == "gmail.send_email"

    def test_log_tool_usage(self, session_manager):
        """Test logging tool usage."""
        session = session_manager.create_session()

        session_manager.log_tool_usage(
            session.session_id,
            "gmail.send_email",
            success=True,
            execution_time_ms=150.5,
        )

        stats = session_manager.get_tool_usage_stats(session.session_id)

        assert "gmail.send_email" in stats
        assert stats["gmail.send_email"]["uses"] == 1
        assert stats["gmail.send_email"]["success_rate"] == 1.0

    def test_tool_usage_stats_aggregation(self, session_manager):
        """Test aggregated tool usage stats."""
        session = session_manager.create_session()

        # Log multiple uses
        session_manager.log_tool_usage(session.session_id, "gmail.send_email", True, 100)
        session_manager.log_tool_usage(session.session_id, "gmail.send_email", True, 150)
        session_manager.log_tool_usage(session.session_id, "gmail.send_email", False, 200, "Error")

        stats = session_manager.get_tool_usage_stats(session.session_id)

        assert stats["gmail.send_email"]["uses"] == 3
        assert stats["gmail.send_email"]["success_rate"] == pytest.approx(2/3)
        assert stats["gmail.send_email"]["avg_time_ms"] == pytest.approx(150)

    def test_archive_messages(self, session_manager):
        """Test archiving old messages."""
        session = session_manager.create_session()

        # Add many messages
        for i in range(30):
            session.add_message("user", f"Message {i}")

        assert len(session.messages) == 30

        summary = session_manager.archive_messages(session, keep_recent=10)

        # Should have 10 recent + 1 summary
        assert len(session.messages) == 11
        assert session.messages[0].role == "system"
        assert "archived" in session.messages[0].content.lower()


class TestSessionState:
    """Tests for SessionState model."""

    def test_add_message(self):
        """Test adding messages to session."""
        session = SessionState()
        msg = session.add_message("user", "Hello")

        assert len(session.messages) == 1
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_record_tool_use(self):
        """Test recording tool usage."""
        session = SessionState()

        session.record_tool_use("gmail.send_email")
        session.record_tool_use("gmail.send_email")
        session.record_tool_use("github.create_pr")

        assert session.tool_usage["gmail.send_email"] == 2
        assert session.tool_usage["github.create_pr"] == 1

    def test_get_recent_messages(self):
        """Test getting recent messages."""
        session = SessionState()

        for i in range(20):
            session.add_message("user", f"Message {i}")

        recent = session.get_recent_messages(5)

        assert len(recent) == 5
        assert recent[0].content == "Message 15"
        assert recent[4].content == "Message 19"

    def test_get_context_for_routing(self):
        """Test generating context string for routing."""
        session = SessionState()

        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi!")
        session.add_message("tool", "Tool result")  # Should be excluded
        session.add_message("user", "Help me")

        context = session.get_context_for_routing(n_messages=10)

        assert "Hello" in context
        assert "Hi!" in context
        assert "Help me" in context
        assert "Tool result" not in context  # Tool messages excluded
