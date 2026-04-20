"""
Lightweight standalone health check — no dependencies beyond stdlib.
For the full-featured version with logging and threshold alerts, use:
    python scripts/run_health_check.py
"""
import os
import platform
import shutil


def check_system() -> None:
    print(f"Host     : {platform.node()}")
    print(f"OS       : {platform.system()} {platform.release()}")
    print(f"CPU      : {os.cpu_count()} logical cores")

    total, used, free = shutil.disk_usage("/")
    print(f"Disk     : {used // (1024**3)}GB used / {total // (1024**3)}GB total")

    print("Status   : Operational")


if __name__ == "__main__":
    check_system()
