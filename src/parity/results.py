"""Append every check result to a history table. Never update, never delete."""

import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb

RESULTS_PATH = Path("results/results.duckdb")

SCHEMA = """
CREATE TABLE IF NOT EXISTS results (
    run_id        VARCHAR NOT NULL,
    run_ts        TIMESTAMP NOT NULL,
    dataset       VARCHAR NOT NULL,
    tier          INTEGER NOT NULL,
    check_type    VARCHAR NOT NULL,
    partition_key VARCHAR,
    metric        VARCHAR,
    source_value  VARCHAR,
    target_value  VARCHAR,
    status        VARCHAR NOT NULL,
    details       VARCHAR
)
"""


def new_run():
    """A short unique id and the current UTC time for one run."""
    return uuid.uuid4().hex[:12], datetime.now(timezone.utc).replace(tzinfo=None)


def as_text(value):
    """Store values as text so nothing is rounded or converted on the way in."""
    return None if value is None else str(value)


def write_results(results, cfg, run_id, run_ts, path=RESULTS_PATH):
    """Append one row per CheckResult. Returns how many rows were written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        (run_id, run_ts, cfg["dataset"], cfg["tier"], r.check, r.partition, r.metric,
         as_text(r.source_value), as_text(r.target_value), r.status, r.details)
        for r in results
    ]
    con = duckdb.connect(str(path))
    try:
        con.execute(SCHEMA)
        con.executemany("INSERT INTO results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    finally:
        con.close()
    return len(rows)