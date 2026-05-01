#!/usr/bin/env python3
"""
Failure simulator — simulates operational failure scenarios without
modifying any real system state. Used for testing, observability
demonstration, and SRE interview portfolio evidence.

Scenarios:
    1. disk_threshold_exceeded  — disk usage above configured threshold
    2. missing_service          — required launchd service has no PID
    3. config_validation        — thresholds config missing required keys

Exit code: 0 if all scenarios resolve to ALERT as expected (simulation
           worked correctly); 1 if a scenario returned an unexpected state.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_LOG_PATH = _ROOT / "logs" / "failure_simulator.log"
_THRESHOLDS_PATH = _ROOT / "config" / "thresholds.json"

logger = logging.getLogger("tools.failure_simulator")
if not logger.handlers:
    _handler = logging.FileHandler(_LOG_PATH)
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

REQUIRED_THRESHOLD_KEYS = {"cpu_percent", "memory_percent", "disk_percent"}


# ── Scenario 1: Disk threshold exceeded ───────────────────────────────────────

def simulate_disk_threshold_exceeded() -> dict:
    """Simulate disk usage reading above the configured 90% threshold."""
    thresholds = json.loads(_THRESHOLDS_PATH.read_text())
    threshold = float(thresholds.get("disk_percent", 90))
    simulated_value = threshold + 4.3  # guaranteed breach

    status = "ALERT" if simulated_value >= threshold else "OK"
    message = (
        f"Simulated disk usage {simulated_value:.1f}% "
        f"exceeds threshold {threshold:.0f}%"
    )
    logger.warning(
        "check=disk_usage status=%s simulated=%.1f%% threshold=%.0f%%",
        status, simulated_value, threshold,
    )
    return {
        "scenario": "disk_threshold_exceeded",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "check": "disk_usage",
        "simulated_value": simulated_value,
        "threshold": threshold,
        "unit": "%",
        "status": status,
        "message": message,
    }


# ── Scenario 2: Missing required service ──────────────────────────────────────

def simulate_missing_service() -> dict:
    """Simulate a launchd target service that is absent from launchctl output."""
    target = "com.example.CriticalDaemon"

    # Represent what launchctl list would return for a missing service
    simulated_launchctl_entry = {"pid": "-", "exit_status": "N/A", "name": target}
    healthy = simulated_launchctl_entry["pid"] != "-"
    status = "OK" if healthy else "ALERT"
    message = (
        f"Service '{target}' not found in launchctl output — "
        "no PID assigned, health=False"
    )
    logger.warning(
        "check=service_health status=%s service=%s pid=%s",
        status, target, simulated_launchctl_entry["pid"],
    )
    return {
        "scenario": "missing_service",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "check": "service_health",
        "service": target,
        "pid": simulated_launchctl_entry["pid"],
        "exit_status": simulated_launchctl_entry["exit_status"],
        "healthy": healthy,
        "status": status,
        "message": message,
    }


# ── Scenario 3: Config validation failure ─────────────────────────────────────

def simulate_config_validation_failure() -> dict:
    """Simulate a thresholds config that is missing required keys."""
    incomplete_config = {"cpu_percent": 85}  # memory_percent + disk_percent absent
    missing = sorted(REQUIRED_THRESHOLD_KEYS - incomplete_config.keys())
    status = "ALERT" if missing else "OK"
    message = f"Config missing required keys: {missing}"
    logger.error(
        "check=config_validation status=%s missing_keys=%s",
        status, missing,
    )
    return {
        "scenario": "config_validation_failure",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "check": "config_validation",
        "required_keys": sorted(REQUIRED_THRESHOLD_KEYS),
        "present_keys": sorted(incomplete_config.keys()),
        "missing_keys": missing,
        "status": status,
        "message": message,
    }


# ── Combined runner ────────────────────────────────────────────────────────────

def run_all_scenarios() -> list:
    logger.info("event=start message='running all failure simulation scenarios'")
    scenarios = [
        simulate_disk_threshold_exceeded(),
        simulate_missing_service(),
        simulate_config_validation_failure(),
    ]
    alert_count = sum(1 for s in scenarios if s["status"] == "ALERT")
    logger.info(
        "event=complete scenarios=%d alerts=%d",
        len(scenarios), alert_count,
    )
    return scenarios


def print_report(scenarios: list) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    divider = "  " + "-" * 60
    print()
    print("  ┌──────────────────────────────────────────────────────┐")
    print("  │           FAILURE SIMULATION REPORT                  │")
    print("  └──────────────────────────────────────────────────────┘")
    print(f"  Timestamp : {ts}")
    print(f"  Scenarios : {len(scenarios)}")
    alert_count = sum(1 for s in scenarios if s["status"] == "ALERT")
    print(f"  Alerts    : {alert_count} / {len(scenarios)}")
    print()
    for i, s in enumerate(scenarios, 1):
        icon = "⚠️  ALERT" if s["status"] == "ALERT" else "✓   OK"
        print(divider)
        print(f"  [{i}] {s['scenario'].upper().replace('_', ' ')}")
        print(f"       Status  : {icon}")
        print(f"       Message : {s['message']}")
    print(divider)
    print()
    print(f"  Log written to: {_LOG_PATH}")
    print()


if __name__ == "__main__":
    results = run_all_scenarios()
    print_report(results)
    # All 3 scenarios are designed to produce ALERT; exit 0 = simulation ran correctly
    unexpected = [r for r in results if r["status"] != "ALERT"]
    sys.exit(1 if unexpected else 0)
