# IT Automation — Python

Python-based IT automation toolkit built to demonstrate operational scripting, service validation, logging, health checks, and test-driven workflow discipline.

## What This Project Covers
- System health checks
- Service validation logic
- Structured logging
- CLI-driven automation
- Testing and maintainable project structure

## Why This Matters
This project shows practical Python use in IT and operations environments where reliability, observability, and repeatable execution are required.
---

## Quick Start

```bash
make install   # create .venv and install dependencies
make all       # run all checks (health + processes + services)
make test      # run the full pytest suite
```

---

## What It Does

Polls CPU, Memory, and Disk utilization on any Mac or Linux host. Compares live readings against configurable thresholds and emits a pass/fail result — either human-readable to the terminal or JSON for pipeline consumption. Every run is logged to `logs/health_check.log` with timestamps.

---

## Project Structure

```
it-automation-python/
├── core/
│   ├── __init__.py
│   ├── system_health.py       # Health logic — CPU, memory, disk checks
│   ├── process_monitor.py     # Process logic — top-N, zombies, threshold flags
│   └── service_checker.py     # launchd service health via launchctl
├── scripts/
│   ├── run_health_check.py    # CLI: system health check
│   ├── run_process_monitor.py # CLI: process monitor
│   ├── run_service_checker.py # CLI: macOS service checker
│   └── run_all_checks.py      # CLI: combined runner + JSON report
├── tests/
│   ├── __init__.py
│   ├── test_health_check.py   # 17 tests — all mocked, no real psutil calls
│   ├── test_process_monitor.py# 16 tests — two-pass mock, zombie + threshold
│   └── test_service_checker.py# 11 tests — subprocess mock, CalledProcessError
├── tools/
│   └── health_check.py        # Stdlib-only quick check (zero dependencies)
├── config/
│   ├── thresholds.json        # Health check alert thresholds
│   └── settings.py            # Process + service constants + test mock values
├── logs/
│   ├── health_check.log       # Auto-created on first run
│   ├── process_monitor.log    # Auto-created on first run
│   ├── service_checker.log    # Auto-created on first run
│   └── report_YYYY-MM-DD_HHMMSS.json  # Combined report per run
├── docs/
│   └── runbook.md
├── Makefile                   # make install | health | processes | services | all | test | clean
├── requirements.txt
└── .gitignore
```

---

## Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/CartierC/it-automation-python.git
cd it-automation-python

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Standard run (human-readable)
```bash
python scripts/run_health_check.py
```

### Quiet mode — returns OK or ALERT only
```bash
python scripts/run_health_check.py --quiet
```

### JSON output — for pipelines, Slack bots, dashboards
```bash
python scripts/run_health_check.py --json
```

### Zero-dependency quick check (no install required)
```bash
python tools/health_check.py
```

---

## Example Output

```
  Host      : macbook-pro.local
  Platform  : Darwin 24.3.0
  Timestamp : 2026-04-20 14:32:11
  Overall   : OK

  Metrics:
    ✓  CPU Usage      12.4%  (threshold: 85%)  [OK]
    ✓  Memory         61.2%  (threshold: 80%)  [OK]
    ✓  Disk Usage     48.7%  (threshold: 90%)  [OK]
```

When a threshold is breached:
```
    ⚠️  CPU Usage      91.3%  (threshold: 85%)  [ALERT]
```

### JSON output (`--json`)
```json
{
  "hostname": "macbook-pro.local",
  "platform": "Darwin 24.3.0",
  "timestamp": "2026-04-20 14:32:11",
  "overall": "OK",
  "metrics": [
    { "name": "CPU Usage", "value": 12.4, "threshold": 85.0, "unit": "%", "status": "OK" },
    { "name": "Memory",    "value": 61.2, "threshold": 80.0, "unit": "%", "status": "OK" },
    { "name": "Disk Usage","value": 48.7, "threshold": 90.0, "unit": "%", "status": "OK" }
  ]
}
```

---

## Configuration

Edit `config/thresholds.json` to adjust alert thresholds — no code changes needed:

```json
{
  "cpu_percent": 85,
  "memory_percent": 80,
  "disk_percent": 90
}
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0`  | All metrics within thresholds |
| `1`  | One or more thresholds breached |

Designed for use in CI pipelines, cron jobs, and monitoring scripts.

---

## Logging

All runs append to `logs/health_check.log`:

```
2026-04-20 14:32:10  INFO      Starting health check on macbook-pro.local
2026-04-20 14:32:11  INFO      CPU check — 12.4% (threshold 85%) [OK]
2026-04-20 14:32:11  INFO      Memory check — 61.2% used of 16.0GB (threshold 80%) [OK]
2026-04-20 14:32:11  INFO      Disk check — 48.7% used of 500.0GB at / (threshold 90%) [OK]
2026-04-20 14:32:11  INFO      Health check complete — overall status: OK
```

---

## Process Monitor

Lists the top CPU-consuming processes on the host, detects zombie processes, and flags any process exceeding the configured CPU threshold. Results log to `logs/process_monitor.log`.

### Usage

```bash
# Standard table output (top 10)
python scripts/run_process_monitor.py

# Show top 20 processes
python scripts/run_process_monitor.py --top 20

# JSON output for pipeline consumption
python scripts/run_process_monitor.py --json

# Kill a process by PID (prompts for confirmation)
python scripts/run_process_monitor.py --kill 1234
```

### Example Output

```
  Timestamp  : 2026-04-20 15:31:54
  Overall    : OK
  Threshold  : CPU > 50.0%
  Zombies    : 0
  Flagged    : 0

  Top 10 Processes by CPU:
  ------------------------------------------------------------------------
  PID     NAME                            CPU%    MEM% STATUS       FLAG
  ------------------------------------------------------------------------
  18763   Code Helper (Renderer)           9.0     0.5 running
  43238   Claude Helper (Renderer)         7.6     0.7 running
  16100   Code Helper (GPU)                7.0     0.3 running
  ------------------------------------------------------------------------
```

Adjust the CPU threshold in `config/settings.py`:

```python
PROCESS_CPU_THRESHOLD = 50.0   # % — flag any process exceeding this
PROCESS_TOP_N         = 10     # default number of processes to display
```

---

## Scheduled Runner

Runs health check and process monitor in sequence, aggregates results, and writes a timestamped JSON report to `logs/`.

```bash
python scripts/run_all_checks.py
```

### Cron Integration

```cron
# Run every 15 minutes
*/15 * * * * cd ~/Projects/Automation/it-automation-python && .venv/bin/python scripts/run_all_checks.py >> /tmp/automation.log 2>&1
```

### Report Format

Each run writes `logs/report_YYYY-MM-DD_HHMMSS.json` containing:
- Combined overall status
- Full health check metrics
- Full process list with flags
- Zombie count and flagged process details

---

## Service Checker

Queries `launchctl list` to verify configured macOS launchd services are running. Marks any service with no PID as unhealthy. Results log to `logs/service_checker.log`.

### Usage

```bash
# Show target services only (configured in config/settings.py)
python scripts/run_service_checker.py

# Show all detected services
python scripts/run_service_checker.py --all

# JSON output
python scripts/run_service_checker.py --json
```

### Example Output

```
  Timestamp  : 2026-04-20 16:41:42
  Overall    : ALERT
  Targets    : 3
  Unhealthy  : 1

  Target Services:
  ------------------------------------------------------------------------------------
  SERVICE                                                  PID     EXIT HEALTHY  FLAG
  ------------------------------------------------------------------------------------
  com.apple.Finder                                        1678        0 True
  com.apple.Safari.SafeBrowsing.Service                   1742        0 True
  com.apple.AirPlayXPCHelper                                 -      N/A False    ⚠️  ALERT
  ------------------------------------------------------------------------------------
```

Configure target services in `config/settings.py`:

```python
TARGET_SERVICES = [
    "com.apple.AirPlayXPCHelper",
    "com.apple.Finder",
    "com.apple.Safari.SafeBrowsing.Service",
]
```

---

## Running Tests

```bash
# Run full suite via make
make test

# Or directly
pytest tests/ -v
```

44 tests across 3 modules. All use mocks — no real system calls, no flakiness.

| File | Tests | Covers |
|---|---|---|
| `test_health_check.py` | 17 | `check_cpu`, `check_memory`, `check_disk`, `run_health_check` |
| `test_process_monitor.py` | 16 | top-N sorting, zombie detection, threshold breach, empty list |
| `test_service_checker.py` | 11 | healthy/unhealthy parsing, missing targets, subprocess failure |

---

## Makefile

```bash
make install    # create .venv + install requirements
make health     # run system health check
make processes  # run process monitor
make services   # run service checker
make all        # run all checks + write JSON report
make test       # run pytest suite
make clean      # remove .pyc, __pycache__, log files
make help       # print this list
```

---

## Why This Matters

| Capability | What It Demonstrates |
|---|---|
| Modular architecture | `core/` separation of concerns — logic is reusable, not buried in scripts |
| Config-driven design | Thresholds and targets in config — no code changes to tune behavior |
| Structured logging | Per-module file + console dual-handler logging with timestamps |
| CLI design | `argparse` across 4 entry points with consistent flag patterns |
| Exit codes | Pipeline-compatible — works with `&&`, CI pass/fail gates, cron |
| JSON output | Composable with dashboards, Slack webhooks, Lambda, or Datadog |
| Unit test suite | 44 mocked tests — psutil, subprocess, and threshold boundary coverage |
| subprocess automation | `launchctl` parsing with graceful error handling for non-zero exits |
| Makefile ops | Single-command install, run, test, and clean — no manual venv activation |
| Aggregated reporting | Combined JSON report written per run — audit trail for all checks |

This pattern scales directly to fleet-wide monitoring, Lambda health checks, Ansible playbook validation, and CI pipeline gates.
