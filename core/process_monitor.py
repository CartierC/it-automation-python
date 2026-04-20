# core/process_monitor.py
import logging
import os
import signal
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil

_ROOT = Path(__file__).resolve().parents[1]

import sys
sys.path.insert(0, str(_ROOT))
from config.settings import PROCESS_CPU_THRESHOLD, PROCESS_TOP_N, PROCESS_LOG_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(PROCESS_LOG_PATH),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessEntry:
    pid: int
    name: str
    cpu_percent: float
    mem_percent: float
    status: str
    flagged: bool = field(init=False)
    is_zombie: bool = field(init=False)

    def __post_init__(self):
        self.is_zombie = self.status == "zombie"
        self.flagged = self.is_zombie or self.cpu_percent >= PROCESS_CPU_THRESHOLD

    def as_dict(self) -> dict:
        return {
            "pid": self.pid,
            "name": self.name,
            "cpu_percent": self.cpu_percent,
            "mem_percent": round(self.mem_percent, 2),
            "status": self.status,
            "flagged": self.flagged,
            "is_zombie": self.is_zombie,
        }


@dataclass
class ProcessMonitorResult:
    timestamp: str
    top_n: int
    cpu_threshold: float
    processes: list[ProcessEntry]
    zombies: list[ProcessEntry] = field(init=False)
    flagged: list[ProcessEntry] = field(init=False)
    overall: str = field(init=False)

    def __post_init__(self):
        self.zombies = [p for p in self.processes if p.is_zombie]
        self.flagged = [p for p in self.processes if p.flagged]
        self.overall = "ALERT" if self.flagged else "OK"

    def summary(self) -> str:
        col = "{:<7} {:<28} {:>7} {:>7} {:<12} {}"
        header = col.format("PID", "NAME", "CPU%", "MEM%", "STATUS", "FLAG")
        divider = "-" * 72
        rows = [
            col.format(
                p.pid,
                p.name[:27],
                f"{p.cpu_percent:.1f}",
                f"{p.mem_percent:.1f}",
                p.status,
                "⚠️  ALERT" if p.flagged else "",
            )
            for p in self.processes
        ]
        lines = [
            "",
            f"  Timestamp  : {self.timestamp}",
            f"  Overall    : {self.overall}",
            f"  Threshold  : CPU > {self.cpu_threshold}%",
            f"  Zombies    : {len(self.zombies)}",
            f"  Flagged    : {len(self.flagged)}",
            "",
            f"  Top {self.top_n} Processes by CPU:",
            f"  {divider}",
            f"  {header}",
            f"  {divider}",
        ]
        for row in rows:
            lines.append(f"  {row}")
        lines.append(f"  {divider}")
        lines.append("")
        return "\n".join(lines)


def _collect_processes() -> list[dict]:
    attrs = ["pid", "name", "cpu_percent", "memory_percent", "status"]
    procs = []
    for proc in psutil.process_iter(attrs, ad_value=None):
        info = proc.info
        if any(v is None for v in info.values()):
            continue
        procs.append(info)
    return procs


def get_top_processes(top_n: int = PROCESS_TOP_N) -> list[ProcessEntry]:
    # Two-pass CPU sampling — first call always returns 0.0; interval=0.1 gives a real reading
    for proc in psutil.process_iter(["cpu_percent"]):
        try:
            proc.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    import time
    time.sleep(0.5)

    raw = _collect_processes()
    raw.sort(key=lambda p: p["cpu_percent"] or 0.0, reverse=True)
    top = raw[:top_n]

    entries = [
        ProcessEntry(
            pid=p["pid"],
            name=p["name"] or "unknown",
            cpu_percent=round(p["cpu_percent"] or 0.0, 1),
            mem_percent=p["memory_percent"] or 0.0,
            status=p["status"] or "unknown",
        )
        for p in top
    ]

    for entry in entries:
        if entry.is_zombie:
            logger.warning("Zombie process detected — PID %d (%s)", entry.pid, entry.name)
        elif entry.flagged:
            logger.warning(
                "CPU threshold breach — PID %d (%s) at %.1f%% (threshold %.0f%%)",
                entry.pid, entry.name, entry.cpu_percent, PROCESS_CPU_THRESHOLD,
            )
        else:
            logger.info("Process — PID %d (%s) CPU %.1f%% MEM %.1f%%",
                        entry.pid, entry.name, entry.cpu_percent, entry.mem_percent)

    return entries


def kill_process(pid: int) -> bool:
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.send_signal(signal.SIGTERM)
        logger.info("SIGTERM sent to PID %d (%s)", pid, name)
        return True
    except psutil.NoSuchProcess:
        logger.error("Kill failed — PID %d does not exist", pid)
        return False
    except psutil.AccessDenied:
        logger.error("Kill failed — access denied for PID %d", pid)
        return False


def run_process_monitor(top_n: int = PROCESS_TOP_N) -> ProcessMonitorResult:
    logger.info("Starting process monitor — top %d, CPU threshold %.0f%%", top_n, PROCESS_CPU_THRESHOLD)
    processes = get_top_processes(top_n)
    result = ProcessMonitorResult(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        top_n=top_n,
        cpu_threshold=PROCESS_CPU_THRESHOLD,
        processes=processes,
    )
    logger.info(
        "Process monitor complete — %d processes, %d flagged, overall: %s",
        len(processes), len(result.flagged), result.overall,
    )
    return result
