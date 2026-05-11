from types import SimpleNamespace
from datetime import datetime
from unittest.mock import MagicMock
import sys

import pytest

# Mock psycopg2 before importing modules that depend on it
sys.modules['psycopg2'] = MagicMock()

import conversation_controller as cc_module
from conversation_controller import ConversationController


class FakeCursor:
    def __init__(self, results=None):
        self.results = results or []
        self.executed_query = None
        self.executed_params = None
        self.committed = False

    def execute(self, query, params=None):
        self.executed_query = query
        self.executed_params = params or ()

    def fetchone(self):
        return self.results[0] if self.results else None

    def fetchall(self):
        return self.results


class FakeConnection:
    def __init__(self, cursor=None):
        self.cursor_obj = cursor or FakeCursor()
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.cursor_obj.committed = True

    def close(self):
        self.closed = True


def _build_controller(mock_connection=None):
    """Factory to build a controller with optional connection mock."""
    controller = ConversationController()
    return controller


def test_conversation_controller_instantiation():
    controller = ConversationController()
    assert controller is not None


def test_test_db_connection_success(monkeypatch):
    """Test database connection check when successful."""
    fake_cursor = FakeCursor()
    fake_conn = FakeConnection(fake_cursor)

    def fake_get_connection():
        return fake_conn

    monkeypatch.setattr(cc_module, "get_connection", fake_get_connection)

    controller = _build_controller()
    result = controller.test_db_connection()

    assert result is True
    assert fake_conn.closed is True


def test_test_db_connection_failure(monkeypatch):
    """Test database connection check when it fails."""
    def fake_get_connection():
        return None

    monkeypatch.setattr(cc_module, "get_connection", fake_get_connection)

    controller = _build_controller()
    result = controller.test_db_connection()

    assert result is False


def test_create_conversation_success(monkeypatch):
    """Create conversation returns ID when successful."""
    fake_cursor = FakeCursor(results=[(42,)])
    fake_conn = FakeConnection(fake_cursor)

    def fake_get_connection():
        return fake_conn

    monkeypatch.setattr(cc_module, "get_connection", fake_get_connection)

    controller = _build_controller()
    result = controller.create_conversation("sqlite:///test.db", "sqlite", user_id=1)

    assert result == 42
    assert "INSERT INTO conversations" in fake_cursor.executed_query
    assert fake_cursor.executed_params == ("sqlite:///test.db", "sqlite", 1)
    assert fake_cursor.committed is True


def test_create_conversation_db_failure(monkeypatch):
    """Create conversation returns None on connection failure."""
    def fake_get_connection():
        return None

    monkeypatch.setattr(cc_module, "get_connection", fake_get_connection)

    controller = _build_controller()
    result = controller.create_conversation("sqlite:///test.db", "sqlite", user_id=1)

    assert result is None


def test_get_conversations_returns_list(monkeypatch):
    """Get conversations returns a list of tuples."""
    fake_results = [
        (1, "conv1", datetime.now()),
        (2, "conv2", datetime.now()),
    ]
    fake_cursor = FakeCursor(results=fake_results)
    fake_conn = FakeConnection(fake_cursor)

    def fake_get_connection():
        return fake_conn

    monkeypatch.setattr(cc_module, "get_connection", fake_get_connection)

    controller = _build_controller()
    result = controller.get_conversations(user_id=1)

    assert result == fake_results
    assert "SELECT id, name, created_at FROM conversations" in fake_cursor.executed_query
    assert fake_cursor.executed_params == (1,)


def test_get_conversations_empty(monkeypatch):
    """Get conversations returns empty list when no conversations exist."""
    fake_cursor = FakeCursor(results=[])
    fake_conn = FakeConnection(fake_cursor)

    def fake_get_connection():
        return fake_conn

    monkeypatch.setattr(cc_module, "get_connection", fake_get_connection)

    controller = _build_controller()
    result = controller.get_conversations(user_id=999)

    assert result == []


def test_add_message_to_conversation_success(monkeypatch):
    """Add message returns True on success."""
    fake_cursor = FakeCursor()
    fake_conn = FakeConnection(fake_cursor)

    def fake_get_connection():
        return fake_conn

    monkeypatch.setattr(cc_module, "get_connection", fake_get_connection)

    controller = _build_controller()
    result = controller.add_message_to_conversation(
        conversation_id=1,
        message="What is 2+2?",
        sender="user"
    )

    assert result is True
    assert "INSERT INTO conversation_history" in fake_cursor.executed_query
    assert fake_cursor.executed_params == (1, "What is 2+2?", "user")
    assert fake_cursor.committed is True


def test_add_message_to_conversation_db_failure(monkeypatch):
    """Add message returns False on connection failure."""
    def fake_get_connection():
        return None

    monkeypatch.setattr(cc_module, "get_connection", fake_get_connection)

    controller = _build_controller()
    result = controller.add_message_to_conversation(
        conversation_id=1,
        message="Test",
        sender="user"
    )

    assert result is False


def test_get_conversation_history_returns_list(monkeypatch):
    """Get conversation history returns a list of tuples."""
    now = datetime.now()
    fake_results = [
        ("What is 2+2?", "user", now),
        ("4", "assistant", now),
    ]
    fake_cursor = FakeCursor(results=fake_results)
    fake_conn = FakeConnection(fake_cursor)

    def fake_get_connection():
        return fake_conn

    monkeypatch.setattr(cc_module, "get_connection", fake_get_connection)

    controller = _build_controller()
    result = controller.get_conversation_history(conversation_id=1)

    assert result == fake_results
    assert "SELECT message, sender, timestamp FROM conversation_history" in fake_cursor.executed_query
    assert fake_cursor.executed_params == (1,)


def test_get_conversation_details_returns_dict(monkeypatch):
    """Get conversation details returns a properly formatted dictionary."""
    now = datetime.now()
    fake_results = [(1, "postgresql://localhost/db", "postgresql", now)]
    fake_cursor = FakeCursor(results=fake_results)
    fake_conn = FakeConnection(fake_cursor)

    def fake_get_connection():
        return fake_conn

    monkeypatch.setattr(cc_module, "get_connection", fake_get_connection)

    controller = _build_controller()
    result = controller.get_conversation_details(conversation_id=1)

    assert isinstance(result, dict)
    assert result["id"] == 1
    assert result["db_url"] == "postgresql://localhost/db"
    assert result["database_type"] == "postgresql"
    assert result["created_at"] == now


def test_get_conversation_details_not_found(monkeypatch):
    """Get conversation details returns None when conversation not found."""
    fake_cursor = FakeCursor(results=[])
    fake_conn = FakeConnection(fake_cursor)

    def fake_get_connection():
        return fake_conn

    monkeypatch.setattr(cc_module, "get_connection", fake_get_connection)

    controller = _build_controller()
    result = controller.get_conversation_details(conversation_id=999)

    assert result is None


def test_rename_conversation_success(monkeypatch):
    """Rename conversation returns True on success."""
    fake_cursor = FakeCursor()
    fake_conn = FakeConnection(fake_cursor)

    def fake_get_connection():
        return fake_conn

    monkeypatch.setattr(cc_module, "get_connection", fake_get_connection)

    controller = _build_controller()
    result = controller.rename_conversation(conversation_id=1, new_name="Updated Name")

    assert result is True
    assert "UPDATE conversations SET name" in fake_cursor.executed_query
    assert fake_cursor.executed_params == ("Updated Name", 1)


def test_delete_conversation_success(monkeypatch):
    """Delete conversation returns True and calls delete queries."""
    fake_cursor = FakeCursor()
    fake_conn = FakeConnection(fake_cursor)
    
    call_count = {"count": 0}
    original_execute = fake_cursor.execute
    
    def track_execute(query, params=None):
        call_count["count"] += 1
        original_execute(query, params)
    
    fake_cursor.execute = track_execute

    def fake_get_connection():
        return fake_conn

    monkeypatch.setattr(cc_module, "get_connection", fake_get_connection)

    controller = _build_controller()
    result = controller.delete_conversation(conversation_id=1)

    assert result is True
    assert call_count["count"] == 2  # One for history, one for conversation
    assert fake_cursor.committed is True

    def test_add_message_to_conversation_invalid_role(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        result = conversation_controller.add_message_to_conversation(conversation_id, "invalid_role", "What is the total sales for last month?")
        assert result is False

    def test_add_message_to_conversation_sql_injection(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        sql_injection_message = "What is the total sales for last month?'; DROP TABLE conversations; --"
        result = conversation_controller.add_message_to_conversation(conversation_id, "user", sql_injection_message)
        assert result is False

    def test_add_message_to_conversation_sql_injection_attempt(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        sql_injection_attempt_message = "What is the total sales for last month?'; SELECT * FROM conversations; --"
        result = conversation_controller.add_message_to_conversation(conversation_id, "user", sql_injection_attempt_message)
        assert result is False

    def test_get_conversation_history_invalid_conversation(self):
        conversation_controller = ConversationController()
        history = conversation_controller.get_conversation_history(9999)
        assert history is None

    def test_get_conversation_history_no_messages(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        history = conversation_controller.get_conversation_history(conversation_id)
        assert history == []

    def test_get_conversation_history_with_messages(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        conversation_controller.add_message_to_conversation(conversation_id, "user", "What is the total sales for last month?")
        history = conversation_controller.get_conversation_history(conversation_id)
        assert len(history) == 1
        assert history[0][0] == "What is the total sales for last month?"
        assert history[0][1] == "user"

    def test_get_conversation_details(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        details = conversation_controller.get_conversation_details(conversation_id)
        assert details is not None
        assert details["id"] == conversation_id
        assert details["db_url"] is not None
        assert details["database_type"] is not None
        assert details["created_at"] is not None

    def test_get_conversation_details_invalid_conversation(self):
        conversation_controller = ConversationController()
        details = conversation_controller.get_conversation_details(9999)
        assert details is None

    def test_get_conversation_details_empty_conversation(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        details = conversation_controller.get_conversation_details(conversation_id)
        assert details is not None
        assert details["id"] == conversation_id

    def test_get_conversation_details_sql_injection(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        sql_injection_conversation_id = "9999; DROP TABLE conversations; --"
        details = conversation_controller.get_conversation_details(sql_injection_conversation_id)
        assert details is None

    def test_get_conversation_details_sql_injection_attempt(self):
        conversation_controller = ConversationController()
        conversation_id = conversation_controller.create_conversation("testuser")
        sql_injection_attempt_conversation_id = "9999; SELECT * FROM conversations; --"
        details = conversation_controller.get_conversation_details(sql_injection_attempt_conversation_id)
        assert details is None

    def test_get_conversations_no_conversations(self):
        conversation_controller = ConversationController()
        conversations = conversation_controller.get_conversations("user_with_no_conversations")
        assert conversations == []

    def test_get_conversations_with_conversations(self):
        conversation_controller = ConversationController()
        conversation_controller.create_conversation("testuser")
        conversations = conversation_controller.get_conversations("testuser")
        assert len(conversations) >= 1
        assert conversations[0]["username"] == "testuser"
        assert conversations[0]["db_url"] is not None
        assert conversations[0]["database_type"] is not None
        assert conversations[0]["created_at"] is not None

    def test_get_conversations_sql_injection(self):
        conversation_controller = ConversationController()
        conversations = conversation_controller.get_conversations("testuser'; DROP TABLE conversations; --")
        assert conversations is None

    def test_get_conversations_sql_injection_attempt(self):
        conversation_controller = ConversationController()
        conversations = conversation_controller.get_conversations("testuser'; SELECT * FROM conversations; --")
        assert conversations is None
