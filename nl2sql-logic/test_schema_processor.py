
from types import SimpleNamespace

import pytest

import schema_processor
from schema_processor import SchemaProcessor


def _make_column(name, col_type="INTEGER", nullable=True, primary_key=False):
    return SimpleNamespace(
        name=name,
        type=col_type,
        nullable=nullable,
        primary_key=primary_key,
    )


def _make_fk(parent_name, referenced):
    return SimpleNamespace(
        parent=SimpleNamespace(name=parent_name),
        column=referenced,
    )


def _make_table(columns, foreign_keys=None):
    return SimpleNamespace(columns=columns, foreign_keys=foreign_keys or [])


def _build_processor(metadata_tables=None, enrich_return=None):
    processor = SchemaProcessor.__new__(SchemaProcessor)
    processor.metadata = SimpleNamespace(tables=metadata_tables or {})
    processor.description_heuristics = SimpleNamespace(
        enrich_schema_with_descriptions=lambda schema: enrich_return if enrich_return is not None else schema
    )
    return processor


def test_init_wires_engine_metadata_and_heuristics(monkeypatch):
    calls = {}

    class FakeMetaData:
        def __init__(self):
            self.reflect_called_with = None

        def reflect(self, bind):
            self.reflect_called_with = bind
            calls["reflect_bind"] = bind

    fake_engine = object()

    def fake_create_engine(url):
        calls["url"] = url
        return fake_engine

    class FakeHeuristics:
        pass

    monkeypatch.setattr(schema_processor, "create_engine", fake_create_engine)
    monkeypatch.setattr(schema_processor, "MetaData", FakeMetaData)
    monkeypatch.setattr(schema_processor, "DescriptionHeuristics", FakeHeuristics)

    processor = SchemaProcessor("sqlite:///mock.db")

    assert processor.engine is fake_engine
    assert isinstance(processor.metadata, FakeMetaData)
    assert isinstance(processor.description_heuristics, FakeHeuristics)
    assert calls["url"] == "sqlite:///mock.db"
    assert calls["reflect_bind"] is fake_engine


def test_process_schema_builds_expected_payload_and_enriches():
    users_table = _make_table(
        columns=[
            _make_column("id", "INTEGER", nullable=False, primary_key=True),
            _make_column("name", "VARCHAR(255)", nullable=True, primary_key=False),
        ]
    )
    orders_table = _make_table(
        columns=[
            _make_column("id", "INTEGER", nullable=False, primary_key=True),
            _make_column("user_id", "INTEGER", nullable=False, primary_key=False),
        ],
        foreign_keys=[_make_fk("user_id", "users.id")],
    )

    captured = {}

    def fake_enrich(schema):
        captured["schema"] = schema
        return {"enriched": True, "tables": list(schema.keys())}

    processor = SchemaProcessor.__new__(SchemaProcessor)
    processor.metadata = SimpleNamespace(
        tables={"users": users_table, "orders": orders_table}
    )
    processor.description_heuristics = SimpleNamespace(
        enrich_schema_with_descriptions=fake_enrich
    )

    result = processor.process_schema()

    assert result == {"enriched": True, "tables": ["users", "orders"]}
    assert "schema" in captured
    assert captured["schema"]["users"][0] == {
        "name": "id",
        "type": "INTEGER",
        "nullable": False,
        "primary_key": True,
    }
    assert captured["schema"]["orders"][1] == {
        "name": "user_id",
        "type": "INTEGER",
        "nullable": False,
        "primary_key": False,
    }
    assert captured["schema"]["orders"][2] == {
        "foreign_keys": [{"column": "user_id", "references": "users.id"}]
    }


@pytest.mark.parametrize(
    "name,expected",
    [
        ("orders", False),
        ("order details", True),
        ("customer-name", True),
        ("100users", True),
        ("status%", True),
    ],
)
def test_needs_escape(name, expected):
    processor = _build_processor()
    assert processor.needs_escape(name) is expected


def test_needs_escape_empty_string_returns_false():
    processor = _build_processor()
    assert processor.needs_escape("") is False


def test_format_schema_for_model_escapes_names_and_skips_non_columns():
    processor = _build_processor()
    schema_info = {
        "order details": [
            {
                "name": "line item",
                "type": "INTEGER",
                "nullable": False,
                "primary_key": True,
            },
            {"foreign_keys": [{"column": "line item", "references": "orders.id"}]},
        ],
        "users": [
            {
                "name": "email",
                "type": "VARCHAR(255)",
                "nullable": False,
                "primary_key": False,
            }
        ],
    }

    formatted = processor.format_schema_for_model(schema_info)

    assert "Table: [order details]" in formatted
    assert "Column: [line item], Type: INTEGER, Nullable: False, Primary Key: True" in formatted
    assert "Table: users" in formatted
    assert "Column: email, Type: VARCHAR(255), Nullable: False, Primary Key: False" in formatted
    assert "foreign_keys" not in formatted


def test_get_schema_keys_returns_metadata_table_names():
    processor = _build_processor(
        metadata_tables={"users": object(), "orders": object(), "products": object()}
    )
    assert processor.get_schema_keys() == ["users", "orders", "products"]


def test_write_schema_to_file_json(tmp_path):
    processor = _build_processor()
    schema_info = {
        "users": [
            {
                "name": "id",
                "type": "INTEGER",
                "nullable": False,
                "primary_key": True,
            }
        ]
    }
    out_file = tmp_path / "schema.json"

    processor.write_schema_to_file(schema_info, str(out_file))

    content = out_file.read_text()
    assert '"users"' in content
    assert '"name": "id"' in content


def test_write_schema_to_file_text(tmp_path):
    processor = _build_processor()
    schema_info = {
        "order details": [
            {
                "name": "line-item",
                "type": "INTEGER",
                "nullable": False,
                "primary_key": True,
            }
        ]
    }
    out_file = tmp_path / "schema.txt"

    processor.write_schema_to_file(schema_info, str(out_file))

    content = out_file.read_text()
    assert "Table: [order details]" in content
    assert "Column: [line-item], Type: INTEGER, Nullable: False, Primary Key: True" in content


def test_write_schema_to_file_text_handles_foreign_key_entries_without_name(tmp_path):
    processor = _build_processor()
    schema_info = {
        "orders": [
            {
                "name": "id",
                "type": "INTEGER",
                "nullable": False,
                "primary_key": True,
            },
            {"foreign_keys": [{"column": "user_id", "references": "users.id"}]},
        ]
    }
    out_file = tmp_path / "schema.txt"

    processor.write_schema_to_file(schema_info, str(out_file))

    content = out_file.read_text()
    assert "Column: id, Type: INTEGER, Nullable: False, Primary Key: True" in content
    assert "Foreign Key: user_id -> users.id" in content


def test_print_schema_info_handles_foreign_key_entries_without_name(capsys):
    processor = _build_processor()
    schema_info = {
        "orders": [
            {
                "name": "id",
                "type": "INTEGER",
                "nullable": False,
                "primary_key": True,
            },
            {"foreign_keys": [{"column": "user_id", "references": "users.id"}]},
        ]
    }

    processor.print_schema_info(schema_info)

    output = capsys.readouterr().out
    assert "Table: orders" in output
    assert "Column: id, Type: INTEGER, Nullable: False, Primary Key: True" in output
    assert "Foreign Key: user_id -> users.id" in output
