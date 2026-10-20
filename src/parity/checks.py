"""Compare source and target. Every check returns a list of CheckResult rows."""

from dataclasses import dataclass

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


@dataclass
class CheckResult:
    """One verdict: one check, on one partition, for one metric."""
    check: str
    partition: str | None
    metric: str | None
    source_value: object
    target_value: object
    status: str
    details: str = ""


def daily_row_counts(adapter, side, cfg):
    """Fetch {partition: row count} from one side. The engine does the counting."""
    rows = adapter.profile(
        side["table"],
        cfg["partition_column"],
        [{"name": "row_count", "expr": "COUNT(*)"}],
    )
    return {partition: count for partition, count in rows}


def check_row_count(src_counts, tgt_counts):
    """Compare two {partition: count} dicts. Pure: no database involved."""
    results = []
    for partition in sorted(set(src_counts) | set(tgt_counts)):
        s = src_counts.get(partition)
        t = tgt_counts.get(partition)
        if s is None:
            status, details = FAIL, "partition only in target"
        elif t is None:
            status, details = FAIL, "partition only in source"
        elif s == t:
            status, details = PASS, ""
        else:
            status, details = FAIL, f"{t - s:+,} rows ({(t - s) / s:+.1%})"
        results.append(CheckResult("row_count", partition, "row_count", s, t, status, details))
    return results