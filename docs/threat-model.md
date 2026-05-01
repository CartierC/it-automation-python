# Threat Model — What This Tooling Detects

**Repo:** `it-automation-python`

This document maps each automation module to the operational failure states it detects, what evidence it produces, and what remains outside its scope. The goal is to be explicit about both coverage and gaps — a clear threat model is more useful than an overclaimed one.

---

## Health Check — `core/system_health.py`

### Failure States Detected

| Failure Condition | Detection Mechanism | Alert Signal |
|---|---|---|
| CPU spike (sustained utilization above threshold) | `psutil.cpu_percent(interval=1)` | `overall: ALERT`, exit code 1 |
| Memory pressure (RAM usage above threshold) | `psutil.virtual_memory().percent` | `overall: ALERT`, exit code 1 |
| Disk saturation (mount point above threshold) | `psutil.disk_usage("/").percent` | `overall: ALERT`, exit code 1 |
| Any single metric at or above threshold | Metric-level `status: ALERT` rolls up to overall | Log entry + structured output |

### How Detection Works

Each metric is sampled once per run and compared against a configured threshold. The `>=` comparison ensures that a reading exactly at the threshold triggers ALERT — "at the limit" is not safe. The 1-second interval on CPU polling gives a real utilization average rather than an instantaneous snapshot.

### What This Does NOT Detect

| Failure Type | Why It's Out of Scope |
|---|---|
| Intermittent CPU spikes (< 1 second duration) | Polling is point-in-time; a spike that resolves before the check runs is invisible |
| Memory leak progression over time | Requires trend analysis across multiple readings; a single run shows current state only |
| Disk I/O saturation (throughput/latency) | Monitors space usage, not I/O wait or bandwidth |
| Swap utilization | Not currently polled; add `psutil.swap_memory()` to extend coverage |
| Specific filesystem paths other than `/` | Health check checks root mount only; add `check_disk(threshold, path="/data")` calls to extend |
| Remote host health | Single-host only; fleet monitoring requires SSH or an agent-based approach |

---

## Process Monitor — `core/process_monitor.py`

### Failure States Detected

| Failure Condition | Detection Mechanism | Alert Signal |
|---|---|---|
| Runaway process (CPU above per-process threshold) | Two-pass `psutil.process_iter()` sampling | `flagged: true`, `overall: ALERT`, exit code 1 |
| Zombie process | `status == "zombie"` check on all enumerated processes | `is_zombie: true`, logged as WARNING |
| Multiple simultaneous CPU offenders | All processes in top-N scanned, all flagged entries reported | Count in `flagged_count` field |

### Two-Pass Sampling

psutil's `cpu_percent()` returns 0.0 on the first call for any process (it needs a baseline reading). The monitor primes all processes with a first pass, sleeps 0.5 seconds, then reads the real CPU values. This eliminates false zeroes and produces accurate per-process readings.

### What This Does NOT Detect

| Failure Type | Why It's Out of Scope |
|---|---|
| Processes consuming excessive memory | Only top-N by CPU is ranked; a low-CPU, high-RAM process may not appear |
| Processes consuming excessive disk I/O | psutil can provide `io_counters()` but this is not currently polled |
| Processes with excessive open file descriptors | Requires `proc.num_fds()` — not included |
| Process crash / unexpected exit | A dead process is simply absent from the listing; requires a watchdog pattern |
| Orphaned processes (non-zombie but parent-detached) | No parent-relationship analysis is performed |
| Privileged processes (root-owned) | `psutil.AccessDenied` is caught and the process is skipped |

---

## Service Checker — `core/service_checker.py`

### Failure States Detected

| Failure Condition | Detection Mechanism | Alert Signal |
|---|---|---|
| Target service not running (no PID) | `launchctl list` output: PID column is `-` | `healthy: false`, `overall: ALERT`, exit code 1 |
| Target service absent from launchctl output | Not found in parsed output → injected as unhealthy | `healthy: false`, logged as WARNING |
| `launchctl` command failure | `CalledProcessError` caught; all targets treated as unhealthy | `overall: ALERT` |
| `launchctl` not found (non-macOS host) | `FileNotFoundError` caught; all targets treated as unhealthy | `overall: ALERT`, logged as ERROR |

### What This Does NOT Detect

| Failure Type | Why It's Out of Scope |
|---|---|
| Service is running but unresponsive | PID presence does not imply the service is accepting requests; health probe required |
| Service restart loops | A service that crashes and relaunches quickly appears healthy if it has a PID at check time |
| Non-launchd services (systemd, Docker, etc.) | macOS launchd only; extend with a `systemctl` backend for Linux parity |
| Service CPU/memory usage | Use the process monitor with the service's PID for resource profiling |
| Exit status codes | Non-zero exit status is recorded but not currently used in health determination |

---

## Combined Runner — `scripts/run_all_checks.py`

The combined runner aggregates results from all three modules. Its overall status is ALERT if any individual module reports ALERT. It does not add new detection logic — it is purely an aggregation and reporting layer.

---

## What This Toolkit Is Not

This is a **local, polling-based IT automation tool** designed for:
- Developer machines, lab hosts, and small server fleets
- Scheduled execution via cron
- Portfolio demonstration of Python operational scripting

It is **not** a replacement for:
- Production observability platforms (Datadog, Grafana + Prometheus, CloudWatch)
- Distributed tracing or APM
- Real-time alerting with on-call paging
- Centralized log aggregation (Elasticsearch, Splunk)
- Container or Kubernetes monitoring

The gaps identified above are intentional scope boundaries, not defects — and many are straightforward extension points documented in the README.
