# tests/test_config_validation.py
#
# Validates that config/thresholds.json and config/settings.py contain
# the expected keys, types, and operationally sane values. These tests
# catch config drift without requiring a live system.
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import (  # noqa: E402
    PROCESS_CPU_THRESHOLD,
    PROCESS_TOP_N,
    TARGET_SERVICES,
)

_THRESHOLDS_PATH = Path(__file__).resolve().parents[1] / "config" / "thresholds.json"
_REQUIRED_THRESHOLD_KEYS = {"cpu_percent", "memory_percent", "disk_percent"}


# ── thresholds.json ───────────────────────────────────────────────────────────

def test_thresholds_file_exists():
    assert _THRESHOLDS_PATH.exists(), "config/thresholds.json not found"


def test_thresholds_file_is_valid_json():
    data = json.loads(_THRESHOLDS_PATH.read_text())
    assert isinstance(data, dict)


def test_thresholds_has_all_required_keys():
    data = json.loads(_THRESHOLDS_PATH.read_text())
    missing = _REQUIRED_THRESHOLD_KEYS - data.keys()
    assert not missing, f"thresholds.json missing required keys: {missing}"


def test_thresholds_values_are_numeric():
    data = json.loads(_THRESHOLDS_PATH.read_text())
    for key in _REQUIRED_THRESHOLD_KEYS:
        assert isinstance(data[key], (int, float)), (
            f"threshold '{key}' must be numeric, got {type(data[key])}"
        )


def test_thresholds_values_are_positive():
    data = json.loads(_THRESHOLDS_PATH.read_text())
    for key in _REQUIRED_THRESHOLD_KEYS:
        assert data[key] > 0, f"threshold '{key}' must be > 0"


def test_thresholds_values_are_below_100():
    data = json.loads(_THRESHOLDS_PATH.read_text())
    for key in _REQUIRED_THRESHOLD_KEYS:
        assert data[key] <= 100, (
            f"threshold '{key}' = {data[key]} is not a valid percentage"
        )


def test_cpu_threshold_is_operationally_sane():
    data = json.loads(_THRESHOLDS_PATH.read_text())
    assert 50 <= data["cpu_percent"] <= 99, (
        "cpu_percent threshold should be between 50 and 99 for operational use"
    )


def test_memory_threshold_is_operationally_sane():
    data = json.loads(_THRESHOLDS_PATH.read_text())
    assert 50 <= data["memory_percent"] <= 99, (
        "memory_percent threshold should be between 50 and 99 for operational use"
    )


def test_disk_threshold_is_operationally_sane():
    data = json.loads(_THRESHOLDS_PATH.read_text())
    assert 50 <= data["disk_percent"] <= 99, (
        "disk_percent threshold should be between 50 and 99 for operational use"
    )


# ── config/settings.py ────────────────────────────────────────────────────────

def test_process_cpu_threshold_is_float():
    assert isinstance(PROCESS_CPU_THRESHOLD, float)


def test_process_cpu_threshold_is_positive():
    assert PROCESS_CPU_THRESHOLD > 0


def test_process_cpu_threshold_is_below_100():
    assert PROCESS_CPU_THRESHOLD < 100


def test_process_top_n_is_positive_int():
    assert isinstance(PROCESS_TOP_N, int)
    assert PROCESS_TOP_N > 0


def test_target_services_is_list():
    assert isinstance(TARGET_SERVICES, list)


def test_target_services_all_strings():
    assert all(isinstance(s, str) for s in TARGET_SERVICES)


def test_target_services_no_empty_strings():
    assert all(s.strip() for s in TARGET_SERVICES)
