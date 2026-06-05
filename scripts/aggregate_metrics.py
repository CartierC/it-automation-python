#!/usr/bin/env python3
"""Aggregate and summarize metrics across JSON execution reports in logs/."""
import json
import sys
from collections import Counter
from pathlib import Path


def load_reports(logs_dir: Path) -> list:
    """Read all report_*.json files from logs_dir, skip unparseable entries."""
    reports = []
    for path in sorted(logs_dir.glob("report_*.json")):
        try:
            reports.append(json.loads(path.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return reports


def aggregate(reports: list) -> dict:
    """Compute aggregate stats across a list of report dicts."""
    if not reports:
        return {"total_runs": 0}

    severity_counts = Counter(r["overall"] for r in reports)

    metric_statuses: Counter = Counter()
    for report in reports:
        for metric in report.get("health_check", {}).get("metrics", []):
            key = f"{metric['name']}:{metric['status']}"
            metric_statuses[key] += 1

    total = len(reports)
    ok_count = severity_counts.get("OK", 0)
    return {
        "total_runs": total,
        "severity_counts": dict(severity_counts),
        "pass_rate": round(ok_count / total * 100, 1),
        "metric_statuses": dict(metric_statuses),
    }


def format_summary(stats: dict) -> str:
    """Return a formatted multi-line summary string."""
    if stats["total_runs"] == 0:
        return "No reports found in logs/."

    lines = [
        "",
        "  ┌─────────────────────────────────────────┐",
        "  │         METRICS AGGREGATE SUMMARY        │",
        "  └─────────────────────────────────────────┘",
        "",
        f"  Total runs   : {stats['total_runs']}",
        f"  Pass rate    : {stats['pass_rate']}%",
        "",
        "  Severity breakdown:",
    ]
    for severity, count in sorted(stats["severity_counts"].items()):
        pct = round(count / stats["total_runs"] * 100, 1)
        lines.append(f"    {severity:<12} {count:>3}  ({pct}%)")
    lines.append("")
    return "\n".join(lines)


def main(logs_dir: Path = None) -> int:
    if logs_dir is None:
        logs_dir = Path(__file__).resolve().parents[1] / "logs"
    reports = load_reports(logs_dir)
    stats = aggregate(reports)
    print(format_summary(stats))
    return 0 if stats["total_runs"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
