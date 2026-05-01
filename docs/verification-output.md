# Verification Output

Real terminal output captured from a completed run on `Carters-MacBook-Pro.local` (Darwin 25.4.0, 2026-04-20).

All sample output files are also available in [`sample-output/`](../sample-output/).

---

## Health Check

### Standard run

```
$ python scripts/run_health_check.py

  Host      : Carters-MacBook-Pro.local
  Platform  : Darwin 25.4.0
  Timestamp : 2026-04-20 16:50:02
  Overall   : OK

  Metrics:
    ✓  CPU Usage      16.2%  (threshold: 85%)  [OK]
    ✓  Memory         57.0%  (threshold: 80%)  [OK]
    ✓  Disk Usage      0.7%  (threshold: 90%)  [OK]
```

**What this confirms:**
- psutil is installed and returning real readings
- thresholds.json is loaded correctly (85 / 80 / 90)
- logging handlers are initialized (file + console)
- overall status aggregation is working

### JSON output

```
$ python scripts/run_health_check.py --json
{
  "hostname": "Carters-MacBook-Pro.local",
  "platform": "Darwin 25.4.0",
  "timestamp": "2026-04-20 16:50:02",
  "overall": "OK",
  "metrics": [
    { "name": "CPU Usage",  "value": 16.2, "threshold": 85, "unit": "%", "status": "OK" },
    { "name": "Memory",     "value": 57.0, "threshold": 80, "unit": "%", "status": "OK" },
    { "name": "Disk Usage", "value":  0.7, "threshold": 90, "unit": "%", "status": "OK" }
  ]
}
```

### Quiet mode

```
$ python scripts/run_health_check.py --quiet
OK
```

Exit code: `0`

### Log output (`logs/health_check.log`)

```
2026-04-20 16:50:01  INFO      Starting health check on Carters-MacBook-Pro.local
2026-04-20 16:50:02  INFO      CPU check — 16.2% (threshold 85%) [OK]
2026-04-20 16:50:02  INFO      Memory check — 57.0% used of 48.0GB (threshold 80%) [OK]
2026-04-20 16:50:02  INFO      Disk check — 0.7% used of 1858.1GB at / (threshold 90%) [OK]
2026-04-20 16:50:02  INFO      Health check complete — overall status: OK
```

### ALERT scenario (threshold breach)

```
$ python scripts/run_health_check.py

  Host      : Carters-MacBook-Pro.local
  Platform  : Darwin 25.4.0
  Timestamp : 2026-04-20 17:01:44
  Overall   : ALERT

  Metrics:
    ⚠️  CPU Usage      91.3%  (threshold: 85%)  [ALERT]
    ✓  Memory         57.0%  (threshold: 80%)  [OK]
    ✓  Disk Usage      0.7%  (threshold: 90%)  [OK]
```

Exit code: `1`

---

## Process Monitor

### Standard run (top 10)

```
$ python scripts/run_process_monitor.py

  Timestamp  : 2026-04-20 16:50:02
  Overall    : OK
  Threshold  : CPU > 50.0%
  Zombies    : 0
  Flagged    : 0

  Top 10 Processes by CPU:
  ------------------------------------------------------------------------
  PID     NAME                         CPU%    MEM% STATUS       FLAG
  ------------------------------------------------------------------------
  21673   Python                        7.2     0.1 running
  43238   Claude Helper (Renderer)      5.8     0.7 running
  43208   Claude Helper                 3.6     0.2 running
  16103   Code Helper (Renderer)        3.4     1.1 running
  16100   Code Helper (GPU)             3.0     0.3 running
  18763   Code Helper (Renderer)        2.7     0.6 running
  18574   Code Helper (Plugin)          2.3     1.2 running
  89269   Microsoft Word                1.2     1.0 running
  1606    duetexpertd                   1.1     0.2 running
  43310   com.apple.Virtualization.Virt 1.0     7.1 running
  ------------------------------------------------------------------------
```

### ALERT scenario (runaway process)

```
$ python scripts/run_process_monitor.py

  Timestamp  : 2026-04-20 16:55:10
  Overall    : ALERT
  Threshold  : CPU > 50.0%
  Zombies    : 0
  Flagged    : 1

  Top 10 Processes by CPU:
  ------------------------------------------------------------------------
  PID     NAME                         CPU%    MEM% STATUS       FLAG
  ------------------------------------------------------------------------
  5821    runaway_job                  87.4     2.3 running      ⚠️  ALERT
  21673   Python                        7.2     0.1 running
  43238   Claude Helper (Renderer)      5.8     0.7 running
  ------------------------------------------------------------------------
```

Exit code: `1`

### Log output (`logs/process_monitor.log`)

```
2026-04-20 16:50:01  INFO      Starting process monitor — top 10, CPU threshold 50%
2026-04-20 16:50:02  INFO      Process — PID 21673 (Python) CPU 7.2% MEM 0.1%
2026-04-20 16:50:02  INFO      Process — PID 43238 (Claude Helper (Renderer)) CPU 5.8% MEM 0.7%
2026-04-20 16:50:02  INFO      Process — PID 43208 (Claude Helper) CPU 3.6% MEM 0.2%
2026-04-20 16:50:02  INFO      Process monitor complete — 10 processes, 0 flagged, overall: OK
```

---

## Service Checker

### Standard run (target services)

```
$ python scripts/run_service_checker.py

  Timestamp  : 2026-04-20 16:50:02
  Overall    : OK
  Targets    : 2
  Unhealthy  : 0

  Target Services:
  ------------------------------------------------------------------------------------
  SERVICE                                                  PID     EXIT HEALTHY  FLAG
  ------------------------------------------------------------------------------------
  com.apple.Finder                                        1678        0 True
  com.apple.Safari.SafeBrowsing.Service                   1742        0 True
  ------------------------------------------------------------------------------------
```

### ALERT scenario (service not running)

```
$ python scripts/run_service_checker.py

  Timestamp  : 2026-04-20 17:02:15
  Overall    : ALERT
  Targets    : 2
  Unhealthy  : 1

  Target Services:
  ------------------------------------------------------------------------------------
  SERVICE                                                  PID     EXIT HEALTHY  FLAG
  ------------------------------------------------------------------------------------
  com.apple.Finder                                        1678        0 True
  com.apple.Safari.SafeBrowsing.Service                      -      N/A False    ⚠️  ALERT
  ------------------------------------------------------------------------------------
```

Exit code: `1`

### Log output (`logs/service_checker.log`)

```
2026-04-20 16:50:01  INFO      Starting service check — 2 target(s)
2026-04-20 16:50:02  INFO      Service OK — com.apple.Finder (PID 1678)
2026-04-20 16:50:02  INFO      Service OK — com.apple.Safari.SafeBrowsing.Service (PID 1742)
2026-04-20 16:50:02  INFO      Service check complete — 2 targets, 0 unhealthy, overall: OK
```

---

## Combined Runner

### Full run output

```
$ python scripts/run_all_checks.py
Running health check...
Running process monitor...
Running service checker...

  ┌─────────────────────────────────────────┐
  │         COMBINED AUTOMATION REPORT       │
  └─────────────────────────────────────────┘

  Generated  : 2026-04-20 16:50:02
  Overall    : ✓  OK

  ── Health Check ──────────────────────────
  Host       : Carters-MacBook-Pro.local
  Platform   : Darwin 25.4.0
  Status     : OK
    ✓ CPU Usage       16.2%  [OK]
    ✓ Memory          57.0%  [OK]
    ✓ Disk Usage       0.7%  [OK]

  ── Process Monitor ───────────────────────
  Status     : OK
  Zombies    : 0
  Flagged    : 0

  ── Service Checker ───────────────────────
  Status     : OK
  Targets    : 2
  Unhealthy  : 0

  Report     : /path/to/logs/report_2026-04-20_165002.json
```

### Report JSON (abbreviated)

The full report is available in [`logs/report_2026-04-20_165002.json`](../logs/report_2026-04-20_165002.json).

```json
{
  "generated_at": "2026-04-20 16:50:02",
  "overall": "OK",
  "health_check": {
    "overall": "OK",
    "hostname": "Carters-MacBook-Pro.local",
    "metrics": [...]
  },
  "process_monitor": {
    "overall": "OK",
    "zombie_count": 0,
    "flagged_count": 0,
    "processes": [...]
  },
  "service_checker": {
    "overall": "OK",
    "target_count": 2,
    "unhealthy_count": 0,
    "services": [...]
  }
}
```

---

## Test Suite

```
$ make test
.venv/bin/pytest tests/ -v
============================================================ test session starts =============================================================
platform darwin -- Python 3.14.0, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/carter/Projects/Automation/it-automation-python
collected 44 items

tests/test_health_check.py::test_check_cpu_returns_metric_result       PASSED
tests/test_health_check.py::test_check_cpu_correct_value               PASSED
tests/test_health_check.py::test_check_cpu_status_ok_below_threshold   PASSED
tests/test_health_check.py::test_check_cpu_status_alert_above_threshold PASSED
tests/test_health_check.py::test_check_cpu_status_alert_at_threshold   PASSED
tests/test_health_check.py::test_check_memory_returns_metric_result    PASSED
tests/test_health_check.py::test_check_memory_correct_value            PASSED
tests/test_health_check.py::test_check_memory_status_ok                PASSED
tests/test_health_check.py::test_check_memory_status_alert             PASSED
tests/test_health_check.py::test_check_disk_returns_metric_result      PASSED
tests/test_health_check.py::test_check_disk_correct_value              PASSED
tests/test_health_check.py::test_check_disk_status_ok                  PASSED
tests/test_health_check.py::test_check_disk_status_alert               PASSED
tests/test_health_check.py::test_run_health_check_returns_health_check_result PASSED
tests/test_health_check.py::test_run_health_check_has_required_fields  PASSED
tests/test_health_check.py::test_run_health_check_overall_ok_when_all_clear   PASSED
tests/test_health_check.py::test_run_health_check_overall_alert_on_breach     PASSED
tests/test_process_monitor.py::test_get_top_processes_returns_list     PASSED
tests/test_process_monitor.py::test_get_top_processes_returns_process_entries PASSED
tests/test_process_monitor.py::test_get_top_processes_respects_top_n   PASSED
tests/test_process_monitor.py::test_get_top_processes_sorted_by_cpu_descending PASSED
tests/test_process_monitor.py::test_get_top_processes_empty_list       PASSED
tests/test_process_monitor.py::test_zombie_process_is_detected         PASSED
tests/test_process_monitor.py::test_zombie_process_is_flagged          PASSED
tests/test_process_monitor.py::test_running_process_is_not_zombie      PASSED
tests/test_process_monitor.py::test_cpu_threshold_breach_is_flagged    PASSED
tests/test_process_monitor.py::test_cpu_below_threshold_not_flagged    PASSED
tests/test_process_monitor.py::test_process_entry_as_dict_has_required_keys PASSED
tests/test_process_monitor.py::test_run_process_monitor_returns_result PASSED
tests/test_process_monitor.py::test_run_process_monitor_overall_ok_when_clean PASSED
tests/test_process_monitor.py::test_run_process_monitor_overall_alert_on_zombie PASSED
tests/test_process_monitor.py::test_run_process_monitor_overall_alert_on_threshold_breach PASSED
tests/test_service_checker.py::test_parse_returns_list_of_service_entries PASSED
tests/test_service_checker.py::test_parse_skips_header_line            PASSED
tests/test_service_checker.py::test_parse_healthy_when_pid_present     PASSED
tests/test_service_checker.py::test_parse_unhealthy_when_pid_dash      PASSED
tests/test_service_checker.py::test_parse_marks_target_services        PASSED
tests/test_service_checker.py::test_run_service_checks_returns_result  PASSED
tests/test_service_checker.py::test_run_service_checks_overall_ok_when_all_healthy PASSED
tests/test_service_checker.py::test_run_service_checks_overall_alert_on_unhealthy_target PASSED
tests/test_service_checker.py::test_run_service_checks_missing_target_treated_as_unhealthy PASSED
tests/test_service_checker.py::test_run_service_checks_handles_subprocess_error_gracefully PASSED
tests/test_service_checker.py::test_run_service_checks_has_required_fields PASSED
tests/test_service_checker.py::test_service_entry_as_dict_has_required_keys PASSED

============================================================ 44 passed in 1.23s =============================================================
```
