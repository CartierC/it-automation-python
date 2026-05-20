# tests/test_health_check.py
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import TEST_CPU_MOCK_VALUE, TEST_DISK_MOCK_VALUE, TEST_MEM_MOCK_VALUE
from core.system_health import (
    HealthCheckResult,
    MetricResult,
    check_cpu,
    check_disk,
    check_memory,
    run_health_check,
)


# ── check_cpu ─────────────────────────────────────────────────────────────────

@patch("core.system_health.psutil.cpu_percent", return_value=TEST_CPU_MOCK_VALUE)
def test_check_cpu_returns_metric_result(mock_cpu):
    result = check_cpu(warn_threshold=80.0, crit_threshold=95.0)
    assert isinstance(result, MetricResult)


@patch("core.system_health.psutil.cpu_percent", return_value=TEST_CPU_MOCK_VALUE)
def test_check_cpu_correct_value(mock_cpu):
    result = check_cpu(warn_threshold=80.0, crit_threshold=95.0)
    assert result.name == "CPU Usage"
    assert result.value == TEST_CPU_MOCK_VALUE
    assert result.warn_threshold == 80.0
    assert result.crit_threshold == 95.0
    assert result.unit == "%"


@patch("core.system_health.psutil.cpu_percent", return_value=TEST_CPU_MOCK_VALUE)
def test_check_cpu_status_ok_below_threshold(mock_cpu):
    result = check_cpu(warn_threshold=80.0, crit_threshold=95.0)
    assert result.status == "OK"


@patch("core.system_health.psutil.cpu_percent", return_value=92.0)
def test_check_cpu_status_alert_above_threshold(mock_cpu):
    # 92.0 > warn(80) but < crit(95) → WARNING
    result = check_cpu(warn_threshold=80.0, crit_threshold=95.0)
    assert result.status == "WARNING"


@patch("core.system_health.psutil.cpu_percent", return_value=85.0)
def test_check_cpu_status_alert_at_threshold(mock_cpu):
    # 85.0 > warn(80) but < crit(95) → WARNING
    result = check_cpu(warn_threshold=80.0, crit_threshold=95.0)
    assert result.status == "WARNING"


@patch("core.system_health.psutil.cpu_percent", return_value=95.0)
def test_check_cpu_status_critical_at_crit_threshold(mock_cpu):
    result = check_cpu(warn_threshold=80.0, crit_threshold=95.0)
    assert result.status == "CRITICAL"


# ── check_memory ──────────────────────────────────────────────────────────────

@patch("core.system_health.psutil.virtual_memory")
def test_check_memory_returns_metric_result(mock_mem):
    mock_mem.return_value = MagicMock(percent=TEST_MEM_MOCK_VALUE, total=16 * 1024 ** 3, used=8 * 1024 ** 3)
    result = check_memory(warn_threshold=80.0, crit_threshold=95.0)
    assert isinstance(result, MetricResult)


@patch("core.system_health.psutil.virtual_memory")
def test_check_memory_correct_value(mock_mem):
    mock_mem.return_value = MagicMock(percent=TEST_MEM_MOCK_VALUE, total=16 * 1024 ** 3, used=8 * 1024 ** 3)
    result = check_memory(warn_threshold=80.0, crit_threshold=95.0)
    assert result.name == "Memory"
    assert result.value == TEST_MEM_MOCK_VALUE
    assert result.warn_threshold == 80.0
    assert result.unit == "%"


@patch("core.system_health.psutil.virtual_memory")
def test_check_memory_status_ok(mock_mem):
    mock_mem.return_value = MagicMock(percent=TEST_MEM_MOCK_VALUE, total=16 * 1024 ** 3, used=8 * 1024 ** 3)
    result = check_memory(warn_threshold=80.0, crit_threshold=95.0)
    assert result.status == "OK"


@patch("core.system_health.psutil.virtual_memory")
def test_check_memory_status_alert(mock_mem):
    mock_mem.return_value = MagicMock(percent=88.0, total=16 * 1024 ** 3, used=12 * 1024 ** 3)
    result = check_memory(warn_threshold=80.0, crit_threshold=95.0)
    assert result.status == "WARNING"


# ── check_disk ────────────────────────────────────────────────────────────────

@patch("core.system_health.psutil.disk_usage")
def test_check_disk_returns_metric_result(mock_disk):
    mock_disk.return_value = MagicMock(percent=TEST_DISK_MOCK_VALUE, total=500 * 1024 ** 3)
    result = check_disk(warn_threshold=85.0, crit_threshold=95.0)
    assert isinstance(result, MetricResult)


@patch("core.system_health.psutil.disk_usage")
def test_check_disk_correct_value(mock_disk):
    mock_disk.return_value = MagicMock(percent=TEST_DISK_MOCK_VALUE, total=500 * 1024 ** 3)
    result = check_disk(warn_threshold=85.0, crit_threshold=95.0)
    assert result.name == "Disk Usage"
    assert result.value == TEST_DISK_MOCK_VALUE
    assert result.warn_threshold == 85.0
    assert result.unit == "%"


@patch("core.system_health.psutil.disk_usage")
def test_check_disk_status_ok(mock_disk):
    mock_disk.return_value = MagicMock(percent=TEST_DISK_MOCK_VALUE, total=500 * 1024 ** 3)
    result = check_disk(warn_threshold=85.0, crit_threshold=95.0)
    assert result.status == "OK"


@patch("core.system_health.psutil.disk_usage")
def test_check_disk_status_alert(mock_disk):
    # 95.0 >= crit(95) → CRITICAL
    mock_disk.return_value = MagicMock(percent=95.0, total=500 * 1024 ** 3)
    result = check_disk(warn_threshold=85.0, crit_threshold=95.0)
    assert result.status == "CRITICAL"


# ── run_health_check ──────────────────────────────────────────────────────────

@patch("core.system_health.psutil.cpu_percent", return_value=TEST_CPU_MOCK_VALUE)
@patch("core.system_health.psutil.virtual_memory")
@patch("core.system_health.psutil.disk_usage")
def test_run_health_check_returns_health_check_result(mock_disk, mock_mem, mock_cpu):
    mock_mem.return_value = MagicMock(percent=TEST_MEM_MOCK_VALUE, total=16 * 1024 ** 3, used=8 * 1024 ** 3)
    mock_disk.return_value = MagicMock(percent=TEST_DISK_MOCK_VALUE, total=500 * 1024 ** 3)
    result = run_health_check()
    assert isinstance(result, HealthCheckResult)


@patch("core.system_health.psutil.cpu_percent", return_value=TEST_CPU_MOCK_VALUE)
@patch("core.system_health.psutil.virtual_memory")
@patch("core.system_health.psutil.disk_usage")
def test_run_health_check_has_required_fields(mock_disk, mock_mem, mock_cpu):
    mock_mem.return_value = MagicMock(percent=TEST_MEM_MOCK_VALUE, total=16 * 1024 ** 3, used=8 * 1024 ** 3)
    mock_disk.return_value = MagicMock(percent=TEST_DISK_MOCK_VALUE, total=500 * 1024 ** 3)
    result = run_health_check()
    assert result.overall in ("OK", "WARNING", "CRITICAL")
    assert result.hostname
    assert result.platform
    assert result.timestamp
    assert len(result.metrics) == 3


@patch("core.system_health.psutil.cpu_percent", return_value=TEST_CPU_MOCK_VALUE)
@patch("core.system_health.psutil.virtual_memory")
@patch("core.system_health.psutil.disk_usage")
def test_run_health_check_overall_ok_when_all_clear(mock_disk, mock_mem, mock_cpu):
    mock_mem.return_value = MagicMock(percent=TEST_MEM_MOCK_VALUE, total=16 * 1024 ** 3, used=8 * 1024 ** 3)
    mock_disk.return_value = MagicMock(percent=TEST_DISK_MOCK_VALUE, total=500 * 1024 ** 3)
    result = run_health_check()
    assert result.overall == "OK"


@patch("core.system_health.psutil.cpu_percent", return_value=96.0)
@patch("core.system_health.psutil.virtual_memory")
@patch("core.system_health.psutil.disk_usage")
def test_run_health_check_overall_alert_on_breach(mock_disk, mock_mem, mock_cpu):
    # 96.0 >= cpu_crit(95) → CRITICAL
    mock_mem.return_value = MagicMock(percent=TEST_MEM_MOCK_VALUE, total=16 * 1024 ** 3, used=8 * 1024 ** 3)
    mock_disk.return_value = MagicMock(percent=TEST_DISK_MOCK_VALUE, total=500 * 1024 ** 3)
    result = run_health_check()
    assert result.overall == "CRITICAL"
