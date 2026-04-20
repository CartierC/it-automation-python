#!/usr/bin/env python3
"""
CLI entry point for the system health checker.

Usage:
    python scripts/run_health_check.py
    python scripts/run_health_check.py --quiet
    python scripts/run_health_check.py --json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.system_health import run_health_check


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="System Health Checker — CPU, Memory, and Disk monitoring with threshold alerts"
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Print only the overall status (OK / ALERT)",
    )
    output.add_argument(
        "--json",
        action="store_true",
        help="Emit results as machine-readable JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_health_check()

    if args.quiet:
        print(result.overall)
    elif args.json:
        payload = {
            "hostname": result.hostname,
            "platform": result.platform,
            "timestamp": result.timestamp,
            "overall": result.overall,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "threshold": m.threshold,
                    "unit": m.unit,
                    "status": m.status,
                }
                for m in result.metrics
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(result.summary())

    return 0 if result.overall == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
