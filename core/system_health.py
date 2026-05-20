import json
import logging
import platform
import socket
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import psutil

_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = _ROOT / "config" / "thresholds.json"
_LOG_PATH = _ROOT / "logs" / "health_check.log"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(_LOG_PATH),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def _load_thresholds() -> dict:
    with open(_CONFIG_PATH) as f:
        return json.load(f)


@dataclass
class MetricResult:
    name: str
    value: float
    warn_threshold: float
    crit_threshold: float
    unit: str = "%"
    status: str = field(init=False)

    def __post_init__(self):
        if self.value >= self.crit_threshold:
            self.status = "CRITICAL"
        elif self.value >= self.warn_threshold:
            self.status = "WARNING"
        else:
            self.status = "OK"

    def __str__(self) -> str:
        flag = "!! " if self.status == "CRITICAL" else ("!  " if self.status == "WARNING" else "   ")
        return (
            f"{flag}{self.name:<12} {self.value:>6.1f}{self.unit}"
            f"  (warn: {self.warn_threshold}{self.unit}  crit: {self.crit_threshold}{self.unit})"
            f"  [{self.status}]"
        )


@dataclass
class HealthCheckResult:
    hostname: str
    platform: str
    timestamp: str
    metrics: list[MetricResult]
    overall: str = field(init=False)

    def __post_init__(self):
        if any(m.status == "CRITICAL" for m in self.metrics):
            self.overall = "CRITICAL"
        elif any(m.status == "WARNING" for m in self.metrics):
            self.overall = "WARNING"
        else:
            self.overall = "OK"

    def summary(self) -> str:
        lines = [
            "",
            f"  Host      : {self.hostname}",
            f"  Platform  : {self.platform}",
            f"  Timestamp : {self.timestamp}",
            f"  Overall   : {self.overall}",
            "",
            "  Metrics:",
        ]
        for metric in self.metrics:
            lines.append(f"    {metric}")
        lines.append("")
        return "\n".join(lines)


def check_cpu(warn_threshold: float, crit_threshold: float) -> MetricResult:
    value = psutil.cpu_percent(interval=1)
    result = MetricResult("CPU Usage", value, warn_threshold, crit_threshold)
    level = (
        logging.CRITICAL if result.status == "CRITICAL"
        else logging.WARNING if result.status == "WARNING"
        else logging.INFO
    )
    logger.log(level, "CPU STATUS: %s | usage=%.1f%%", result.status, value)
    return result


def check_memory(warn_threshold: float, crit_threshold: float) -> MetricResult:
    mem = psutil.virtual_memory()
    value = mem.percent
    result = MetricResult("Memory", value, warn_threshold, crit_threshold)
    available_gb = (mem.total - mem.used) / (1024 ** 3)
    level = (
        logging.CRITICAL if result.status == "CRITICAL"
        else logging.WARNING if result.status == "WARNING"
        else logging.INFO
    )
    logger.log(
        level,
        "MEMORY STATUS: %s | usage=%.1f%% available=%.1fGB",
        result.status, value, available_gb,
    )
    return result


def check_disk(warn_threshold: float, crit_threshold: float, path: str = "/") -> MetricResult:
    disk = psutil.disk_usage(path)
    value = disk.percent
    result = MetricResult("Disk Usage", value, warn_threshold, crit_threshold)
    level = (
        logging.CRITICAL if result.status == "CRITICAL"
        else logging.WARNING if result.status == "WARNING"
        else logging.INFO
    )
    logger.log(
        level,
        "DISK STATUS: %s | usage=%.1f%% mount=%s",
        result.status, value, path,
    )
    return result


def run_health_check() -> HealthCheckResult:
    thresholds = _load_thresholds()
    logger.info("HEALTH CHECK: STARTING | host=%s", socket.gethostname())

    metrics = [
        check_cpu(thresholds["cpu_warn"], thresholds["cpu_crit"]),
        check_memory(thresholds["memory_warn"], thresholds["memory_crit"]),
        check_disk(thresholds["disk_warn"], thresholds["disk_crit"]),
    ]

    result = HealthCheckResult(
        hostname=socket.gethostname(),
        platform=f"{platform.system()} {platform.release()}",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        metrics=metrics,
    )

    logger.info("HEALTH CHECK: COMPLETE | overall=%s", result.overall)
    return result
