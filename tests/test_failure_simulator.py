# tests/test_failure_simulator.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.failure_simulator import (  # noqa: E402
    REQUIRED_THRESHOLD_KEYS,
    run_all_scenarios,
    simulate_config_validation_failure,
    simulate_disk_threshold_exceeded,
    simulate_missing_service,
)

_REQUIRED_RESULT_KEYS = {"scenario", "timestamp", "check", "status", "message"}


# ── simulate_disk_threshold_exceeded ──────────────────────────────────────────

def test_disk_scenario_returns_alert():
    result = simulate_disk_threshold_exceeded()
    assert result["status"] == "ALERT"


def test_disk_scenario_has_required_keys():
    result = simulate_disk_threshold_exceeded()
    assert _REQUIRED_RESULT_KEYS.issubset(result.keys())


def test_disk_scenario_simulated_value_exceeds_threshold():
    result = simulate_disk_threshold_exceeded()
    assert result["simulated_value"] > result["threshold"]


def test_disk_scenario_correct_scenario_name():
    result = simulate_disk_threshold_exceeded()
    assert result["scenario"] == "disk_threshold_exceeded"


def test_disk_scenario_message_is_not_empty():
    result = simulate_disk_threshold_exceeded()
    assert result["message"]


# ── simulate_missing_service ──────────────────────────────────────────────────

def test_missing_service_returns_alert():
    result = simulate_missing_service()
    assert result["status"] == "ALERT"


def test_missing_service_has_required_keys():
    result = simulate_missing_service()
    assert _REQUIRED_RESULT_KEYS.issubset(result.keys())


def test_missing_service_pid_is_dash():
    result = simulate_missing_service()
    assert result["pid"] == "-"


def test_missing_service_healthy_is_false():
    result = simulate_missing_service()
    assert result["healthy"] is False


def test_missing_service_correct_scenario_name():
    result = simulate_missing_service()
    assert result["scenario"] == "missing_service"


def test_missing_service_message_is_not_empty():
    result = simulate_missing_service()
    assert result["message"]


# ── simulate_config_validation_failure ────────────────────────────────────────

def test_config_validation_returns_alert():
    result = simulate_config_validation_failure()
    assert result["status"] == "ALERT"


def test_config_validation_has_required_keys():
    result = simulate_config_validation_failure()
    assert _REQUIRED_RESULT_KEYS.issubset(result.keys())


def test_config_validation_missing_keys_not_empty():
    result = simulate_config_validation_failure()
    assert len(result["missing_keys"]) > 0


def test_config_validation_missing_keys_are_known_required_keys():
    result = simulate_config_validation_failure()
    for key in result["missing_keys"]:
        assert key in REQUIRED_THRESHOLD_KEYS


def test_config_validation_correct_scenario_name():
    result = simulate_config_validation_failure()
    assert result["scenario"] == "config_validation_failure"


# ── run_all_scenarios ─────────────────────────────────────────────────────────

def test_run_all_scenarios_returns_three_results():
    results = run_all_scenarios()
    assert len(results) == 3


def test_run_all_scenarios_all_alert():
    results = run_all_scenarios()
    for r in results:
        assert r["status"] == "ALERT", f"Expected ALERT for {r['scenario']}"


def test_run_all_scenarios_unique_scenario_names():
    results = run_all_scenarios()
    names = [r["scenario"] for r in results]
    assert len(names) == len(set(names)), "Duplicate scenario names detected"


def test_run_all_scenarios_all_have_timestamps():
    results = run_all_scenarios()
    for r in results:
        assert r["timestamp"], f"Missing timestamp in {r['scenario']}"


def test_run_all_scenarios_all_have_messages():
    results = run_all_scenarios()
    for r in results:
        assert r["message"], f"Empty message in {r['scenario']}"
