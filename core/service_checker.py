# core/service_checker.py
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from config.settings import SERVICE_LOG_PATH, TARGET_SERVICES  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(SERVICE_LOG_PATH),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class ServiceEntry:
    name: str
    pid: str
    exit_status: str
    is_target: bool = False
    healthy: bool = field(init=False)

    def __post_init__(self):
        self.healthy = self.pid != "-"

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "pid": self.pid,
            "exit_status": self.exit_status,
            "is_target": self.is_target,
            "healthy": self.healthy,
        }


@dataclass
class ServiceCheckResult:
    timestamp: str
    target_names: list[str]
    services: list[ServiceEntry]
    targets: list[ServiceEntry] = field(init=False)
    unhealthy: list[ServiceEntry] = field(init=False)
    overall: str = field(init=False)

    def __post_init__(self):
        self.targets = [s for s in self.services if s.is_target]
        self.unhealthy = [s for s in self.targets if not s.healthy]
        self.overall = "ALERT" if self.unhealthy else "OK"

    def summary(self, show_all: bool = False) -> str:
        display = self.services if show_all else self.targets
        col = "{:<50} {:>8} {:>8} {:<8} {}"
        header = col.format("SERVICE", "PID", "EXIT", "HEALTHY", "FLAG")
        divider = "-" * 84
        lines = [
            "",
            f"  Timestamp  : {self.timestamp}",
            f"  Overall    : {self.overall}",
            f"  Targets    : {len(self.targets)}",
            f"  Unhealthy  : {len(self.unhealthy)}",
            "",
            f"  {'All Services' if show_all else 'Target Services'}:",
            f"  {divider}",
            f"  {header}",
            f"  {divider}",
        ]
        for s in display:
            flag = "⚠️  ALERT" if not s.healthy else ""
            lines.append(
                f"  {col.format(s.name[:49], s.pid, s.exit_status, str(s.healthy), flag)}"
            )
        lines.append(f"  {divider}")
        lines.append("")
        return "\n".join(lines)


def _parse_launchctl_output(output: str, target_names: list[str]) -> list[ServiceEntry]:
    entries: list[ServiceEntry] = []
    for line in output.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("PID"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        pid, exit_status, name = parts
        entries.append(ServiceEntry(
            name=name,
            pid=pid,
            exit_status=exit_status,
            is_target=name in target_names,
        ))
    return entries


def _inject_missing_targets(
    entries: list[ServiceEntry], target_names: list[str]
) -> list[ServiceEntry]:
    found = {e.name for e in entries}
    for name in target_names:
        if name not in found:
            entries.append(ServiceEntry(
                name=name,
                pid="-",
                exit_status="N/A",
                is_target=True,
            ))
            logger.warning("Target service not found in launchctl output: %s", name)
    return entries


def run_service_checks(target_services: list[str] = TARGET_SERVICES) -> ServiceCheckResult:
    logger.info("Starting service check — %d target(s)", len(target_services))

    try:
        proc = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True,
            check=True,
        )
        raw_output = proc.stdout
    except subprocess.CalledProcessError as exc:
        logger.error("launchctl failed (exit %d): %s", exc.returncode, exc.stderr)
        raw_output = ""
    except FileNotFoundError:
        logger.error("launchctl not found — not running on macOS?")
        raw_output = ""

    entries = _parse_launchctl_output(raw_output, target_services)
    entries = _inject_missing_targets(entries, target_services)

    for s in entries:
        if s.is_target:
            if s.healthy:
                logger.info("Service OK — %s (PID %s)", s.name, s.pid)
            else:
                logger.warning(
                    "Service UNHEALTHY — %s (PID %s, exit %s)", s.name, s.pid, s.exit_status
                )

    result = ServiceCheckResult(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        target_names=target_services,
        services=entries,
    )
    logger.info(
        "Service check complete — %d targets, %d unhealthy, overall: %s",
        len(result.targets), len(result.unhealthy), result.overall,
    )
    return result
