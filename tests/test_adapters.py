import pytest

from parity.adapters import get_adapter
from parity.adapters.base import Adapter


def schemas(clean_dbs):
    source, target = clean_dbs
    src = get_adapter({"engine": "sqlite", "path": source}).schema("orders")
    tgt = get_adapter({"engine": "duckdb", "path": target}).schema("orders")
    return src, tgt


def test_schemas_line_up(clean_dbs):
    src, tgt = schemas(clean_dbs)
    assert [c["name"] for c in src] == [c["name"] for c in tgt]
    assert [c["nullable"] for c in src] == [c["nullable"] for c in tgt]


def test_types_are_reported_per_engine(clean_dbs):
    src, tgt = schemas(clean_dbs)
    revenue_src = next(c for c in src if c["name"] == "revenue")
    revenue_tgt = next(c for c in tgt if c["name"] == "revenue")
    assert revenue_src["type"] == "NUMERIC"
    assert revenue_tgt["type"] == "DECIMAL(18,2)"


def test_missing_database_is_reported(tmp_path):
    adapter = get_adapter({"engine": "duckdb", "path": tmp_path / "nope.db"})
    with pytest.raises(FileNotFoundError, match="generate_data"):
        adapter.connect()


def test_adapter_must_implement_all_four_methods():
    class Incomplete(Adapter):
        def connect(self):
            return None

    with pytest.raises(TypeError):
        Incomplete("anything.db")