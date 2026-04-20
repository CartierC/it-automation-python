PYTHON  := .venv/bin/python
PYTEST  := .venv/bin/pytest
VENV    := .venv

.PHONY: install health processes services all test clean help

## install  : Create .venv and install all dependencies
install:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -q -r requirements.txt
	@echo "Environment ready."

## health   : Run system health check (CPU, memory, disk)
health:
	$(PYTHON) scripts/run_health_check.py

## processes: Run process monitor (top CPU consumers + zombie detection)
processes:
	$(PYTHON) scripts/run_process_monitor.py

## services : Run macOS service checker (launchd target service health)
services:
	$(PYTHON) scripts/run_service_checker.py

## all      : Run all checks and write combined JSON report to logs/
all:
	$(PYTHON) scripts/run_all_checks.py

## test     : Run pytest unit test suite
test:
	$(PYTEST) tests/ -v

## clean    : Remove .pyc files, __pycache__ dirs, and log files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -path "./logs/*.log" -delete
	@echo "Clean complete."

## help     : Print this help message
help:
	@echo ""
	@echo "  it-automation-python — available targets:"
	@echo ""
	@grep "^##" Makefile | sed 's/^## /  make /' | column -t -s ':'
	@echo ""
