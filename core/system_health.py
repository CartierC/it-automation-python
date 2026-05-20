import json
import logging
import platform
import socket
import time
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

CPU_WARN = 80
CPU_CRIT = 95
MEM_WARN = 80
MEM_CRIT = 95
DISK_WARN = 85
DISK_CRIT = 95


def _load_thresholds() -> dict:
    with open(_CONFIG_PATH) as f:
        return json.load(f)


@dataclass
class MetricResult:
    name: str
    value: float
    threshold: float
    crit_threshold: float = 0.0
    unit: str = "%"
    status: str = field(init=False)

    def __post_init__(self):
        if self.crit_threshold > 0 and self.value >= self.crit_threshold:
            self.status = "CRITICAL"
        elif self.value >= self.threshold:
            self.status = "WARNING"
        else:
            self.status = "OK"

    def __str__(self) -> str:
        flag = "✓  " if self.status == "OK" else "⚠️ "
        return (
            f"{flag}{self.name:<12} {self.value:>6.1f}{self.unit}"
            f"  (warn: {self.threshold}{self.unit}, crit: {self.crit_threshold}{self.unit})  [{self.status}]"
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


def check_cpu(threshold: float = CPU_WARN, crit_threshold: float = CPU_CRIT) -> MetricResult:
    value = psutil.cpu_percent(interval=1)
    result = MetricResult("CPU Usage", value, threshold, crit_threshold)
    msg = f"CPU STATUS: {result.status} | usage={value:.1f}%"
    if result.status == "CRITICAL":
        logger.critical(msg)
    elif result.status == "WARNING":
        logger.warning(msg)
    else:
        logger.info(msg)
    return result


def check_memory(threshold: float = MEM_WARN, crit_threshold: float = MEM_CRIT) -> MetricResult:
    mem = psutil.virtual_memory()
    value = mem.percent
    available_gb = mem.available / (1024 ** 3)
    result = MetricResult("Memory", value, threshold, crit_threshold)
    msg = f"MEMORY STATUS: {result.status} | usage={value:.1f}% available={available_gb:.1f}GB"
    if result.status == "CRITICAL":
        logger.critical(msg)
    elif result.status == "WARNING":
        logger.warning(msg)
    else:
        logger.info(msg)
    return result


def check_disk(threshold: float = DISK_WARN, crit_threshold: float = DISK_CRIT, path: str = "/") -> MetricResult:
    disk = psutil.disk_usage(path)
    value = disk.percent
    result = MetricResult("Disk Usage", value, threshold, crit_threshold)
    msg = f"DISK STATUS: {result.status} | usage={value:.1f}% mount={path}"
    if result.status == "CRITICAL":
        logger.critical(msg)
    elif result.status == "WARNING":
        logger.warning(msg)
    else:
        logger.info(msg)
    return result


def run_health_check() -> HealthCheckResult:
    thresholds = _load_thresholds()
    t0 = time.perf_counter()
    logger.info("Starting health check on %s", socket.gethostname())

    metrics = [
        check_cpu(thresholds["cpu_percent"]),
        check_memory(thresholds["memory_percent"]),
        check_disk(thresholds["disk_percent"]),
    ]

    result = HealthCheckResult(
        hostname=socket.gethostname(),
        platform=f"{platform.system()} {platform.release()}",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        metrics=metrics,
    )

    duration = time.perf_counter() - t0
    exit_code = 0 if result.overall == "OK" else (2 if result.overall == "CRITICAL" else 1)
    logger.info(
        "Health check completed | exit_code=%d duration=%.2fs",
        exit_code,
        duration,
    )
    return result
