"""
Storage module for water quality readings and alerts.

Provides an in-memory storage backend and an optional file-based persistent
storage using JSON, allowing the sentinel to retain data across restarts.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .models import Alert, SensorReading, WaterParameter

logger = logging.getLogger(__name__)


class ReadingStore:
    """Stores sensor readings in memory with optional JSON file persistence.

    Attributes:
        max_readings_per_parameter: Maximum number of readings to keep in
            memory per parameter. Oldest readings are pruned when this limit
            is reached.
    """

    def __init__(
        self,
        max_readings_per_parameter: int = 1000,
        storage_path: Optional[Path] = None,
    ) -> None:
        self._readings: Dict[WaterParameter, List[SensorReading]] = {
            param: [] for param in WaterParameter
        }
        self.max_readings_per_parameter = max_readings_per_parameter
        self._storage_path = storage_path

        if storage_path and storage_path.exists():
            self._load(storage_path)

    def add(self, reading: SensorReading) -> None:
        """Add a sensor reading to the store."""
        readings = self._readings[reading.parameter]
        readings.append(reading)
        if len(readings) > self.max_readings_per_parameter:
            readings.pop(0)

        if self._storage_path:
            self._save(self._storage_path)

    def get_latest(self, parameter: WaterParameter) -> Optional[SensorReading]:
        """Get the most recent reading for a parameter."""
        readings = self._readings[parameter]
        return readings[-1] if readings else None

    def get_all(self, parameter: WaterParameter) -> List[SensorReading]:
        """Get all stored readings for a parameter."""
        return list(self._readings[parameter])

    def get_readings_since(
        self, parameter: WaterParameter, since: datetime
    ) -> List[SensorReading]:
        """Get all readings for a parameter recorded after a given time."""
        return [r for r in self._readings[parameter] if r.timestamp >= since]

    def _save(self, path: Path) -> None:
        """Persist all readings to a JSON file."""
        data: Dict[str, list] = {}
        for param, readings in self._readings.items():
            data[param.value] = [r.to_dict() for r in readings]
        try:
            path.write_text(json.dumps(data, indent=2))
        except OSError as exc:
            logger.error("Failed to save readings to %s: %s", path, exc)

    def _load(self, path: Path) -> None:
        """Load readings from a JSON file."""
        try:
            raw = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to load readings from %s: %s", path, exc)
            return

        for param_str, readings in raw.items():
            try:
                param = WaterParameter(param_str)
                self._readings[param] = [SensorReading.from_dict(r) for r in readings]
            except (KeyError, ValueError) as exc:
                logger.warning("Skipping invalid reading data for %s: %s", param_str, exc)


class AlertStore:
    """Stores alerts in memory with optional JSON file persistence.

    Attributes:
        max_alerts: Maximum number of alerts to keep in memory. Oldest alerts
            are pruned when this limit is reached.
    """

    def __init__(
        self,
        max_alerts: int = 500,
        storage_path: Optional[Path] = None,
    ) -> None:
        self._alerts: List[Alert] = []
        self.max_alerts = max_alerts
        self._storage_path = storage_path

        if storage_path and storage_path.exists():
            self._load(storage_path)

    def add(self, alert: Alert) -> None:
        """Add an alert to the store."""
        self._alerts.append(alert)
        if len(self._alerts) > self.max_alerts:
            self._alerts.pop(0)

        if self._storage_path:
            self._save(self._storage_path)

    def get_active(self) -> List[Alert]:
        """Get all unacknowledged alerts."""
        return [a for a in self._alerts if not a.acknowledged]

    def get_all(self) -> List[Alert]:
        """Get all stored alerts."""
        return list(self._alerts)

    def get_by_id(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by its unique identifier."""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                return alert
        return None

    def acknowledge(self, alert_id: str) -> bool:
        """Acknowledge an alert by ID. Returns True if the alert was found."""
        alert = self.get_by_id(alert_id)
        if alert:
            alert.acknowledge()
            if self._storage_path:
                self._save(self._storage_path)
            return True
        return False

    def _save(self, path: Path) -> None:
        """Persist all alerts to a JSON file."""
        data = [a.to_dict() for a in self._alerts]
        try:
            path.write_text(json.dumps(data, indent=2))
        except OSError as exc:
            logger.error("Failed to save alerts to %s: %s", path, exc)

    def _load(self, path: Path) -> None:
        """Load alerts from a JSON file (metadata only, no linked readings)."""
        try:
            raw = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to load alerts from %s: %s", path, exc)
            return

        for item in raw:
            try:
                reading = SensorReading.from_dict(item["reading"])
                alert = Alert(
                    alert_id=item["alert_id"],
                    severity=item["severity"],
                    parameter=item["parameter"],
                    reading=reading,
                    message=item["message"],
                    threshold_value=float(item["threshold_value"]),
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    acknowledged=item.get("acknowledged", False),
                )
                self._alerts.append(alert)
            except (KeyError, ValueError, TypeError) as exc:
                logger.warning("Skipping invalid alert data: %s", exc)
