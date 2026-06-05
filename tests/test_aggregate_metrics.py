# tests/test_aggregate_metrics.py
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.aggregate_metrics import aggregate, format_summary, load_reports


_REPORT_OK = {
    "generated_at": "2026-05-20 14:12:14",
    "overall": "OK",
    "health_check": {
        "overall": "OK",
        "hostname": "test-host",
        "platform": "Linux",
        "metrics": [
            {
                "name": "CPU Usage",
                "value": 20.0,
                "threshold": 80.0,
                "crit_threshold": 95.0,
                "unit": "%",
                "status": "OK",
            },
            {
                "name": "Memory",
                "value": 40.0,
                "threshold": 80.0,
                "crit_threshold": 95.0,
                "unit": "%",
                "status": "OK",
            },
        ],
    },
    "process_monitor": {
        "overall": "OK",
        "cpu_threshold": 50.0,
        "zombie_count": 0,
        "flagged_count": 0,
        "processes": [],
    },
    "service_checker": {
        "overall": "OK",
        "target_count": 2,
        "unhealthy_count": 0,
        "services": [],
    },
}

_REPORT_WARNING = {**_REPORT_OK, "overall": "WARNING"}
_REPORT_CRITICAL = {**_REPORT_OK, "overall": "CRITICAL"}


# ── load_reports ──────────────────────────────────────────────────────────────


def test_load_reports_empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = load_reports(Path(tmpdir))
    assert result == []


def test_load_reports_reads_matching_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "report_2026-05-20_140000.json"
        p.write_text(json.dumps(_REPORT_OK))
        result = load_reports(Path(tmpdir))
    assert len(result) == 1
    assert result[0]["overall"] == "OK"


def test_load_reports_skips_invalid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "report_2026-05-20_140000.json"
        p.write_text("not valid {{{")
        result = load_reports(Path(tmpdir))
    assert result == []


def test_load_reports_ignores_non_report_prefix():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "report_2026-05-20_140000.json").write_text(
            json.dumps(_REPORT_OK)
        )
        (Path(tmpdir) / "other_log.json").write_text(json.dumps(_REPORT_OK))
        result = load_reports(Path(tmpdir))
    assert len(result) == 1


def test_load_reports_sorted_order():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "report_2026-05-20_120000.json").write_text(
            json.dumps({**_REPORT_OK, "generated_at": "2026-05-20 12:00:00"})
        )
        (Path(tmpdir) / "report_2026-05-20_130000.json").write_text(
            json.dumps({**_REPORT_OK, "generated_at": "2026-05-20 13:00:00"})
        )
        result = load_reports(Path(tmpdir))
    assert result[0]["generated_at"] == "2026-05-20 12:00:00"
    assert result[1]["generated_at"] == "2026-05-20 13:00:00"


# ── aggregate ─────────────────────────────────────────────────────────────────


def test_aggregate_empty_returns_zero_runs():
    result = aggregate([])
    assert result["total_runs"] == 0


def test_aggregate_counts_total_runs():
    result = aggregate([_REPORT_OK, _REPORT_OK])
    assert result["total_runs"] == 2


def test_aggregate_pass_rate_all_ok():
    result = aggregate([_REPORT_OK, _REPORT_OK])
    assert result["pass_rate"] == 100.0


def test_aggregate_pass_rate_half_ok():
    result = aggregate([_REPORT_OK, _REPORT_WARNING])
    assert result["pass_rate"] == 50.0


def test_aggregate_pass_rate_none_ok():
    result = aggregate([_REPORT_WARNING, _REPORT_CRITICAL])
    assert result["pass_rate"] == 0.0


def test_aggregate_severity_counts_single():
    result = aggregate([_REPORT_OK])
    assert result["severity_counts"] == {"OK": 1}


def test_aggregate_severity_counts_mixed():
    result = aggregate([_REPORT_OK, _REPORT_WARNING, _REPORT_CRITICAL])
    assert result["severity_counts"]["OK"] == 1
    assert result["severity_counts"]["WARNING"] == 1
    assert result["severity_counts"]["CRITICAL"] == 1


def test_aggregate_metric_statuses_tracked():
    result = aggregate([_REPORT_OK])
    assert result["metric_statuses"].get("CPU Usage:OK") == 1
    assert result["metric_statuses"].get("Memory:OK") == 1


def test_aggregate_metric_statuses_accumulate():
    result = aggregate([_REPORT_OK, _REPORT_OK])
    assert result["metric_statuses"].get("CPU Usage:OK") == 2


def test_aggregate_missing_health_check_key():
    bare = {"generated_at": "2026-05-20", "overall": "OK"}
    result = aggregate([bare])
    assert result["total_runs"] == 1
    assert result["metric_statuses"] == {}


# ── format_summary ────────────────────────────────────────────────────────────


def test_format_summary_no_reports():
    result = format_summary({"total_runs": 0})
    assert "No reports" in result


def test_format_summary_includes_total_count():
    stats = aggregate([_REPORT_OK, _REPORT_WARNING])
    result = format_summary(stats)
    assert "2" in result


def test_format_summary_includes_pass_rate():
    stats = aggregate([_REPORT_OK])
    result = format_summary(stats)
    assert "100.0" in result


def test_format_summary_shows_ok_severity():
    stats = aggregate([_REPORT_OK, _REPORT_WARNING])
    result = format_summary(stats)
    assert "OK" in result


def test_format_summary_shows_warning_severity():
    stats = aggregate([_REPORT_OK, _REPORT_WARNING])
    result = format_summary(stats)
    assert "WARNING" in result


def test_format_summary_is_string():
    stats = aggregate([_REPORT_OK])
    result = format_summary(stats)
    assert isinstance(result, str)
