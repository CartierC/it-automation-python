# Operations Runbook — IT Automation Toolkit

**Repo:** `it-automation-python`  
**Author:** CartierC  
**Last updated:** 2026-04-20

---

## Overview

This runbook covers day-to-day operation, configuration, troubleshooting, and escalation procedures for the IT Automation Python toolkit. The toolkit performs automated system health checks, process monitoring, and macOS service validation with structured logging and JSON reporting.

---

## Components

| Component | Script | Log | Description |
|---|---|---|---|
| System Health Check | `scripts/run_health_check.py` | `logs/health_check.log` | CPU, memory, and disk utilization vs. configured thresholds |
| Process Monitor | `scripts/run_process_monitor.py` | `logs/process_monitor.log` | Top-N CPU consumers, zombie detection, threshold breach flagging |
| Service Checker | `scripts/run_service_checker.py` | `logs/service_checker.log` | macOS launchd service health via `launchctl list` |
| Combined Runner | `scripts/run_all_checks.py` | `logs/report_YYYY-MM-DD_HHMMSS.json` | Runs all checks and writes a timestamped JSON report |

---

## Quick Start

```bash
# Install dependencies
make install

# Run all checks + write JSON report
make all

# Run individual checks
make health
make processes
make services

# Run test suite
make test
```

---

## Configuration

### Threshold Configuration

Edit `config/thresholds.json` — no code changes required:

```json
{
  "cpu_percent": 85,
  "memory_percent": 80,
  "disk_percent": 90
}
```

| Field | Default | Description |
|---|---|---|
| `cpu_percent` | `85` | CPU utilization % that triggers ALERT |
| `memory_percent` | `80` | RAM utilization % that triggers ALERT |
| `disk_percent` | `90` | Disk utilization % that triggers ALERT |

### Process and Service Configuration

Edit `config/settings.py`:

```python
PROCESS_CPU_THRESHOLD = 50.0   # flag any process exceeding this CPU %
PROCESS_TOP_N         = 10     # default number of top processes to display

TARGET_SERVICES = [
    "com.apple.Finder",
    "com.apple.Safari.SafeBrowsing.Service",
]
```

To monitor additional macOS services, add their `launchctl` service names to `TARGET_SERVICES`.

---

## Running the Checks

### Health Check

```bash
# Human-readable output
python scripts/run_health_check.py

# JSON output (for pipelines, dashboards)
python scripts/run_health_check.py --json

# Quiet mode — exits 0 for OK, 1 for ALERT
python scripts/run_health_check.py --quiet
```

**Exit codes:**

| Code | Meaning |
|---|---|
| `0` | All metrics within thresholds |
| `1` | One or more thresholds breached |

### Process Monitor

```bash
# Default (top 10 by CPU)
python scripts/run_process_monitor.py

# Show top 20
python scripts/run_process_monitor.py --top 20

# JSON output
python scripts/run_process_monitor.py --json

# Terminate a process (prompts for confirmation)
python scripts/run_process_monitor.py --kill <PID>
```

### Service Checker

```bash
# Show configured target services only
python scripts/run_service_checker.py

# Show all detected services
python scripts/run_service_checker.py --all

# JSON output
python scripts/run_service_checker.py --json
```

### Combined Report

```bash
python scripts/run_all_checks.py
```

Writes `logs/report_YYYY-MM-DD_HHMMSS.json` with full health, process, and service data.

---

## Scheduled Automation (Cron)

```cron
# Run every 15 minutes and append to automation log
*/15 * * * * cd ~/Projects/Automation/it-automation-python && .venv/bin/python scripts/run_all_checks.py >> /tmp/automation.log 2>&1
```

To install: `crontab -e`

To verify: `crontab -l`

---

## Alert Response Procedures

### CPU ALERT

1. Confirm the reading:
   ```bash
   python scripts/run_process_monitor.py --top 20
   ```
2. Identify the flagged process (listed under `Flagged` in the output).
3. Investigate: is it a legitimate spike (build job, backup) or runaway process?
4. If runaway, terminate safely:
   ```bash
   python scripts/run_process_monitor.py --kill <PID>
   ```
5. Confirm CPU returns below threshold on next health check run.

### Memory ALERT

1. Check current memory usage:
   ```bash
   python scripts/run_health_check.py
   ```
2. Review process memory consumers:
   ```bash
   python scripts/run_process_monitor.py --json | python3 -c "import json,sys; [print(p['name'], p['mem_percent']) for p in json.load(sys.stdin)['processes']]"
   ```
3. Clear caches or restart high-memory processes as appropriate.
4. If persistent, consider adjusting `memory_percent` threshold in `config/thresholds.json`.

### Disk ALERT

1. Identify the disk path breaching threshold (check `check_disk` in logs).
2. Investigate large files: `du -sh /* | sort -rh | head -20`
3. Clear log archives, temp files, or caches as appropriate.
4. Update `disk_percent` in `config/thresholds.json` only if the new baseline is intentional.

### Service UNHEALTHY

1. Identify which service is flagged:
   ```bash
   python scripts/run_service_checker.py
   ```
2. Check if the service is expected to be running on this host.
3. Attempt to restart (macOS):
   ```bash
   launchctl start <service-name>
   ```
4. If the service legitimately does not exist on this host, remove it from `TARGET_SERVICES` in `config/settings.py`.
5. Re-run the service checker to confirm resolution.

### Zombie Processes

Zombie processes appear in the process monitor with `STATUS = zombie`. These are usually safe — the parent process has not yet reaped the child. If zombie count increases over time:

1. Identify the parent: `ps -ef | grep <zombie-PID>`
2. Restart the parent process if it is unresponsive.
3. Only escalate if zombie count exceeds 10 or if the parent is a critical system service.

---

## Log Reference

| Log File | Format | Rotated? |
|---|---|---|
| `logs/health_check.log` | `YYYY-MM-DD HH:MM:SS  LEVEL  message` | No — append only |
| `logs/process_monitor.log` | `YYYY-MM-DD HH:MM:SS  LEVEL  message` | No — append only |
| `logs/service_checker.log` | `YYYY-MM-DD HH:MM:SS  LEVEL  message` | No — append only |
| `logs/report_YYYY-MM-DD_HHMMSS.json` | JSON | One file per run |

To clear all logs:
```bash
make clean
```

---

## Zero-Dependency Quick Check

For environments where psutil cannot be installed:

```bash
python tools/health_check.py
```

Uses only stdlib (`os`, `platform`, `shutil`) — no installation required.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: psutil` | Virtual environment not activated or dependencies not installed | `make install` then re-run |
| `launchctl not found` | Not running on macOS | Service checker is macOS-only; use `--json` flag to consume data programmatically on other platforms |
| `FileNotFoundError: logs/` | Logs directory missing | Create it: `mkdir -p logs` |
| All metrics read `0.0` | First psutil poll always returns 0 — two-pass sampling required | This is handled automatically by the process monitor; if seen in tests, check mock setup |
| `Permission denied` when killing a process | Process is owned by root or a system user | Re-run with `sudo` or escalate to sysadmin |

---

## Development

### Running Tests

```bash
make test
# or
pytest tests/ -v
```

44 tests across 3 modules. All tests use mocks — no real system calls, no network, no flakiness.

### Adding a New Check

1. Add logic to an existing module in `core/` or create a new one.
2. Add configuration constants to `config/settings.py`.
3. Create a CLI entry point in `scripts/`.
4. Write unit tests in `tests/` using `pytest-mock`.
5. Add a `make` target in `Makefile`.
6. Document the new check in this runbook and in `README.md`.

---

## Contact

Raise issues or improvements at:  
[https://github.com/CartierC/it-automation-python/issues](https://github.com/CartierC/it-automation-python/issues)
