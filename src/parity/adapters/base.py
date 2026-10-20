"""The interface every database engine implements."""

from abc import ABC, abstractmethod
from pathlib import Path


class Adapter(ABC):
    """One database engine. Everything engine-specific lives behind four methods."""

    def __init__(self, path):
        self.path = Path(path)
        self._con = None

    @abstractmethod
    def connect(self):
        """Open (once) and return a read-only connection."""

    @abstractmethod
    def schema(self, table):
        """Return [{'name', 'type', 'nullable'}, ...] in column order."""

    @abstractmethod
    def profile(self, table, partition_col, metrics, by=None):
        """Per-partition aggregates, computed inside the engine."""

    @abstractmethod
    def fingerprint_expr(self, columns):
        """SQL that builds one canonical SHA-256 hash per row."""

    # Shared plumbing. Identical for every engine, so it lives here once.

    def query(self, sql, params=None):
        con = self.connect()
        cursor = con.execute(sql, params) if params else con.execute(sql)
        return cursor.fetchall()

    def close(self):
        if self._con is not None:
            self._con.close()
            self._con = None