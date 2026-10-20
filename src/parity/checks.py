"""Compare source and target. Every check returns a list of CheckResult rows."""

from dataclasses import dataclass
from decimal import Decimal
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

def to_decimal(value):
    """Exact Decimal from whatever the engine returned (int, float, Decimal)."""
    return value if isinstance(value, Decimal) else Decimal(str(value))


def rounded(value, scale):
    """Round to `scale` decimal places (2 -> 0.01). No scale: leave as is."""
    value = to_decimal(value)
    return value if scale is None else value.quantize(Decimal(1).scaleb(-scale))


def within(src, tgt, tolerance, scale=None):
    """True if tgt is close enough to src. Pure, exact, never compares floats."""
    s, t = rounded(src, scale), rounded(tgt, scale)
    if tolerance == "exact":
        return s == t
    if s == 0:
        return t == 0
    return abs(t - s) / abs(s) <= Decimal(str(tolerance))


def describe_difference(src, tgt, scale=None):
    """'-99,107.07 (-38.99%)': the change from source to target."""
    s, t = rounded(src, scale), rounded(tgt, scale)
    diff = t - s
    pct = f" ({diff / s:+.2%})" if s != 0 else ""
    return f"{diff:+,}{pct}"


def profile_to_dict(profile):
    """Long profile DataFrame -> {(partition, dimension, metric): value}."""
    out = {}
    for row in profile.itertuples(index=False):
        dimension = row.dimension if isinstance(row.dimension, str) else None
        out[(row.partition, dimension, row.metric)] = row.value
    return out


def check_metrics(src_profile, tgt_profile, metrics):
    """Compare every metric, per partition and dimension, with its own tolerance."""
    by_name = {m["name"]: m for m in metrics}
    src, tgt = profile_to_dict(src_profile), profile_to_dict(tgt_profile)
    results = []
    keys = sorted(set(src) | set(tgt), key=lambda k: (k[0], k[1] or "", k[2]))
    for partition, dimension, name in keys:
        m = by_name[name]
        s = src.get((partition, dimension, name))
        t = tgt.get((partition, dimension, name))
        label = name if dimension is None else f"{name} [{dimension}]"
        if s is None:
            status, details = FAIL, "partition only in target"
        elif t is None:
            status, details = FAIL, "partition only in source"
        elif within(s, t, m["tolerance"], m.get("scale")):
            status, details = PASS, ""
        else:
            status, details = FAIL, describe_difference(s, t, m.get("scale"))
        results.append(CheckResult("metric", partition, label, s, t, status, details))
    return results