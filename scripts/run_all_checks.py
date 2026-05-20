#!/usr/bin/env python3
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Configure root logger before core module imports so format is consistent
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

from config.settings import LOG_DIR  # noqa: E402
from core.process_monitor import run_process_monitor  # noqa: E402
from core.service_checker import run_service_checks  # noqa: E402
from core.system_health import run_health_check  # noqa: E402


def _compute_exit_code(health_result, process_result, service_result) -> int:
    if health_result.overall == "CRITICAL":
        return 2
    if any(s in ("WARNING", "ALERT") for s in [
        health_result.overall, process_result.overall, service_result.overall
    ]):
        return 1
    return 0


def build_report(health_result, process_result, service_result, exit_code: int) -> dict:
    overall = {2: "CRITICAL", 1: "WARNING", 0: "OK"}[exit_code]
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall": overall,
        "exit_code": exit_code,
        "health_check": {
            "overall": health_result.overall,
            "hostname": health_result.hostname,
            "platform": health_result.platform,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "warn_threshold": m.warn_threshold,
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


def log_summary(report: dict, report_path: Path, duration: float) -> None:
    hc = report["health_check"]
    pm = report["process_monitor"]
    sc = report["service_checker"]
    exit_code = report["exit_code"]

    logger.info("=== COMBINED AUTOMATION REPORT ===")
    logger.info(
        "generated_at=%s | overall=%s | exit_code=%d",
        report["generated_at"], report["overall"], exit_code,
    )

    hc_level = (
        logging.CRITICAL if hc["overall"] == "CRITICAL"
        else logging.WARNING if hc["overall"] == "WARNING"
        else logging.INFO
    )
    logger.log(
        hc_level,
        "HEALTH CHECK | host=%s platform=%s | overall=%s",
        hc["hostname"], hc["platform"], hc["overall"],
    )
    for m in hc["metrics"]:
        m_level = (
            logging.CRITICAL if m["status"] == "CRITICAL"
            else logging.WARNING if m["status"] == "WARNING"
            else logging.INFO
        )
        logger.log(
            m_level,
            "%s STATUS: %s | usage=%.1f%%",
            m["name"].upper(), m["status"], m["value"],
        )

    pm_level = logging.WARNING if pm["overall"] != "OK" else logging.INFO
    logger.log(
        pm_level,
        "PROCESS MONITOR | processes=%d zombies=%d flagged=%d | overall=%s",
        len(pm["processes"]), pm["zombie_count"], pm["flagged_count"], pm["overall"],
    )

    sc_level = logging.WARNING if sc["overall"] != "OK" else logging.INFO
    logger.log(
        sc_level,
        "SERVICE CHECKER | targets=%d unhealthy=%d | overall=%s",
        sc["target_count"], sc["unhealthy_count"], sc["overall"],
    )

    logger.info(
        "report=%s | duration=%.2fs | exit_code=%d",
        report_path, duration, exit_code,
    )


def main() -> int:
    t_start = time.perf_counter()

    health_result = run_health_check()
    process_result = run_process_monitor()
    service_result = run_service_checks()

    exit_code = _compute_exit_code(health_result, process_result, service_result)
    report = build_report(health_result, process_result, service_result, exit_code)
    report_path = write_report(report)

    duration = time.perf_counter() - t_start
    log_summary(report, report_path, duration)

    level = logging.CRITICAL if exit_code == 2 else (logging.WARNING if exit_code == 1 else logging.INFO)
    logger.log(level, "Health check completed | exit_code=%d duration=%.2fs", exit_code, duration)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
