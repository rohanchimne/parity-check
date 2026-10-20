"""Build per-partition aggregate queries from config. The engines do the work."""

import pandas as pd


def build_profile_sql(table, partition_expr, metrics, by=None):
    """One query: one row per partition (and dimension), one column per metric."""
    by = list(by or [])
    group_cols = [f"{partition_expr} AS partition"] + by
    metric_cols = [f"{m['expr']} AS {m['name']}" for m in metrics]
    positions = ", ".join(str(i + 1) for i in range(len(group_cols)))
    return (
        "SELECT " + ",\n       ".join(group_cols + metric_cols) + "\n"
        f"FROM {table}\n"
        f"GROUP BY {positions}\n"
        f"ORDER BY {positions}"
    )


def run_profile(adapter, side, cfg):
    """Profile one side. Returns a long DataFrame: partition, dimension, metric, value."""
    table = side["table"]
    partition_col = cfg["partition_column"]

    # Metrics that share the same 'by' run in one query
    groups = {}
    for metric in cfg["checks"]["metrics"]:
        groups.setdefault(tuple(metric.get("by", [])), []).append(metric)

    out = []
    for by, metrics in groups.items():
        for row in adapter.profile(table, partition_col, metrics, list(by)):
            partition = row[0]
            dims = row[1:1 + len(by)]
            values = row[1 + len(by):]
            dimension = ",".join(f"{col}={val}" for col, val in zip(by, dims)) or None
            for metric, value in zip(metrics, values):
                out.append({"partition": partition, "dimension": dimension,
                            "metric": metric["name"], "value": value})

    # dtype=object keeps each value as the engine returned it (int, float, Decimal).
    # Without it, pandas silently converts mixed numbers to float.
    return pd.DataFrame(out, dtype=object)
    # return pd.DataFrame(out)