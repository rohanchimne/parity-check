from pathlib import Path

from parity.adapters import get_adapter
from parity.config import load_config
from parity.profile import build_profile_sql, run_profile

ORDERS = Path(__file__).resolve().parent.parent / "configs" / "orders.yaml"


def profiles(dbs):
    """Profile both sides of a pair of test databases using the real config."""
    cfg = load_config(ORDERS)
    source, target = dbs
    src_side = {**cfg["source"], "path": source}
    tgt_side = {**cfg["target"], "path": target}
    return (run_profile(get_adapter(src_side), src_side, cfg),
            run_profile(get_adapter(tgt_side), tgt_side, cfg))


def daily_counts(profile):
    rows = profile[profile["metric"] == "order_count"]
    return dict(zip(rows["partition"], rows["value"]))


def test_profile_sql_groups_inside_the_engine():
    sql = build_profile_sql("orders", "order_date",
                            [{"name": "n", "expr": "COUNT(*)"}], by=["region"])
    assert "COUNT(*) AS n" in sql
    assert "GROUP BY 1, 2" in sql


def test_one_row_per_partition_per_metric(clean_dbs):
    src, tgt = profiles(clean_dbs)
    assert len(src) == len(tgt) == 720
    assert src["partition"].nunique() == 90


def test_daily_counts_match_on_clean_data(clean_dbs):
    src, tgt = profiles(clean_dbs)
    assert daily_counts(src) == daily_counts(tgt)


def test_timezone_bug_shows_in_daily_counts(timezone_dbs):
    src, tgt = profiles(timezone_dbs)
    assert daily_counts(src) != daily_counts(tgt)
    assert "2026-04-01" in daily_counts(tgt)
    assert "2026-04-01" not in daily_counts(src)