"""Load and validate a dataset config file."""

from pathlib import Path

import yaml

ENGINES = {"sqlite", "duckdb"}
REQUIRED_TOP = ["dataset", "tier", "source", "target", "partition_column",
                "primary_key", "columns", "checks"]
REQUIRED_SIDE = ["engine", "path", "table"]
REQUIRED_METRIC = ["name", "expr", "tolerance"]


class ConfigError(Exception):
    """A config file is missing something or has a wrong value."""


def load_config(path) -> dict:
    """Read a YAML config and check it. Raises ConfigError with a readable message."""
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    try:
        cfg = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        raise ConfigError(f"{path.name} is not valid YAML: {e}") from e
    if not isinstance(cfg, dict):
        raise ConfigError(f"{path.name} should contain 'key: value' lines at the top level")
    validate(cfg, path.name)
    return cfg


def validate(cfg: dict, name: str) -> None:
    for key in REQUIRED_TOP:
        if key not in cfg:
            raise ConfigError(f"{name}: missing required key '{key}'")

    for side in ("source", "target"):
        if not isinstance(cfg[side], dict):
            raise ConfigError(f"{name}: '{side}' should contain engine, path and table")
        for key in REQUIRED_SIDE:
            if key not in cfg[side]:
                raise ConfigError(f"{name}: {side} is missing '{key}'")
        if cfg[side]["engine"] not in ENGINES:
            raise ConfigError(
                f"{name}: {side}.engine '{cfg[side]['engine']}' is not one of {sorted(ENGINES)}"
            )

    if cfg["partition_column"] not in cfg["columns"]:
        raise ConfigError(f"{name}: partition_column '{cfg['partition_column']}' is not in columns")

    for i, metric in enumerate(cfg["checks"].get("metrics", [])):
        for key in REQUIRED_METRIC:
            if key not in metric:
                raise ConfigError(f"{name}: checks.metrics[{i}] is missing '{key}'")
        tol = metric["tolerance"]
        if tol != "exact" and not (isinstance(tol, (int, float)) and tol >= 0):
            raise ConfigError(
                f"{name}: metric '{metric['name']}' tolerance must be 'exact' "
                f"or a number >= 0, got {tol!r}"
            )