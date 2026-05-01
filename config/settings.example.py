# config/settings.example.py
#
# Portfolio-safe reference showing all configurable parameters.
# Copy to config/settings.py and adjust values for your environment.
# The real config/settings.py is committed with safe defaults.
#
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
CONFIG_DIR = ROOT / "config"

# ── Process Monitor ────────────────────────────────────────────────────────────
# Flag any process whose CPU% exceeds this value as ALERT.
# Lower this threshold to catch runaway background jobs sooner.
PROCESS_CPU_THRESHOLD: float = 50.0   # percent

# Number of top processes to display in table output.
# Increase for a fuller picture; decrease for quieter cron output.
PROCESS_TOP_N: int = 10

PROCESS_LOG_PATH = LOG_DIR / "process_monitor.log"

# ── Service Checker ────────────────────────────────────────────────────────────
# macOS launchd service names to monitor. Any listed service with no active PID
# is marked unhealthy and triggers an ALERT exit code.
# Find service names with: launchctl list | grep <keyword>
TARGET_SERVICES: list[str] = [
    "com.apple.Finder",                      # Finder — always running on desktop
    "com.apple.Safari.SafeBrowsing.Service",  # Safari SafeBrowsing daemon
    # "com.apple.AirPlayXPCHelper",          # AirPlay — only present when active
    # "com.apple.networkd",                  # Network daemon — always running
]

SERVICE_LOG_PATH = LOG_DIR / "service_checker.log"

# ── Test Mock Values ───────────────────────────────────────────────────────────
# Used by the pytest suite to produce consistent, threshold-safe mock readings.
# Do not set these near your real thresholds — tests assert OK status.
TEST_CPU_MOCK_VALUE: float = 45.0    # below PROCESS_CPU_THRESHOLD of 50
TEST_MEM_MOCK_VALUE: float = 60.0    # below memory threshold of 80 (thresholds.json)
TEST_DISK_MOCK_VALUE: float = 55.0   # below disk threshold of 90 (thresholds.json)
