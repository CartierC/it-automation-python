# System Health Monitoring

**Module:** `core/system_health.py`  
**Script:** `scripts/run_health_check.py`  
**Log:** `logs/health_check.log`

---

## What It Monitors

The health check polls three system metrics on every run using [psutil](https://psutil.readthedocs.io/):

| Metric | psutil API | Default Threshold | What It Measures |
|---|---|---|---|
| CPU Usage | `psutil.cpu_percent(interval=1)` | 85% | System-wide CPU utilization averaged over 1 second |
| Memory | `psutil.virtual_memory().percent` | 80% | RAM in use as a percentage of total physical memory |
| Disk | `psutil.disk_usage("/").percent` | 90% | Used disk space at the root mount as a percentage of total |

---

## How Threshold Comparison Works

Each metric is wrapped in a `MetricResult` dataclass that evaluates status at construction time:

```python
@dataclass
class MetricResult:
    name: str
    value: float
    threshold: float
    unit: str = "%"
    status: str = field(init=False)

    def __post_init__(self):
        self.status = "ALERT" if self.value >= self.threshold else "OK"
```

`>=` is intentional — a reading exactly at the threshold triggers ALERT. This matches the operational principle that "at the limit" is not "safe."

The `HealthCheckResult` rolls up individual metric statuses: if any single metric is ALERT, the overall status is ALERT.

---

## CPU Sampling Strategy

`psutil.cpu_percent(interval=1)` blocks for one second and returns a real utilization reading. The `interval=1` argument is required — calling with `interval=None` returns 0.0 on the first call because psutil computes CPU% as a delta between two readings.

This is distinct from the process monitor's two-pass sampling strategy, which primes a per-process baseline before reading.

---

## Configuring Thresholds

Thresholds are stored in `config/thresholds.json` — no code changes required:

```json
{
  "cpu_percent": 85,
  "memory_percent": 80,
  "disk_percent": 90
}
```

**Tuning guidance:**

| Threshold | Conservative | Moderate | Aggressive |
|---|---|---|---|
| `cpu_percent` | 70% | 85% | 95% |
| `memory_percent` | 70% | 80% | 90% |
| `disk_percent` | 80% | 90% | 95% |

Lower values generate more alerts. Set based on your workload's normal operating baseline — a developer machine running compilation may legitimately spike to 85% CPU, while a service host should rarely exceed 50%.

---

## Output Formats

### Human-readable (default)

```
  Host      : macbook-pro.local
  Platform  : Darwin 25.4.0
  Timestamp : 2026-04-20 16:50:02
  Overall   : OK

  Metrics:
    ✓  CPU Usage      16.2%  (threshold: 85%)  [OK]
    ✓  Memory         57.0%  (threshold: 80%)  [OK]
    ✓  Disk Usage      0.7%  (threshold: 90%)  [OK]
```

### JSON (`--json`)

```json
{
  "hostname": "macbook-pro.local",
  "platform": "Darwin 25.4.0",
  "timestamp": "2026-04-20 16:50:02",
  "overall": "OK",
  "metrics": [
    { "name": "CPU Usage", "value": 16.2, "threshold": 85, "unit": "%", "status": "OK" },
    { "name": "Memory",    "value": 57.0, "threshold": 80, "unit": "%", "status": "OK" },
    { "name": "Disk Usage","value":  0.7, "threshold": 90, "unit": "%", "status": "OK" }
  ]
}
```

### Quiet (`--quiet`)

Prints only `OK` or `ALERT` — designed for cron and shell scripting:

```bash
STATUS=$(python scripts/run_health_check.py --quiet)
if [ "$STATUS" = "ALERT" ]; then
    # send notification
fi
```

---

## Exit Codes

| Code | Condition |
|---|---|
| `0` | All metrics within thresholds |
| `1` | One or more metrics at or above threshold |

The exit code is the primary signal for CI/CD gates, cron alerting, and shell `&&` chains.

---

## Logging

Every run appends to `logs/health_check.log`:

```
2026-04-20 16:50:01  INFO      Starting health check on macbook-pro.local
2026-04-20 16:50:02  INFO      CPU check — 16.2% (threshold 85%) [OK]
2026-04-20 16:50:02  INFO      Memory check — 57.0% used of 48.0GB (threshold 80%) [OK]
2026-04-20 16:50:02  INFO      Disk check — 0.7% used of 1858.1GB at / (threshold 90%) [OK]
2026-04-20 16:50:02  INFO      Health check complete — overall status: OK
```

The logger uses a dual-handler setup: one `FileHandler` (persistent audit trail) and one `StreamHandler` (console visibility). Format: `YYYY-MM-DD HH:MM:SS  LEVEL  message`.

---

## Scope and Limitations

**In scope:**
- Single-host CPU, memory, and disk monitoring
- Configurable thresholds via JSON
- Structured logging for audit trail
- Pipeline-compatible output (JSON + exit codes)

**Out of scope:**
- Multi-host / fleet monitoring (requires SSH + orchestration layer)
- Historical trend analysis or alerting rate-of-change
- Network I/O monitoring (not covered by this module)
- Log rotation (stdlib `RotatingFileHandler` would be the next step)
- Prometheus / Datadog metrics export

See [Threat Model](threat-model.md) for a complete breakdown of what failure conditions this tooling detects vs. what it does not.
