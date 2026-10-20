from datetime import datetime
from decimal import Decimal

import duckdb

from parity.checks import FAIL, PASS, CheckResult
from parity.results import write_results

CFG = {"dataset": "orders", "tier": 1}


def read(path):
    con = duckdb.connect(str(path), read_only=True)
    rows = con.execute(
        "SELECT run_id, partition_key, source_value, target_value, status "
        "FROM results ORDER BY run_id, partition_key"
    ).fetchall()
    con.close()
    return rows


def test_results_are_appended_not_replaced(tmp_path):
    path = tmp_path / "results.duckdb"
    result = [CheckResult("row_count", "2026-01-01", "row_count", 5, 5, PASS)]
    write_results(result, CFG, "run1", datetime(2026, 1, 1), path)
    write_results(result, CFG, "run2", datetime(2026, 1, 2), path)
    assert [row[0] for row in read(path)] == ["run1", "run2"]


def test_values_are_stored_exactly_as_text(tmp_path):
    path = tmp_path / "results.duckdb"
    results = [
        CheckResult("metric", "2026-01-01", "total_revenue",
                    254199.72999999998, Decimal("254199.73"), PASS),
        CheckResult("row_count", "2026-04-01", "row_count",
                    None, 1814, FAIL, "partition only in target"),
    ]
    write_results(results, CFG, "run1", datetime(2026, 1, 1), path)
    rows = read(path)
    assert rows[0][2:4] == ("254199.72999999998", "254199.73")
    assert rows[1][2] is None