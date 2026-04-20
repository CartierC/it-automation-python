# tests/test_service_checker.py
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.service_checker import (
    ServiceCheckResult,
    ServiceEntry,
    _parse_launchctl_output,
    run_service_checks,
)

_LAUNCHCTL_OUTPUT = (
    "PID\tStatus\tLabel\n"
    "1234\t0\tcom.apple.Finder\n"
    "-\t0\tcom.apple.AirPlayXPCHelper\n"
    "5678\t0\tcom.apple.Safari.SafeBrowsing.Service\n"
    "-\t1\tcom.apple.some.dead.service\n"
)

_TARGET = [
    "com.apple.Finder",
    "com.apple.AirPlayXPCHelper",
    "com.apple.Safari.SafeBrowsing.Service",
]


# ── _parse_launchctl_output ───────────────────────────────────────────────────

def test_parse_returns_list_of_service_entries():
    entries = _parse_launchctl_output(_LAUNCHCTL_OUTPUT, _TARGET)
    assert isinstance(entries, list)
    assert all(isinstance(e, ServiceEntry) for e in entries)


def test_parse_skips_header_line():
    entries = _parse_launchctl_output(_LAUNCHCTL_OUTPUT, _TARGET)
    names = [e.name for e in entries]
    assert "PID" not in names
    assert "Label" not in names


def test_parse_healthy_when_pid_present():
    entries = _parse_launchctl_output(_LAUNCHCTL_OUTPUT, _TARGET)
    finder = next(e for e in entries if e.name == "com.apple.Finder")
    assert finder.healthy is True
    assert finder.pid == "1234"


def test_parse_unhealthy_when_pid_dash():
    entries = _parse_launchctl_output(_LAUNCHCTL_OUTPUT, _TARGET)
    airplay = next(e for e in entries if e.name == "com.apple.AirPlayXPCHelper")
    assert airplay.healthy is False
    assert airplay.pid == "-"


def test_parse_marks_target_services():
    entries = _parse_launchctl_output(_LAUNCHCTL_OUTPUT, _TARGET)
    targets = [e for e in entries if e.is_target]
    assert len(targets) == 3


# ── run_service_checks ────────────────────────────────────────────────────────

@patch("core.service_checker.subprocess.run")
def test_run_service_checks_returns_result(mock_run):
    mock_run.return_value = MagicMock(stdout=_LAUNCHCTL_OUTPUT, returncode=0)
    result = run_service_checks(target_services=_TARGET)
    assert isinstance(result, ServiceCheckResult)


@patch("core.service_checker.subprocess.run")
def test_run_service_checks_overall_ok_when_all_healthy(mock_run):
    output = (
        "PID\tStatus\tLabel\n"
        "1234\t0\tcom.apple.Finder\n"
        "2345\t0\tcom.apple.AirPlayXPCHelper\n"
        "5678\t0\tcom.apple.Safari.SafeBrowsing.Service\n"
    )
    mock_run.return_value = MagicMock(stdout=output, returncode=0)
    result = run_service_checks(target_services=_TARGET)
    assert result.overall == "OK"
    assert len(result.unhealthy) == 0


@patch("core.service_checker.subprocess.run")
def test_run_service_checks_overall_alert_on_unhealthy_target(mock_run):
    output = (
        "PID\tStatus\tLabel\n"
        "1234\t0\tcom.apple.Finder\n"
        "-\t0\tcom.apple.AirPlayXPCHelper\n"
        "5678\t0\tcom.apple.Safari.SafeBrowsing.Service\n"
    )
    mock_run.return_value = MagicMock(stdout=output, returncode=0)
    result = run_service_checks(target_services=_TARGET)
    assert result.overall == "ALERT"
    assert len(result.unhealthy) == 1
    assert result.unhealthy[0].name == "com.apple.AirPlayXPCHelper"


@patch("core.service_checker.subprocess.run")
def test_run_service_checks_missing_target_treated_as_unhealthy(mock_run):
    output = "PID\tStatus\tLabel\n1234\t0\tcom.apple.Finder\n"
    mock_run.return_value = MagicMock(stdout=output, returncode=0)
    result = run_service_checks(target_services=_TARGET)
    assert result.overall == "ALERT"
    missing = [s for s in result.targets if s.name != "com.apple.Finder"]
    assert all(not s.healthy for s in missing)


@patch("core.service_checker.subprocess.run")
def test_run_service_checks_handles_subprocess_error_gracefully(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, "launchctl", stderr="error")
    result = run_service_checks(target_services=_TARGET)
    assert isinstance(result, ServiceCheckResult)
    assert result.overall == "ALERT"


@patch("core.service_checker.subprocess.run")
def test_run_service_checks_has_required_fields(mock_run):
    mock_run.return_value = MagicMock(stdout=_LAUNCHCTL_OUTPUT, returncode=0)
    result = run_service_checks(target_services=_TARGET)
    assert result.timestamp
    assert result.target_names == _TARGET
    assert isinstance(result.services, list)
    assert isinstance(result.targets, list)
    assert isinstance(result.unhealthy, list)


@patch("core.service_checker.subprocess.run")
def test_service_entry_as_dict_has_required_keys(mock_run):
    output = "PID\tStatus\tLabel\n1234\t0\tcom.apple.Finder\n"
    mock_run.return_value = MagicMock(stdout=output, returncode=0)
    result = run_service_checks(target_services=["com.apple.Finder"])
    d = result.services[0].as_dict()
    for key in ("name", "pid", "exit_status", "is_target", "healthy"):
        assert key in d
