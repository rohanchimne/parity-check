from parity.adapters import get_adapter
from parity.checks import FAIL, PASS, check_row_count, daily_row_counts


# Pure tests: hand-made dicts, no database, run in milliseconds

def test_matching_counts_pass():
    results = check_row_count({"2026-01-01": 10}, {"2026-01-01": 10})
    assert [r.status for r in results] == [PASS]


def test_different_counts_fail_with_the_difference():
    [r] = check_row_count({"2026-01-01": 200}, {"2026-01-01": 150})
    assert r.status == FAIL
    assert r.details == "-50 rows (-25.0%)"


def test_partition_only_in_target_is_named():
    results = check_row_count({"2026-01-01": 5}, {"2026-01-01": 5, "2026-04-01": 3})
    extra = [r for r in results if r.partition == "2026-04-01"][0]
    assert extra.status == FAIL
    assert extra.details == "partition only in target"
    assert extra.source_value is None


def test_partition_only_in_source_is_named():
    [r] = check_row_count({"2026-01-01": 5}, {})
    assert r.details == "partition only in source"


def test_results_are_sorted_by_partition():
    results = check_row_count({"2026-01-02": 1, "2026-01-01": 1}, {"2026-01-01": 1, "2026-01-02": 1})
    assert [r.partition for r in results] == ["2026-01-01", "2026-01-02"]


# Integration tests: the real databases from conftest.py

def run_row_count(dbs):
    source, target = dbs
    cfg = {"partition_column": "order_date"}
    src = daily_row_counts(get_adapter({"engine": "sqlite", "path": source}), {"table": "orders"}, cfg)
    tgt = daily_row_counts(get_adapter({"engine": "duckdb", "path": target}), {"table": "orders"}, cfg)
    return check_row_count(src, tgt)


def test_clean_data_passes_every_day(clean_dbs):
    results = run_row_count(clean_dbs)
    assert len(results) == 90
    assert all(r.status == PASS for r in results)


def test_timezone_bug_fails_and_names_the_extra_day(timezone_dbs):
    results = run_row_count(timezone_dbs)
    assert any(r.status == FAIL for r in results)
    last = results[-1]
    assert last.partition == "2026-04-01"
    assert last.details == "partition only in target"