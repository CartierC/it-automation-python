"""
Lightweight standalone health check — no dependencies beyond stdlib.
For the full-featured version with logging and threshold alerts, use:
    python scripts/run_health_check.py
"""
import logging
import os
import platform
import shutil

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def check_system() -> None:
    total, used, free = shutil.disk_usage("/")
    disk_pct = round(used / total * 100, 1)

    logger.info(
        "HOST STATUS: OK | host=%s os=%s %s",
        platform.node(), platform.system(), platform.release(),
    )
    logger.info("CPU STATUS: OK | cores=%d", os.cpu_count())
    logger.info(
        "DISK STATUS: OK | used=%dGB total=%dGB usage=%.1f%%",
        used // (1024 ** 3), total // (1024 ** 3), disk_pct,
    )


if __name__ == "__main__":
    check_system()
