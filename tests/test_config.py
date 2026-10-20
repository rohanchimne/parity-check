from pathlib import Path

import pytest

from parity.config import ConfigError, load_config

ORDERS = Path(__file__).resolve().parent.parent / "configs" / "orders.yaml"


def write(tmp_path, text):
    path = tmp_path / "test.yaml"
    path.write_text(text)
    return path


def test_orders_config_loads():
    cfg = load_config(ORDERS)
    assert cfg["dataset"] == "orders"
    assert cfg["partition_column"] == "order_date"


def test_missing_key_is_named(tmp_path):
    with pytest.raises(ConfigError, match="missing required key 'dataset'"):
        load_config(write(tmp_path, "tier: 1\n"))


def test_bad_tolerance_names_the_metric(tmp_path):
    text = ORDERS.read_text().replace("tolerance: 0.001", "tolerance: lots", 1)
    with pytest.raises(ConfigError, match="distinct_customers"):
        load_config(write(tmp_path, text))


def test_missing_file_is_reported(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.yaml")