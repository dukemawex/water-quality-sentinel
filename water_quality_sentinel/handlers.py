"""
Alert notification handlers for the Water Quality Sentinel.

Supports logging, console, and file-based alert output. New handlers
can be added by subclassing AlertHandler and implementing the ``notify``
method.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .models import Alert, AlertSeverity

logger = logging.getLogger(__name__)


class AlertHandler(ABC):
    """Abstract base class for alert notification handlers."""

    @abstractmethod
    def notify(self, alert: Alert) -> None:
        """Process and dispatch an alert notification.

        Args:
            alert: The alert to notify about.
        """


class LoggingAlertHandler(AlertHandler):
    """Sends alert notifications to the Python logging system.

    WARNING-level alerts use ``logging.warning``; CRITICAL-level alerts use
    ``logging.critical``; INFO-level alerts use ``logging.info``.
    """

    def __init__(self, log_name: str = "water_quality_sentinel.alerts") -> None:
        self._log = logging.getLogger(log_name)

    def notify(self, alert: Alert) -> None:
        level_map = {
            AlertSeverity.INFO: self._log.info,
            AlertSeverity.WARNING: self._log.warning,
            AlertSeverity.CRITICAL: self._log.critical,
        }
        log_fn = level_map.get(alert.severity, self._log.warning)
        log_fn(
            "[%s] %s | sensor=%s | value=%.4f %s | threshold=%.4f | location=%s",
            alert.severity.value.upper(),
            alert.message,
            alert.reading.sensor_id,
            alert.reading.value,
            alert.reading.unit,
            alert.threshold_value,
            alert.reading.location or "unknown",
        )


class ConsoleAlertHandler(AlertHandler):
    """Prints alert notifications to standard output."""

    SEVERITY_COLORS = {
        AlertSeverity.INFO: "\033[34m",       # blue
        AlertSeverity.WARNING: "\033[33m",    # yellow
        AlertSeverity.CRITICAL: "\033[31m",   # red
    }
    RESET = "\033[0m"

    def notify(self, alert: Alert) -> None:
        color = self.SEVERITY_COLORS.get(alert.severity, "")
        ts = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(
            f"{color}[{alert.severity.value.upper()}] {ts} — {alert.message}{self.RESET}\n"
            f"  Sensor:    {alert.reading.sensor_id}"
            + (f" @ {alert.reading.location}" if alert.reading.location else "")
            + f"\n  Value:     {alert.reading.value:.4f} {alert.reading.unit}"
            + f"\n  Threshold: {alert.threshold_value:.4f} {alert.reading.unit}"
            + f"\n  Alert ID:  {alert.alert_id}"
        )


class FileAlertHandler(AlertHandler):
    """Appends alert notifications to a log file.

    Args:
        path: Path to the output log file. The file is created if it does not
            exist.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def notify(self, alert: Alert) -> None:
        ts = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        line = (
            f"[{alert.severity.value.upper()}] {ts} | {alert.message} | "
            f"sensor={alert.reading.sensor_id} | "
            f"value={alert.reading.value:.4f} {alert.reading.unit} | "
            f"threshold={alert.threshold_value:.4f} | "
            f"location={alert.reading.location or 'unknown'} | "
            f"alert_id={alert.alert_id}\n"
        )
        try:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError as exc:
            logger.error("Failed to write alert to %s: %s", self._path, exc)


class CompositeAlertHandler(AlertHandler):
    """Delegates notifications to multiple handlers.

    Args:
        handlers: A list of AlertHandler instances to notify.
    """

    def __init__(self, handlers: List[AlertHandler]) -> None:
        self._handlers = list(handlers)

    def add_handler(self, handler: AlertHandler) -> None:
        """Add a handler to the composite."""
        self._handlers.append(handler)

    def notify(self, alert: Alert) -> None:
        for handler in self._handlers:
            try:
                handler.notify(alert)
            except Exception as exc:  # noqa: BLE001
                logger.error("Alert handler %s raised an error: %s", handler, exc)
