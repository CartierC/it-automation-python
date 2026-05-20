# IT Automation Toolkit (Python)

[![CI](https://github.com/CartierC/it-automation-python/actions/workflows/ci.yml/badge.svg)](https://github.com/CartierC/it-automation-python/actions/workflows/ci.yml)

Operational monitoring and system health automation for IT support, infrastructure operations, and cloud-adjacent environments. Demonstrates production-oriented Python scripting: modular architecture, structured logging, exit-code–driven workflows, and CI-integrated test coverage.

---

## What It Does

- Polls CPU, memory, and disk utilization against configurable warn/critical thresholds
- Monitors top-N processes by CPU — detects zombie processes and threshold breaches
- Validates macOS launchd service health via `launchctl`
- Emits structured, severity-mapped logs (`[INFO]` / `[WARNING]` / `[CRITICAL]`) with timestamps and duration
- Writes a timestamped JSON report per run — audit trail for every execution

---

## Skills Demonstrated

| Skill | Implementation |
|---|---|
| Python scripting | `core/` modules — dataclasses, argparse, logging, subprocess |
| System metrics | CPU, memory, disk polling with psutil; tri-level severity model |
| Service inspection | macOS launchd via `launchctl` with graceful subprocess error handling |
| Structured logging | `[YYYY-MM-DD HH:MM:SS] [LEVEL] message` — dual file + console handlers |
| Exit-code discipline | `0` = OK, `1` = WARNING, `2` = CRITICAL — CI and cron compatible |
| JSON output | Per-run report in `logs/` — composable with pipelines, dashboards, Lambda |
| Unit testing | 81 mocked pytest tests — boundary coverage, zero flakiness, no real system calls |
| CI | GitHub Actions — lint (flake8), test (pytest), artifact export on every push |

---

## Quick Start

```bash
git clone https://github.com/CartierC/it-automation-python.git
cd it-automation-python
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## Run Health Checks

```bash
# Combined runner — health + processes + services, JSON report written to logs/
python scripts/run_all_checks.py

# System health only
python scripts/run_health_check.py

# JSON output — pipeline and Lambda ready
python scripts/run_health_check.py --json

# Quiet mode — prints OK or ALERT, exits 0 or 1
python scripts/run_health_check.py --quiet

# Zero-dependency quick check (no psutil required)
python tools/health_check.py
```

Thresholds are configurable in `config/thresholds.json` — no code changes needed.

---

## Run Tests

```bash
pytest tests/ -v
```

81 tests across 5 modules. All mocked — no live system calls, no flakiness.

| Module | Tests | Covers |
|---|---|---|
| `test_health_check.py` | 17 | CPU, memory, disk — OK/WARNING/CRITICAL boundaries |
| `test_process_monitor.py` | 16 | Top-N sort, zombie detection, threshold breach |
| `test_service_checker.py` | 11 | Healthy/unhealthy parsing, missing targets, subprocess failure |
| `test_config_validation.py` | 16 | Key presence, types, sane value ranges |
| `test_failure_simulator.py` | 21 | Scenario structure, status, correctness |

---

## Sample Output

Real execution artifact: [`sample-output/health-check-run.txt`](sample-output/health-check-run.txt)

```
[2026-05-20 14:12:14] [INFO] Orchestration started | checks=health,process,service
[2026-05-20 14:12:15] [INFO] CPU STATUS: OK | usage=2.7%
[2026-05-20 14:12:15] [INFO] MEMORY STATUS: OK | usage=44.2% available=26.8GB
[2026-05-20 14:12:15] [INFO] DISK STATUS: OK | usage=0.7% mount=/
[2026-05-20 14:12:15] [INFO] Health check completed | exit_code=0 duration=1.01s
[2026-05-20 14:12:16] [WARNING] CPU threshold breach — PID 903 (mediaanalysisd) at 96.8%
[2026-05-20 14:12:16] [INFO] Orchestration complete | overall=WARNING exit_code=1 duration=1.57s
```

---

## Project Structure

```
core/               # Health, process, and service check logic
scripts/            # CLI entry points (run_all_checks, run_health_check, ...)
tests/              # pytest suite — 81 mocked tests
tools/              # Stdlib-only quick health check
config/             # thresholds.json, settings.py
logs/               # Auto-created — structured log files + JSON reports
sample-output/      # Real execution artifacts
.github/workflows/  # CI — lint, test, artifact export
```

---

## Recruiter Note

Every component maps directly to tasks an Automation Analyst, IT Support Engineer, or Technical Operations hire performs on the job: polling system state, detecting threshold breaches, validating service health, writing structured logs, and integrating with CI pipelines. The codebase is runnable from a single command and auditable from the JSON reports in `logs/`.
