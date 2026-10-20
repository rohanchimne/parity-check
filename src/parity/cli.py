"""Command line: python -m parity run configs/orders.yaml"""

import argparse
import sys
from collections import Counter

from .checks import FAIL, PASS, WARN
from .config import ConfigError, load_config
from .results import RESULTS_PATH, new_run, write_results
from .runner import run_checks

EXIT_OK, EXIT_FAILED, EXIT_USAGE = 0, 1, 2


def print_report(cfg, results, run_id, show=10):
    print(f"parity-check  dataset={cfg['dataset']}  run={run_id}")
    print(f"source: {cfg['source']['engine']}  {cfg['source']['path']}")
    print(f"target: {cfg['target']['engine']}  {cfg['target']['path']}\n")

    by_check = {}
    for r in results:
        by_check.setdefault(r.check, Counter())[r.status] += 1
    for check, counts in by_check.items():
        print(f"{check:<10} {counts[PASS]:>5} pass  {counts[WARN]:>4} warn  {counts[FAIL]:>5} fail")

    problems = [r for r in results if r.status != PASS]
    if problems:
        print(f"\nfirst {min(show, len(problems))} of {len(problems)} problems:")
        for r in problems[:show]:
            print(f"  {r.status}  {r.check:<9} {r.partition or '-':<10}  {r.metric:<34} {r.details}")

    fails = sum(1 for r in results if r.status == FAIL)
    print(f"\nRESULT: {'FAIL' if fails else 'PASS'}  ({fails} failed checks)")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="parity", description="Prove two engines return the same answers.")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run every check for one dataset config")
    run.add_argument("config", help="path to a dataset config, e.g. configs/orders.yaml")
    run.add_argument("--results", default=str(RESULTS_PATH), help="results history file")
    run.add_argument("--type-maps", default="configs/type_maps", help="folder of type map files")
    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.config)
        results = run_checks(cfg, args.type_maps)
    except (ConfigError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_USAGE

    run_id, run_ts = new_run()
    write_results(results, cfg, run_id, run_ts, args.results)
    print_report(cfg, results, run_id)
    return EXIT_FAILED if any(r.status == FAIL for r in results) else EXIT_OK