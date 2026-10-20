"""Run every check for one dataset config. The only place that talks to both engines."""

from .adapters import get_adapter
from .checks import (
    FAIL, WARN, check_metrics, check_row_count, check_schema,
    daily_row_counts, load_type_map,
)
from .profile import run_profile


def apply_settling_window(results, src_partitions, settling_days):
    """The newest source partitions may still receive late data: FAIL becomes WARN."""
    if not settling_days or not src_partitions:
        return results
    settling = set(sorted(src_partitions)[-settling_days:])
    for r in results:
        if r.status == FAIL and r.partition in settling:
            r.status = WARN
            r.details = f"{r.details} (settling window)"
    return results


def run_checks(cfg, type_map_folder="configs/type_maps"):
    """Row count, schema and metrics for one config. Returns a list of CheckResult."""
    src_side, tgt_side = cfg["source"], cfg["target"]
    src, tgt = get_adapter(src_side), get_adapter(tgt_side)
    checks = cfg["checks"]
    results = []
    try:
        src_counts = daily_row_counts(src, src_side, cfg)
        tgt_counts = daily_row_counts(tgt, tgt_side, cfg)
        results += check_row_count(src_counts, tgt_counts)

        if "schema" in checks:
            schema_cfg = checks["schema"]
            results += check_schema(
                src.schema(src_side["table"]),
                tgt.schema(tgt_side["table"]),
                load_type_map(schema_cfg["type_map"], type_map_folder),
                schema_cfg.get("require_nullability_match", True),
            )

        if checks.get("metrics"):
            results += check_metrics(
                run_profile(src, src_side, cfg),
                run_profile(tgt, tgt_side, cfg),
                checks["metrics"],
            )
    finally:
        src.close()
        tgt.close()

    settling_days = cfg.get("gate", {}).get("settling_days", 0)
    return apply_settling_window(results, src_counts, settling_days)