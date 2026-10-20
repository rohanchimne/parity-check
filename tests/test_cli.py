from pathlib import Path

import yaml

from parity.checks import FAIL, WARN, CheckResult
from parity.cli import main
from parity.config import load_config
from parity.runner import apply_settling_window

ROOT = Path(__file__).resolve().parent.parent
ORDERS = ROOT / "configs" / "orders.yaml"
TYPE_MAPS = ROOT / "configs" / "type_maps"


def write_config(tmp_path, dbs):
    """The real orders config, pointed at a pair of test databases."""
    cfg = load_config(ORDERS)
    source, target = dbs
    cfg["source"]["path"] = str(source)
    cfg["target"]["path"] = str(target)
    path = tmp_path / "orders.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return path


def run_cli(tmp_path, dbs, capsys):
    code = main([
        "run", str(write_config(tmp_path, dbs)),
        "--results", str(tmp_path / "results.duckdb"),
        "--type-maps", str(TYPE_MAPS),
    ])
    return code, capsys.readouterr().out


def test_clean_run_passes_with_exit_code_0(tmp_path, clean_dbs, capsys):
    code, out = run_cli(tmp_path, clean_dbs, capsys)
    assert code == 0
    assert "RESULT: PASS" in out


def test_timezone_run_fails_with_exit_code_1(tmp_path, timezone_dbs, capsys):
    code, out = run_cli(tmp_path, timezone_dbs, capsys)
    assert code == 1
    assert "RESULT: FAIL" in out


def test_bad_config_exits_2_with_one_clean_line(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("tier: 1\n")
    assert main(["run", str(bad)]) == 2
    err = capsys.readouterr().err
    assert "missing required key 'dataset'" in err
    assert "Traceback" not in err


def test_settling_window_turns_newest_fails_into_warns():
    days = ["2026-03-29", "2026-03-30", "2026-03-31"]
    results = [CheckResult("row_count", d, "row_count", 1, 2, FAIL) for d in days]
    apply_settling_window(results, {d: 1 for d in days}, settling_days=2)
    assert [r.status for r in results] == [FAIL, WARN, WARN]