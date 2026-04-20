# config/settings.py
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
CONFIG_DIR = ROOT / "config"

# ── Process Monitor ───────────────────────────────────────────────────────────
PROCESS_CPU_THRESHOLD: float = 50.0   # % — flag any process exceeding this
PROCESS_TOP_N: int = 10               # default number of processes to display
PROCESS_LOG_PATH = LOG_DIR / "process_monitor.log"

# ── Service Checker ───────────────────────────────────────────────────────────
TARGET_SERVICES: list[str] = [
    "com.apple.AirPlayXPCHelper",
    "com.apple.Finder",
    "com.apple.Safari.SafeBrowsing.Service",
]
SERVICE_LOG_PATH = LOG_DIR / "service_checker.log"

# ── Test Mock Values ──────────────────────────────────────────────────────────
TEST_CPU_MOCK_VALUE: float = 45.0
TEST_MEM_MOCK_VALUE: float = 60.0
TEST_DISK_MOCK_VALUE: float = 55.0
