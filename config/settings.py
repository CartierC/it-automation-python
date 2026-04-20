# config/settings.py
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
CONFIG_DIR = ROOT / "config"

# ── Process Monitor ───────────────────────────────────────────────────────────
PROCESS_CPU_THRESHOLD: float = 50.0   # % — flag any process exceeding this
PROCESS_TOP_N: int = 10               # default number of processes to display
PROCESS_LOG_PATH = LOG_DIR / "process_monitor.log"
