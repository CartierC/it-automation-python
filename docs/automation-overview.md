# Automation Overview

**Repo:** `it-automation-python`  
**Author:** CartierC

---

## What This Toolkit Automates

This toolkit replaces manual spot-checks with repeatable, scriptable automation across three operational domains: system resource health, process lifecycle, and macOS service state. Each domain maps to a `core/` module and a `scripts/` CLI entry point.

---

## Component Map

| Domain | Core Module | CLI Script | Log File | Output Formats |
|---|---|---|---|---|
| System Health | `core/system_health.py` | `scripts/run_health_check.py` | `logs/health_check.log` | human, JSON, quiet |
| Process Monitor | `core/process_monitor.py` | `scripts/run_process_monitor.py` | `logs/process_monitor.log` | human, JSON |
| Service Checker | `core/service_checker.py` | `scripts/run_service_checker.py` | `logs/service_checker.log` | human, JSON |
| Combined Runner | _(calls all three)_ | `scripts/run_all_checks.py` | `logs/report_YYYY-MM-DD_HHMMSS.json` | human summary + JSON report |

---

## Data Flow

```
config/thresholds.json  ──┐
config/settings.py      ──┤
                          ▼
                    core/ modules
                    (pure logic, no I/O)
                          │
               ┌──────────┼──────────┐
               ▼          ▼          ▼
        scripts/       logs/      JSON report
        (CLI I/O)    (append)    (per run)
```

The `core/` modules are pure logic — they receive thresholds, call system APIs, and return typed dataclass results. All I/O (print, log, write) happens in `scripts/`. This separation makes unit testing straightforward: tests mock psutil and subprocess at the `core/` layer and never touch the filesystem.

---

## Execution Model

Every script follows the same pattern:

1. Parse CLI args with `argparse`
2. Call the relevant `core/` function
3. Print results in the requested format (human / JSON / quiet)
4. Exit with code `0` (OK) or `1` (ALERT)

The exit code makes every script pipeline-compatible: usable with `&&` chains, Makefile guards, cron alerting, and CI gates.

---

## Configuration

Two config files control behavior — no code changes needed to tune the system:

| File | Controls |
|---|---|
| `config/thresholds.json` | CPU, memory, and disk alert thresholds (health check) |
| `config/settings.py` | Per-process CPU threshold, top-N count, target services list, log paths |

See `config/settings.example.py` for fully documented parameter reference.

---

## Combined Runner

`scripts/run_all_checks.py` runs all three checks in sequence and writes a single timestamped JSON report to `logs/`. This is the primary entry point for cron and scheduled monitoring:

```bash
python scripts/run_all_checks.py
# → logs/report_2026-04-20_165002.json
```

The report aggregates all results into one document with a combined overall status, making it suitable for ingestion by dashboards, log aggregators, or webhook senders.

---

## Zero-Dependency Fallback

`tools/health_check.py` uses only Python stdlib (`os`, `platform`, `shutil`) and requires no installation. It's intended for environments where psutil cannot be installed (restricted hosts, quick triage):

```bash
python tools/health_check.py
```

It does not perform threshold comparison or logging — for full monitoring, use `scripts/run_health_check.py`.

---

## Further Reading

- [System Health Monitoring](system-health-monitoring.md) — psutil internals, sampling strategy, threshold logic
- [Threat Model](threat-model.md) — what failure states this tooling detects and what it doesn't
- [Verification Checklist](verification-checklist.md) — how to confirm the tooling is working correctly
- [Verification Output](verification-output.md) — real terminal output from a completed run
- [Operations Runbook](runbook.md) — alert response procedures, config reference, troubleshooting
