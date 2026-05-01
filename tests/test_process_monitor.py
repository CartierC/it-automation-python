# tests/test_process_monitor.py
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.process_monitor import (
    ProcessEntry,
    ProcessMonitorResult,
    get_top_processes,
    run_process_monitor,
)


def _make_proc(pid: int, name: str, cpu: float, mem: float, status: str) -> MagicMock:
    proc = MagicMock()
    proc.info = {
        "pid": pid,
        "name": name,
        "cpu_percent": cpu,
        "memory_percent": mem,
        "status": status,
    }
    proc.cpu_percent.return_value = cpu
    return proc


def _proc_iter_factory(procs):
    """Return a fresh iterator on every call — handles two-pass sampling."""
    return lambda *args, **kwargs: iter(procs)


# ── get_top_processes ─────────────────────────────────────────────────────────

@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_get_top_processes_returns_list(mock_iter, mock_sleep):
    procs = [_make_proc(1, "python", 20.0, 2.0, "running")]
    mock_iter.side_effect = _proc_iter_factory(procs)
    entries = get_top_processes(top_n=5)
    assert isinstance(entries, list)


@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_get_top_processes_returns_process_entries(mock_iter, mock_sleep):
    procs = [_make_proc(1, "python", 20.0, 2.0, "running")]
    mock_iter.side_effect = _proc_iter_factory(procs)
    entries = get_top_processes(top_n=5)
    assert all(isinstance(e, ProcessEntry) for e in entries)


@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_get_top_processes_respects_top_n(mock_iter, mock_sleep):
    procs = [_make_proc(i, f"proc{i}", float(i), 1.0, "running") for i in range(1, 8)]
    mock_iter.side_effect = _proc_iter_factory(procs)
    entries = get_top_processes(top_n=3)
    assert len(entries) == 3


@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_get_top_processes_sorted_by_cpu_descending(mock_iter, mock_sleep):
    procs = [
        _make_proc(1, "low",  5.0,  1.0, "running"),
        _make_proc(2, "high", 40.0, 1.0, "running"),
        _make_proc(3, "mid",  20.0, 1.0, "running"),
    ]
    mock_iter.side_effect = _proc_iter_factory(procs)
    entries = get_top_processes(top_n=3)
    cpu_values = [e.cpu_percent for e in entries]
    assert cpu_values == sorted(cpu_values, reverse=True)


@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_get_top_processes_empty_list(mock_iter, mock_sleep):
    mock_iter.side_effect = _proc_iter_factory([])
    entries = get_top_processes(top_n=10)
    assert entries == []


# ── zombie detection ──────────────────────────────────────────────────────────

@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_zombie_process_is_detected(mock_iter, mock_sleep):
    procs = [_make_proc(999, "defunct", 0.0, 0.0, "zombie")]
    mock_iter.side_effect = _proc_iter_factory(procs)
    entries = get_top_processes(top_n=5)
    assert entries[0].is_zombie is True


@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_zombie_process_is_flagged(mock_iter, mock_sleep):
    procs = [_make_proc(999, "defunct", 0.0, 0.0, "zombie")]
    mock_iter.side_effect = _proc_iter_factory(procs)
    entries = get_top_processes(top_n=5)
    assert entries[0].flagged is True


@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_running_process_is_not_zombie(mock_iter, mock_sleep):
    procs = [_make_proc(1, "python", 10.0, 2.0, "running")]
    mock_iter.side_effect = _proc_iter_factory(procs)
    entries = get_top_processes(top_n=5)
    assert entries[0].is_zombie is False


# ── threshold breach ──────────────────────────────────────────────────────────

@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_cpu_threshold_breach_is_flagged(mock_iter, mock_sleep):
    procs = [_make_proc(100, "runaway", 90.0, 5.0, "running")]
    mock_iter.side_effect = _proc_iter_factory(procs)
    entries = get_top_processes(top_n=5)
    assert entries[0].flagged is True
    assert entries[0].cpu_percent == 90.0


@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_cpu_below_threshold_not_flagged(mock_iter, mock_sleep):
    procs = [_make_proc(1, "normal", 10.0, 2.0, "running")]
    mock_iter.side_effect = _proc_iter_factory(procs)
    entries = get_top_processes(top_n=5)
    assert entries[0].flagged is False


@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_process_entry_as_dict_has_required_keys(mock_iter, mock_sleep):
    procs = [_make_proc(1, "python", 10.0, 2.0, "running")]
    mock_iter.side_effect = _proc_iter_factory(procs)
    entries = get_top_processes(top_n=1)
    d = entries[0].as_dict()
    for key in ("pid", "name", "cpu_percent", "mem_percent", "status", "flagged", "is_zombie"):
        assert key in d


# ── run_process_monitor ───────────────────────────────────────────────────────

@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_run_process_monitor_returns_result(mock_iter, mock_sleep):
    procs = [_make_proc(1, "python", 10.0, 2.0, "running")]
    mock_iter.side_effect = _proc_iter_factory(procs)
    result = run_process_monitor(top_n=1)
    assert isinstance(result, ProcessMonitorResult)


@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_run_process_monitor_overall_ok_when_clean(mock_iter, mock_sleep):
    procs = [_make_proc(1, "python", 10.0, 2.0, "running")]
    mock_iter.side_effect = _proc_iter_factory(procs)
    result = run_process_monitor(top_n=1)
    assert result.overall == "OK"


@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_run_process_monitor_overall_alert_on_zombie(mock_iter, mock_sleep):
    procs = [_make_proc(999, "defunct", 0.0, 0.0, "zombie")]
    mock_iter.side_effect = _proc_iter_factory(procs)
    result = run_process_monitor(top_n=5)
    assert result.overall == "ALERT"
    assert len(result.zombies) == 1


@patch("time.sleep")
@patch("core.process_monitor.psutil.process_iter")
def test_run_process_monitor_overall_alert_on_threshold_breach(mock_iter, mock_sleep):
    procs = [_make_proc(100, "runaway", 90.0, 5.0, "running")]
    mock_iter.side_effect = _proc_iter_factory(procs)
    result = run_process_monitor(top_n=5)
    assert result.overall == "ALERT"
    assert len(result.flagged) == 1
