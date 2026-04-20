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
    format="%(asctime)s  %(levelname)-8s  %(message)s",
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
    threshold: float
    unit: str = "%"
    status: str = field(init=False)

    def __post_init__(self):
        self.status = "ALERT" if self.value >= self.threshold else "OK"

    def __str__(self) -> str:
        flag = "⚠️ " if self.status == "ALERT" else "✓  "
        return f"{flag}{self.name:<12} {self.value:>6.1f}{self.unit}  (threshold: {self.threshold}{self.unit})  [{self.status}]"


@dataclass
class HealthCheckResult:
    hostname: str
    platform: str
    timestamp: str
    metrics: list[MetricResult]
    overall: str = field(init=False)

    def __post_init__(self):
        self.overall = "ALERT" if any(m.status == "ALERT" for m in self.metrics) else "OK"

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


def check_cpu(threshold: float) -> MetricResult:
    value = psutil.cpu_percent(interval=1)
    result = MetricResult("CPU Usage", value, threshold)
    logger.info("CPU check — %.1f%% (threshold %.0f%%) [%s]", value, threshold, result.status)
    return result


def check_memory(threshold: float) -> MetricResult:
    mem = psutil.virtual_memory()
    value = mem.percent
    result = MetricResult("Memory", value, threshold)
    logger.info(
        "Memory check — %.1f%% used of %.1fGB (threshold %.0f%%) [%s]",
        value,
        mem.total / (1024 ** 3),
        threshold,
        result.status,
    )
    return result


def check_disk(threshold: float, path: str = "/") -> MetricResult:
    disk = psutil.disk_usage(path)
    value = disk.percent
    result = MetricResult("Disk Usage", value, threshold)
    logger.info(
        "Disk check — %.1f%% used of %.1fGB at %s (threshold %.0f%%) [%s]",
        value,
        disk.total / (1024 ** 3),
        path,
        threshold,
        result.status,
    )
    return result


def run_health_check() -> HealthCheckResult:
    thresholds = _load_thresholds()
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

    logger.info("Health check complete — overall status: %s", result.overall)
    return result
