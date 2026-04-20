#!/usr/bin/env python3
# scripts/run_service_checker.py
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.service_checker import run_service_checks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Service Checker — macOS launchd service health via launchctl"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit results as machine-readable JSON",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all detected services, not just configured targets",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_service_checks()

    if args.json:
        payload = {
            "timestamp": result.timestamp,
            "overall": result.overall,
            "target_count": len(result.targets),
            "unhealthy_count": len(result.unhealthy),
            "services": [s.as_dict() for s in (result.services if args.all else result.targets)],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(result.summary(show_all=args.all))

    return 0 if result.overall == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
