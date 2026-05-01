# Verification Checklist

Use this checklist to confirm the toolkit is installed, configured, and producing correct output. Each item has a concrete pass criterion — "looks right" is not a pass.

---

## Environment Setup

- [ ] **Python 3.10+ available**
  ```bash
  python3 --version
  # Pass: Python 3.10.x or higher
  ```

- [ ] **Virtual environment created**
  ```bash
  ls .venv/bin/python
  # Pass: file exists
  # If not: make install
  ```

- [ ] **Dependencies installed**
  ```bash
  .venv/bin/python -c "import psutil; print(psutil.__version__)"
  # Pass: prints version string (e.g., 6.1.1)
  ```

- [ ] **All required files present**
  ```bash
  for f in README.md requirements.txt core/system_health.py core/process_monitor.py core/service_checker.py; do
    [ -f "$f" ] && echo "OK  $f" || echo "MISSING  $f"
  done
  # Pass: all lines show OK
  ```

---

## Health Check

- [ ] **Script runs without error**
  ```bash
  python scripts/run_health_check.py
  # Pass: prints Host / Platform / Timestamp / Overall / Metrics block with no traceback
  ```

- [ ] **JSON output is valid**
  ```bash
  python scripts/run_health_check.py --json | python3 -m json.tool > /dev/null
  # Pass: exits 0 (no JSON parse error)
  ```

- [ ] **Quiet mode returns only OK or ALERT**
  ```bash
  python scripts/run_health_check.py --quiet
  # Pass: single line, value is exactly "OK" or "ALERT"
  ```

- [ ] **Exit code is correct**
  ```bash
  python scripts/run_health_check.py --quiet; echo "Exit: $?"
  # Pass: Exit: 0 when output is OK; Exit: 1 when output is ALERT
  ```

- [ ] **Log file is written**
  ```bash
  ls -lh logs/health_check.log
  # Pass: file exists and has a non-zero size
  grep "Health check complete" logs/health_check.log | tail -1
  # Pass: line with today's date appears
  ```

- [ ] **Threshold breach triggers ALERT**
  - Temporarily lower CPU threshold: edit `config/thresholds.json`, set `"cpu_percent": 1`
  - Run: `python scripts/run_health_check.py --quiet`
  - Pass: output is `ALERT`; exit code is `1`
  - Restore: reset `cpu_percent` to `85`

---

## Process Monitor

- [ ] **Script runs without error**
  ```bash
  python scripts/run_process_monitor.py
  # Pass: prints Timestamp / Overall / table of processes with no traceback
  ```

- [ ] **top N flag works**
  ```bash
  python scripts/run_process_monitor.py --top 3
  # Pass: table shows exactly 3 process rows (or fewer if system has fewer processes)
  ```

- [ ] **JSON output is valid and complete**
  ```bash
  python scripts/run_process_monitor.py --json | python3 -c "
  import json, sys
  d = json.load(sys.stdin)
  assert 'overall' in d
  assert 'processes' in d
  assert isinstance(d['processes'], list)
  print('JSON structure: OK')
  "
  ```

- [ ] **Each process entry has required fields**
  ```bash
  python scripts/run_process_monitor.py --json | python3 -c "
  import json, sys
  d = json.load(sys.stdin)
  required = {'pid', 'name', 'cpu_percent', 'mem_percent', 'status', 'flagged', 'is_zombie'}
  for p in d['processes']:
      assert required.issubset(p.keys()), f'Missing keys in: {p}'
  print('All entries have required keys: OK')
  "
  ```

- [ ] **Log file is written**
  ```bash
  grep "Process monitor complete" logs/process_monitor.log | tail -1
  # Pass: line with today's date appears
  ```

---

## Service Checker

- [ ] **Script runs without error**
  ```bash
  python scripts/run_service_checker.py
  # Pass: prints Timestamp / Overall / service table with no traceback
  # Note: on non-macOS hosts, overall will be ALERT (launchctl not found — expected)
  ```

- [ ] **JSON output is valid**
  ```bash
  python scripts/run_service_checker.py --json | python3 -m json.tool > /dev/null
  # Pass: exits 0
  ```

- [ ] **Target services are present in output**
  ```bash
  python scripts/run_service_checker.py --json | python3 -c "
  import json, sys
  d = json.load(sys.stdin)
  print('Targets checked:', d['target_count'])
  print('Unhealthy:', d['unhealthy_count'])
  "
  # Pass: target_count matches number of entries in TARGET_SERVICES (config/settings.py)
  ```

- [ ] **Log file is written**
  ```bash
  grep "Service check complete" logs/service_checker.log | tail -1
  # Pass: line with today's date appears
  ```

---

## Combined Runner

- [ ] **All checks run and report file is written**
  ```bash
  python scripts/run_all_checks.py
  ls -lh logs/report_*.json | tail -1
  # Pass: new report file with today's date, non-zero size
  ```

- [ ] **Report is valid JSON with expected top-level keys**
  ```bash
  ls logs/report_*.json | tail -1 | xargs python3 -c "
  import json, sys
  d = json.load(open(sys.argv[1]))
  for key in ('generated_at', 'overall', 'health_check', 'process_monitor', 'service_checker'):
      assert key in d, f'Missing key: {key}'
  print('Report structure: OK')
  " 2>/dev/null || python3 -c "
  import json, glob
  path = sorted(glob.glob('logs/report_*.json'))[-1]
  d = json.load(open(path))
  for key in ('generated_at', 'overall', 'health_check', 'process_monitor', 'service_checker'):
      assert key in d, f'Missing key: {key}'
  print('Report structure: OK')
  "
  ```

---

## Unit Tests

- [ ] **Full test suite passes**
  ```bash
  make test
  # Pass: all 44 tests pass, 0 failures, 0 errors
  ```

- [ ] **No tests skipped**
  ```bash
  pytest tests/ -v 2>&1 | grep -E "passed|failed|error|skip"
  # Pass: line shows "44 passed"
  ```

---

## CI / Linting

- [ ] **flake8 passes with no errors**
  ```bash
  flake8 core/ scripts/ tests/ tools/ config/ --statistics
  # Pass: exits 0, no error lines in output
  ```

- [ ] **Syntax check passes**
  ```bash
  python -m compileall core/ scripts/ tests/ tools/ config/ -q
  # Pass: exits 0, no error lines
  ```

---

## Makefile

- [ ] **All targets are listed**
  ```bash
  make help
  # Pass: shows install, health, processes, services, all, test, clean
  ```

- [ ] **make all runs without error**
  ```bash
  make all
  # Pass: exits 0 (or 1 if any check is ALERT — that is correct behavior, not an error)
  ```
