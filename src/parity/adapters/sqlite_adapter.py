"""SQLite: the legacy source."""

import sqlite3

from .base import Adapter


class SQLiteAdapter(Adapter):

    def connect(self):
        if self._con is None:
            if not self.path.exists():
                raise FileNotFoundError(
                    f"database not found: {self.path} (run scripts/generate_data.py first)"
                )
            uri = self.path.resolve().as_uri() + "?mode=ro"
            self._con = sqlite3.connect(uri, uri=True)
        return self._con

    def schema(self, table):
        rows = self.query(f"PRAGMA table_info({table})")
        return [
            # SQLite quirk: an INTEGER PRIMARY KEY can never be NULL,
            # but PRAGMA reports notnull=0 for it. Treat key columns as not nullable.
            {"name": name, "type": col_type.upper(), "nullable": not notnull and not pk}
            for _cid, name, col_type, notnull, _default, pk in rows
        ]

    def profile(self, table, partition_col, metrics, by=None):
        raise NotImplementedError("built in Phase 2, part 3")

    def fingerprint_expr(self, columns):
        raise NotImplementedError("built in Phase 4")