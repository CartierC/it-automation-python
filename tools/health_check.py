"""
Lightweight standalone health check — no dependencies beyond stdlib.

Writes structured logs to logs/health_check.log.
For the full-featured version with psutil and threshold alerts, use:
    python scripts/run_health_check.py
"""
import logging
import os
import platform
import shutil
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_LOG_PATH = _ROOT / "logs" / "health_check.log"

# Named logger — avoids conflicts with root logger from core/ modules.
# File-only handler so terminal shows only the clean structured print output.
logger = logging.getLogger("tools.health_check")
if not logger.handlers:
    _handler = logging.FileHandler(_LOG_PATH)
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def check_system() -> None:
    host = platform.node()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("event=start host=%s timestamp=%s", host, ts)

    cpu_count = os.cpu_count() or 0
    logger.info("check=cpu status=OK value=%d unit=cores", cpu_count)
    print(f"Host     : {host}")
    print(f"OS       : {platform.system()} {platform.release()}")
    print(f"CPU      : {cpu_count} logical cores")

    total, used, _ = shutil.disk_usage("/")
    used_gb = used // (1024 ** 3)
    total_gb = total // (1024 ** 3)
    disk_pct = round(used / total * 100, 1) if total else 0.0
    disk_status = "ALERT" if disk_pct >= 90.0 else "OK"
    logger.info(
        "check=disk status=%s value=%.1f unit=pct used=%dGB total=%dGB",
        disk_status, disk_pct, used_gb, total_gb,
    )
    print(f"Disk     : {used_gb}GB used / {total_gb}GB total")

    logger.info("event=complete overall=%s", disk_status)
    print("Status   : Operational")


if __name__ == "__main__":
    check_system()
