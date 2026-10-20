"""Pick the right adapter for an engine named in a config."""

from .duckdb_adapter import DuckDBAdapter
from .sqlite_adapter import SQLiteAdapter

ADAPTERS = {"sqlite": SQLiteAdapter, "duckdb": DuckDBAdapter}


def get_adapter(side: dict):
    """side is a config block like {'engine': 'sqlite', 'path': ..., 'table': ...}."""
    return ADAPTERS[side["engine"]](side["path"])