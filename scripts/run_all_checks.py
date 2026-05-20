#!/usr/bin/env python3
# scripts/run_all_checks.py
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import LOG_DIR
from core.process_monitor import run_process_monitor
from core.service_checker import run_service_checks
from core.system_health import run_health_check

logger = logging.getLogger(__name__)


def build_report(health_result, process_result, service_result) -> dict:
    statuses = (health_result.overall, process_result.overall, service_result.overall)
    if "CRITICAL" in statuses:
        combined = "CRITICAL"
    elif any(s in ("WARNING", "ALERT") for s in statuses):
        combined = "WARNING"
    else:
        combined = "OK"
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall": combined,
        "health_check": {
            "overall": health_result.overall,
            "hostname": health_result.hostname,
            "platform": health_result.platform,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "threshold": m.threshold,
                    "crit_threshold": m.crit_threshold,
                    "unit": m.unit,
                    "status": m.status,
                }
                for m in health_result.metrics
            ],
        },
        "process_monitor": {
            "overall": process_result.overall,
            "cpu_threshold": process_result.cpu_threshold,
            "zombie_count": len(process_result.zombies),
            "flagged_count": len(process_result.flagged),
            "processes": [p.as_dict() for p in process_result.processes],
        },
        "service_checker": {
            "overall": service_result.overall,
            "target_count": len(service_result.targets),
            "unhealthy_count": len(service_result.unhealthy),
            "services": [s.as_dict() for s in service_result.targets],
        },
    }


def write_report(report: dict) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = LOG_DIR / f"report_{ts}.json"
    path.write_text(json.dumps(report, indent=2))
    return path


def print_summary(report: dict, report_path: Path) -> None:
    hc = report["health_check"]
    pm = report["process_monitor"]
    sc = report["service_checker"]
    overall = report["overall"]

    if overall == "CRITICAL":
        flag = "✗  CRITICAL"
    elif overall == "WARNING":
        flag = "⚠️  WARNING"
    else:
        flag = "✓  OK"

    lines = [
        "",
        "  ┌─────────────────────────────────────────┐",
        "  │         COMBINED AUTOMATION REPORT       │",
        "  └─────────────────────────────────────────┘",
        "",
        f"  Generated  : {report['generated_at']}",
        f"  Overall    : {flag}",
        "",
        "  ── Health Check ──────────────────────────",
        f"  Host       : {hc['hostname']}",
        f"  Platform   : {hc['platform']}",
        f"  Status     : {hc['overall']}",
    ]
    for m in hc["metrics"]:
        icon = "⚠️ " if m["status"] != "OK" else "✓ "
        lines.append(f"    {icon} {m['name']:<12} {m['value']:>6.1f}%  [{m['status']}]")

    lines += [
        "",
        "  ── Process Monitor ───────────────────────",
        f"  Status     : {pm['overall']}",
        f"  Zombies    : {pm['zombie_count']}",
        f"  Flagged    : {pm['flagged_count']}",
    ]
    if pm["flagged_count"]:
        for p in pm["processes"]:
            if p["flagged"]:
                reason = "ZOMBIE" if p["is_zombie"] else f"CPU {p['cpu_percent']}%"
                lines.append(f"    ⚠️  PID {p['pid']:>6}  {p['name']:<25}  {reason}")

    lines += [
        "",
        "  ── Service Checker ───────────────────────",
        f"  Status     : {sc['overall']}",
        f"  Targets    : {sc['target_count']}",
        f"  Unhealthy  : {sc['unhealthy_count']}",
    ]
    if sc["unhealthy_count"]:
        for s in sc["services"]:
            if not s["healthy"]:
                lines.append(f"    ⚠️  {s['name']:<50}  [UNHEALTHY]")

    lines += [
        "",
        f"  Report     : {report_path}",
        "",
    ]
    print("\n".join(lines))


def main() -> int:
    t0 = time.perf_counter()

    logger.info("Orchestration started | checks=health,process,service")

    health_result = run_health_check()
    logger.info("Health check complete | status=%s", health_result.overall)

    process_result = run_process_monitor()
    logger.info("Process monitor complete | status=%s", process_result.overall)

    service_result = run_service_checks()
    logger.info("Service checker complete | status=%s", service_result.overall)

    report = build_report(health_result, process_result, service_result)
    report_path = write_report(report)
    print_summary(report, report_path)

    duration = time.perf_counter() - t0
    exit_codes = {"OK": 0, "WARNING": 1, "CRITICAL": 2}
    exit_code = exit_codes.get(report["overall"], 1)
    logger.info(
        "Orchestration complete | overall=%s exit_code=%d duration=%.2fs",
        report["overall"], exit_code, duration,
    )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
