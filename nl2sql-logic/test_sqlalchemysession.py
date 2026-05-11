from types import SimpleNamespace

import pytest

import SQLAlchemySession as sas_module
from SQLAlchemySession import SQLAlchemySession


def test_sqlalchemy_session_instantiation(monkeypatch):
    """Test that SQLAlchemySession can be instantiated."""
    def fake_get_session(self, db_url):
        return SimpleNamespace()
    
    monkeypatch.setattr(SQLAlchemySession, "get_session", staticmethod(lambda db_url: SimpleNamespace()))
    session = SQLAlchemySession()
    assert session is not None


def test_execute_query_returns_list_of_dicts(monkeypatch):
    """Test execute_query returns a list of dictionaries for successful queries."""
    fake_result = SimpleNamespace(
        keys=lambda: ["name", "type"],
        fetchall=lambda: [("users", "table"), ("products", "table")]
    )
    
    fake_session = SimpleNamespace(
        execute=lambda text_obj: fake_result
    )
    
    monkeypatch.setattr(SQLAlchemySession, "get_session", staticmethod(lambda db_url: fake_session))
    session = SQLAlchemySession()
    result = session.execute_query("SELECT name, type FROM sqlite_master;")
    
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] == {"name": "users", "type": "table"}
    assert result[1] == {"name": "products", "type": "table"}


def test_execute_query_returns_empty_list_for_no_results(monkeypatch):
    """Test execute_query returns empty list when no rows are returned."""
    fake_result = SimpleNamespace(
        keys=lambda: ["id"],
        fetchall=lambda: []
    )
    
    fake_session = SimpleNamespace(
        execute=lambda text_obj: fake_result
    )
    
    monkeypatch.setattr(SQLAlchemySession, "get_session", staticmethod(lambda db_url: fake_session))
    session = SQLAlchemySession()
    result = session.execute_query("SELECT * FROM empty_table;")
    
    assert isinstance(result, list)
    assert len(result) == 0


def test_execute_query_returns_error_string_on_exception(monkeypatch):
    """Test execute_query returns error string on database exception."""
    def fake_execute(text_obj):
        raise Exception("Database connection error")
    
    fake_session = SimpleNamespace(execute=fake_execute)
    
    monkeypatch.setattr(SQLAlchemySession, "get_session", staticmethod(lambda db_url: fake_session))
    session = SQLAlchemySession()
    result = session.execute_query("SELECT * FROM users;")
    
    assert isinstance(result, str)
    assert "Database connection error" in result

    def test_execute_query_empty(self):
        session = SQLAlchemySession()
        result = session.execute_query("")
        assert isinstance(result, str)  # Expecting an error message as a string

    def test_execute_query_sql_injection(self):
        session = SQLAlchemySession()
        result = session.execute_query("SELECT name FROM sqlite_master WHERE type='table'; DROP TABLE users; --")
        assert isinstance(result, str)  # Expecting an error message as a string

    def test_execute_query_sql_injection_attempt(self):
        session = SQLAlchemySession()
        result = session.execute_query("SELECT name FROM sqlite_master WHERE type='table'; SELECT * FROM users; --")
        assert isinstance(result, str)  # Expecting an error message as a string
