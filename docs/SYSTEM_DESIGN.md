# System Design — IT Automation Toolkit

## Overview

The IT Automation Toolkit is a Python-based operational monitoring system designed to run as a standalone CLI tool, a cron job, or a CI/CD step. It polls system health, process state, and service availability — emitting structured logs, exit-code–driven results, and JSON reports per run.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    CLI Entry Points                       │
│   scripts/run_all_checks.py   scripts/run_health_check.py│
│   scripts/run_process_monitor.py  scripts/run_service... │
└─────────────────────┬────────────────────────────────────┘
                      │ imports
         ┌────────────┼────────────┐
         ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
│  core/       │ │  core/       │ │  core/               │
│  system_     │ │  process_    │ │  service_checker.py  │
│  health.py   │ │  monitor.py  │ │                      │
│              │ │              │ │  launchctl subprocess │
│  psutil CPU  │ │  psutil proc │ │  macOS service health │
│  memory disk │ │  top-N + zombie│ │                    │
└──────┬───────┘ └──────┬───────┘ └──────────┬───────────┘
       │                │                    │
       └────────────────┴────────────────────┘
                        │ results
                        ▼
              ┌──────────────────┐
              │  run_all_checks  │
              │  build_report()  │  ← aggregates all check results
              │  write_report()  │  ← logs/report_YYYY-MM-DD_HHMMSS.json
              │  print_summary() │  ← structured console output
              └──────────────────┘
                        │
          ┌─────────────┴──────────────┐
          ▼                            ▼
┌──────────────────┐        ┌──────────────────────┐
│  logs/           │        │  sample-output/      │
│  health_check.log│        │  health-check-run.txt│
│  process_mon.log │        │  health-check-        │
│  report_*.json   │        │  screenshot.png       │
└──────────────────┘        └──────────────────────┘
```

---

## Module Responsibilities

| Module | Responsibility | Key Output |
|---|---|---|
| `core/system_health.py` | CPU, memory, disk polling via psutil | `HealthCheckResult` dataclass |
| `core/process_monitor.py` | Top-N process CPU, zombie detection | `ProcessMonitorResult` dataclass |
| `core/service_checker.py` | macOS launchd service health via `launchctl` | `ServiceCheckResult` dataclass |
| `scripts/run_all_checks.py` | Orchestrator — runs all three checks, writes report | JSON report + console summary |
| `scripts/run_health_check.py` | Standalone health check with `--json` / `--quiet` flags | Flexible output modes |
| `scripts/aggregate_metrics.py` | Reads `logs/report_*.json`, computes aggregate stats | Pass rate, severity distribution |
| `tools/health_check.py` | Zero-dependency quick check (no psutil) | Stdlib-only fallback |
| `tools/failure_simulator.py` | Injects synthetic failures for testing alerting paths | Test/CI validation tool |
| `config/thresholds.json` | Threshold configuration — no code changes needed | Runtime-configurable limits |

---

## Data Flow

```
1. run_all_checks.py starts
   └── logs: "Orchestration started | checks=health,process,service"

2. core/system_health.run_health_check()
   ├── reads config/thresholds.json
   ├── polls: psutil.cpu_percent(), virtual_memory(), disk_usage()
   ├── constructs MetricResult per check (status: OK/WARNING/CRITICAL)
   └── returns HealthCheckResult (overall = worst-case severity)

3. core/process_monitor.run_process_monitor()
   ├── gets top-N processes by CPU (psutil.process_iter)
   ├── flags: zombies + CPU threshold breaches
   └── returns ProcessMonitorResult

4. core/service_checker.run_service_checks()
   ├── runs: launchctl list <service> for each target
   ├── parses stdout for health state
   └── returns ServiceCheckResult

5. build_report() aggregates → worst-case overall status
   ├── write_report() → logs/report_YYYY-MM-DD_HHMMSS.json
   └── print_summary() → structured console output

6. sys.exit(0|1|2) — OK | WARNING | CRITICAL
   └── composable with CI pipelines, cron, Lambda health checks
```

---

## Design Decisions

### Exit-Code Discipline

All entry points exit `0` (OK), `1` (WARNING), or `2` (CRITICAL). This makes the toolkit composable with any orchestrator that reads exit codes — cron, GitHub Actions `if: failure()`, AWS Lambda health checks, or Makefile `&&` chains.

### Dataclass-First Results

Each check module returns a typed dataclass (`HealthCheckResult`, `ProcessMonitorResult`, etc.) rather than raw dicts. This enforces a contract between check modules and the orchestrator, makes test assertions readable, and allows each module to be run independently.

### Structured Logging

All modules log to both file and stdout via `logging.basicConfig`. Log format is `[YYYY-MM-DD HH:MM:SS] [LEVEL] message` — machine-parseable by log aggregators (CloudWatch, Datadog) without a custom parser.

### Configurable Thresholds, No Hardcoding

Warn and critical thresholds live in `config/thresholds.json`. Operators can tune alerting sensitivity without touching Python. This is the same pattern used in production monitoring tools like Nagios and Prometheus alert rules.

### Zero-Dependency Fallback

`tools/health_check.py` implements CPU/memory/disk polling using only Python stdlib (`os`, `subprocess`, `pathlib`). This ensures the core capability works in locked-down environments where pip installs are restricted.

---

## Testing Strategy

| Test Module | Coverage Target | Approach |
|---|---|---|
| `test_health_check.py` | `core/system_health` | Mock `psutil.*` — boundary testing at warn/crit thresholds |
| `test_process_monitor.py` | `core/process_monitor` | Mock `psutil.process_iter` — zombie and CPU breach scenarios |
| `test_service_checker.py` | `core/service_checker` | Mock `subprocess.run` — healthy, unhealthy, missing, error cases |
| `test_config_validation.py` | `config/` | Direct JSON load — key presence, types, value ranges |
| `test_failure_simulator.py` | `tools/failure_simulator` | Direct instantiation — scenario structure, status values |

**No live system calls in tests.** Every psutil and subprocess call is mocked. This means tests run identically on macOS, Linux, and CI runners without requiring real services or specific hardware state.

---

## Observability Model

```
┌─────────────────────────────────────────────────────┐
│  SIGNAL          │  MECHANISM          │  CONSUMER   │
├─────────────────────────────────────────────────────┤
│  Structured log  │  logging module     │  tail, grep,│
│  (per run)       │  file + stdout      │  CloudWatch  │
├─────────────────────────────────────────────────────┤
│  Exit code       │  sys.exit(0/1/2)    │  cron, CI,  │
│                  │                     │  Lambda     │
├─────────────────────────────────────────────────────┤
│  JSON report     │  logs/report_*.json │  dashboards,│
│  (per run)       │  structured schema  │  pipelines  │
├─────────────────────────────────────────────────────┤
│  Aggregate stats │  aggregate_metrics  │  trend      │
│  (cross-run)     │  .py reads reports  │  analysis   │
└─────────────────────────────────────────────────────┘
```

The JSON report schema is stable across runs — every report includes `generated_at`, `overall`, and nested `health_check`, `process_monitor`, `service_checker` objects. `scripts/aggregate_metrics.py` reads these reports to compute cross-run statistics: pass rate, severity distribution, per-metric status counts.

---

## Configuration

`config/thresholds.json` controls all alert thresholds:

```json
{
  "cpu_percent": 80,
  "memory_percent": 80,
  "disk_percent": 85
}
```

`config/settings.py` controls process monitor behavior, target service list, and log file paths. No environment variables required — the tool is self-contained and run-anywhere.
