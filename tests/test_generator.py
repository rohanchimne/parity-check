"""Tests for the synthetic data generator."""

import sqlite3

import duckdb

import generate_data as gen


def daily_source(path):
    """Per day in SQLite: (row count, revenue in whole cents)."""
    con = sqlite3.connect(path)
    rows = con.execute("""
        SELECT order_date,
               COUNT(*),
               SUM(CAST(ROUND(revenue * 100) AS INTEGER))
        FROM orders
        GROUP BY order_date
        ORDER BY order_date
    """).fetchall()
    con.close()
    return {day: (count, cents) for day, count, cents in rows}


def daily_target(path):
    """Per day in DuckDB: (row count, revenue in whole cents)."""
    con = duckdb.connect(str(path), read_only=True)
    rows = con.execute("""
        SELECT strftime(order_date, '%Y-%m-%d'),
               COUNT(*),
               SUM(CAST(revenue * 100 AS BIGINT))
        FROM orders
        GROUP BY order_date
        ORDER BY order_date
    """).fetchall()
    con.close()
    return {day: (count, cents) for day, count, cents in rows}


def totals(daily):
    """Whole-table (row count, revenue in cents), summed from the per-day numbers."""
    rows = sum(count for count, _ in daily.values())
    cents = sum(c for _, c in daily.values())
    return rows, cents


def test_clean_data_matches_every_day(clean_dbs):
    source, target = clean_dbs
    src = daily_source(source)
    tgt = daily_target(target)
    assert len(src) == 90
    assert src == tgt


def test_generator_is_deterministic():
    assert gen.build_orders().equals(gen.build_orders())


def test_timezone_bug_keeps_totals_but_moves_days(timezone_dbs):
    source, target = timezone_dbs
    src = daily_source(source)
    tgt = daily_target(target)

    assert totals(src) == totals(tgt)                         # nothing is lost...
    assert src != tgt                                         # ...but the days are wrong
    assert "2026-04-01" in tgt and "2026-04-01" not in src    # and a day appears from nowhere