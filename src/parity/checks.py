"""Compare source and target. Every check returns a list of CheckResult rows."""

from dataclasses import dataclass

from dataclasses import dataclass
from pathlib import Path

import yaml

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

def load_type_map(name, folder="configs/type_maps"):
    """Read a type map file: {source type: [allowed target types]}."""
    path = Path(folder) / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"type map not found: {path}")
    raw = yaml.safe_load(path.read_text())
    return {src.upper(): [t.upper() for t in targets] for src, targets in raw.items()}


def check_schema(src_cols, tgt_cols, type_map, require_nullability_match=True):
    """Compare two schemas column by column. Pure: no database involved."""
    src = {c["name"]: c for c in src_cols}
    tgt = {c["name"]: c for c in tgt_cols}
    results = []
    for name in list(src) + [n for n in tgt if n not in src]:
        s, t = src.get(name), tgt.get(name)
        if t is None:
            status, details = FAIL, "column missing in target"
        elif s is None:
            status, details = FAIL, "column only in target"
        elif t["type"] not in type_map.get(s["type"], []):
            status, details = FAIL, f"{s['type']} -> {t['type']} not allowed by type map"
        elif require_nullability_match and s["nullable"] != t["nullable"]:
            status, details = FAIL, f"nullable {s['nullable']} -> {t['nullable']}"
        else:
            status, details = PASS, ""
        results.append(CheckResult(
            "schema", None, name, s and s["type"], t and t["type"], status, details,
        ))
    return results