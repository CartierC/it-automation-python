# System Health Checker - Runbook

## Purpose
Automated monitoring of CPU, RAM, and Disk utilization against defined thresholds.

## Usage
```bash
pip install psutil
python3 scripts/health_check.py
```

## Alert Logic
- CPU  > 85% ? Alert
- RAM  > 80% ? Alert
- Disk > 90% ? Alert

## Author
CartierC - Cloud Systems Architect
