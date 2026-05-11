
from types import SimpleNamespace

import pytest

import prompt_manager
from prompt_manager import PromptManager


class FakeTensor:
    def __init__(self, value):
        self._value = float(value)

    def item(self):
        return self._value


class FakeModel:
    def encode(self, text, convert_to_tensor=True):
        return text


def _build_manager(schema=None, examples=None):
    manager = PromptManager.__new__(PromptManager)
    manager.nl_input = ""
    manager.model_name = "nl2sql"
    manager.schema = schema if schema is not None else {}
    manager.database_type = "sqlite"
    manager.client = SimpleNamespace(chat=lambda **kwargs: None)
    manager.example_manager = SimpleNamespace(
        get_examples=lambda: examples or [],
        get_static_examples=lambda: [e for e in (examples or []) if e.get("source") != "production"],
        get_production_examples=lambda: [e for e in (examples or []) if e.get("source") == "production"],
    )
    manager.examples = examples or []
    manager.conversation_history = []
    manager.max_history_turns = 3
    manager.model = FakeModel()
    manager._initialize_context()
    return manager


def test_init_uses_mocked_dependencies(monkeypatch):
    class FakeClient:
        pass

    class FakeExampleManager:
        def get_examples(self):
            return []

    monkeypatch.setattr(prompt_manager.ollama, "Client", lambda: FakeClient())
    monkeypatch.setattr(prompt_manager, "ExampleManager", FakeExampleManager)

    def fake_init_transformer(self):
        self.model = FakeModel()

    monkeypatch.setattr(PromptManager, "initialize_sentence_transformer", fake_init_transformer)

    manager = PromptManager(schema={"users": []}, database_type="sqlite")

    assert isinstance(manager.client, FakeClient)
    assert isinstance(manager.model, FakeModel)
    assert manager.examples == []
    assert manager.conversation_history[0]["role"] == "system"


def test_compact_assistant_message_prefers_sql_codeblock():
    manager = _build_manager()
    text = "Here is SQL:\n```sql\nSELECT * FROM users;\n```\nDone"
    assert manager._compact_assistant_message(text) == "SELECT * FROM users;"


def test_compact_assistant_message_falls_back_to_select_statement():
    manager = _build_manager()
    text = "Response: SELECT id FROM users; extra text"
    assert manager._compact_assistant_message(text) == "SELECT id FROM users;"


def test_trim_conversation_history_keeps_system_plus_last_turns():
    manager = _build_manager()
    manager.max_history_turns = 2
    manager.conversation_history = [manager.system_prompt]
    for idx in range(1, 6):
        manager.conversation_history.append({"role": "user", "content": f"q{idx}"})
        manager.conversation_history.append({"role": "assistant", "content": f"a{idx}"})

    manager.trim_conversation_history()

    assert manager.conversation_history[0] == manager.system_prompt
    assert len(manager.conversation_history) == 1 + manager.max_history_turns * 2
    assert manager.conversation_history[-1]["content"] == "a5"
    assert manager.conversation_history[-2]["content"] == "q5"


def test_reset_conversation_keeps_only_system_prompt():
    manager = _build_manager()
    manager.conversation_history.extend(
        [
            {"role": "user", "content": "q"},
            {"role": "assistant", "content": "a"},
        ]
    )

    manager.reset_conversation()

    assert manager.conversation_history == [manager.system_prompt]


def test_build_request_messages_includes_compact_history_and_prompt(monkeypatch):
    manager = _build_manager()
    manager.max_history_turns = 2
    manager.conversation_history = [manager.system_prompt]
    for idx in range(1, 5):
        manager.conversation_history.append({"role": "user", "content": f"q{idx}"})
        manager.conversation_history.append({"role": "assistant", "content": f"a{idx}"})

    monkeypatch.setattr(manager, "generate_prompt", lambda nl: f"PROMPT::{nl}")

    messages = manager._build_request_messages("find users")

    assert messages[0] == manager.system_prompt
    assert messages[-1] == {"role": "user", "content": "PROMPT::find users"}
    assert len(messages) == 1 + manager.max_history_turns * 2 + 1
    assert messages[1]["content"] == "q3"


def test_format_filtered_schema_supports_new_structure_and_escaping():
    manager = _build_manager()
    filtered_schema = {
        "order details": {
            "description": "line items",
            "role_label": "Detail/line-item table",
            "role_confidence": 0.8,
            "columns": [
                {"name": "line item", "type": "INTEGER", "description": "line id"},
                {"name": "order_id", "type": "INTEGER"},
            ],
        }
    }

    formatted = manager.format_filtered_schema(filtered_schema)

    assert "Table: [order details] [role: Detail/line-item table, confidence: 0.8] - line items" in formatted
    assert "Column: [line item], Type: INTEGER - line id" in formatted
    assert "Column: order_id, Type: INTEGER" in formatted


def test_filter_relevant_tables_returns_empty_for_invalid_schema():
    manager = _build_manager(schema=None)
    manager.schema = None

    assert manager.filter_relevant_tables("anything") == {}


def test_filter_relevant_tables_uses_similarity_and_fallback(monkeypatch):
    schema = {
        "orders": [{"name": "order_id", "description": "order"}],
        "customers": [{"name": "customer_name", "description": "customer"}],
    }
    manager = _build_manager(schema=schema)

    def fake_cos_sim(a, b):
        if b.startswith("orders"):
            return FakeTensor(0.65)
        return FakeTensor(0.10)

    monkeypatch.setattr(prompt_manager.util, "pytorch_cos_sim", fake_cos_sim)
    monkeypatch.setattr(manager, "_load_manual_descriptions", lambda: {})

    relevant = manager.filter_relevant_tables("show order totals")

    assert list(relevant.keys()) == ["orders"]

    def low_cos_sim(a, b):
        return FakeTensor(0.05)

    monkeypatch.setattr(prompt_manager.util, "pytorch_cos_sim", low_cos_sim)
    relevant_fallback = manager.filter_relevant_tables("unknown request")

    assert len(relevant_fallback) == 2


def test_generate_prompt_adds_fallback_schema_and_examples(monkeypatch):
    schema = {
        "employees": [{"name": "id", "type": "INTEGER"}],
        "orders": [{"name": "order_id", "type": "INTEGER"}],
    }
    examples = [
        {"question": "Q1", "sql": "SELECT 1;", "source": "static"},
    ]
    manager = _build_manager(schema=schema, examples=examples)

    monkeypatch.setattr(manager, "filter_relevant_tables", lambda _: {})
    monkeypatch.setattr(manager, "_load_manual_descriptions", lambda: {"employees": {"description": "Employee table", "notes": "Use IDs"}})
    monkeypatch.setattr(manager, "select_relevant_examples", lambda _: examples)

    prompt = manager.generate_prompt("list employees")

    assert "Question: list employees" in prompt
    assert "Schema (columns in [brackets] require quoting in SQL):" in prompt
    assert "Table: employees" in prompt
    assert "TABLE SELECTION GUIDE:" in prompt
    assert "Question: Q1" in prompt
    assert prompt.strip().endswith("Just executable SQL:")


def test_load_conversation_history_compacts_and_trims():
    manager = _build_manager()
    manager.max_history_turns = 1
    history = [
        ("How many users?", "user", "ts1"),
        ("```sql\nSELECT COUNT(*) FROM users;\n```", "assistant", "ts2"),
        ("Another question", "user", "ts3"),
        ("SELECT id FROM users;", "assistant", "ts4"),
    ]

    manager.load_conversation_history(history)

    assert manager.conversation_history[0] == manager.system_prompt
    assert len(manager.conversation_history) == 3
    assert manager.conversation_history[1]["role"] == "user"
    assert manager.conversation_history[2]["content"] == "SELECT id FROM users;"


def test_get_response_calls_client_and_persists_compact_memory(monkeypatch):
    manager = _build_manager()

    captured = {}

    def fake_chat(model, messages):
        captured["model"] = model
        captured["messages"] = messages
        return SimpleNamespace(message={"content": "```sql\nSELECT * FROM users;\n```"})

    manager.client = SimpleNamespace(chat=fake_chat)
    monkeypatch.setattr(manager, "_build_request_messages", lambda nl: [{"role": "system", "content": "sys"}, {"role": "user", "content": f"PROMPT::{nl}"}])
    monkeypatch.setattr(manager, "_log_full_prompt", lambda msgs: None)

    response = manager.get_response("show users")

    assert response == "```sql\nSELECT * FROM users;\n```"
    assert captured["model"] == "nl2sql"
    assert captured["messages"][1]["content"] == "PROMPT::show users"
    assert manager.conversation_history[-2] == {"role": "user", "content": "show users"}
    assert manager.conversation_history[-1] == {"role": "assistant", "content": "SELECT * FROM users;"}
