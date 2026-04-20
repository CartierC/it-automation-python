# IT Automation — Python

Production-grade system health monitoring with configurable alert thresholds, structured logging, and machine-readable output. Built as a foundation for IT / Cloud / DevOps automation tooling.

**Author:** CartierC — Cloud Systems Architect

---

## What It Does

Polls CPU, Memory, and Disk utilization on any Mac or Linux host. Compares live readings against configurable thresholds and emits a pass/fail result — either human-readable to the terminal or JSON for pipeline consumption. Every run is logged to `logs/health_check.log` with timestamps.

---

## Project Structure

```
it-automation-python/
├── core/
│   ├── __init__.py
│   └── system_health.py       # Business logic — metric collection + threshold evaluation
├── scripts/
│   └── run_health_check.py    # CLI entry point (argparse, JSON output, exit codes)
├── tools/
│   └── health_check.py        # Stdlib-only quick check (zero dependencies)
├── config/
│   └── thresholds.json        # Alert thresholds — edit without touching code
├── logs/
│   └── health_check.log       # Auto-created on first run
├── docs/
│   └── runbook.md
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

## Why This Matters

| Capability | What It Demonstrates |
|---|---|
| Modular architecture | `core/` separation of concerns — logic is reusable, not buried in scripts |
| Config-driven design | Thresholds in JSON — no code changes to adjust behavior |
| Structured logging | File + console dual-handler logging with timestamps |
| CLI design | `argparse` with mutually exclusive output modes |
| Exit codes | Pipeline-compatible — works with `&&`, CI pass/fail gates |
| JSON output | Composable with dashboards, Slack webhooks, or monitoring stacks |

This pattern scales directly to fleet-wide monitoring, Lambda health checks, and Ansible playbook validation.
