"""DuckDB: the new warehouse target."""

import duckdb

from .base import Adapter
from ..profile import build_profile_sql

class DuckDBAdapter(Adapter):

    def connect(self):
        if self._con is None:
            if not self.path.exists():
                raise FileNotFoundError(
                    f"database not found: {self.path} (run scripts/generate_data.py first)"
                )
            self._con = duckdb.connect(str(self.path), read_only=True)
        return self._con

    def schema(self, table):
        rows = self.query(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = ?
            ORDER BY ordinal_position
            """,
            [table],
        )
        return [
            {"name": name, "type": col_type.upper(), "nullable": nullable == "YES"}
            for name, col_type, nullable in rows
        ]


    def profile(self, table, partition_col, metrics, by=None):
        # DuckDB returns dates as date objects; render them as text like SQLite
        partition_expr = f"strftime({partition_col}, '%Y-%m-%d')"
        return self.query(build_profile_sql(table, partition_expr, metrics, by))

    def fingerprint_expr(self, columns):
        raise NotImplementedError("built in Phase 4")