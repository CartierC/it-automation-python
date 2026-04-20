#!/usr/bin/env python3
# scripts/run_process_monitor.py
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import PROCESS_TOP_N
from core.process_monitor import kill_process, run_process_monitor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process Monitor — top CPU consumers, zombie detection, threshold alerts"
    )
    parser.add_argument(
        "--top", "-n",
        type=int,
        default=PROCESS_TOP_N,
        metavar="N",
        help=f"Number of processes to display (default: {PROCESS_TOP_N})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit results as machine-readable JSON",
    )
    parser.add_argument(
        "--kill",
        type=int,
        metavar="PID",
        help="Send SIGTERM to the specified PID (prompts for confirmation)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.kill:
        confirm = input(f"Send SIGTERM to PID {args.kill}? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return 0
        success = kill_process(args.kill)
        return 0 if success else 1

    result = run_process_monitor(top_n=args.top)

    if args.json:
        payload = {
            "timestamp": result.timestamp,
            "overall": result.overall,
            "top_n": result.top_n,
            "cpu_threshold": result.cpu_threshold,
            "zombie_count": len(result.zombies),
            "flagged_count": len(result.flagged),
            "processes": [p.as_dict() for p in result.processes],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(result.summary())

    return 0 if result.overall == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
