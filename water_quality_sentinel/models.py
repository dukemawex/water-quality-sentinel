"""
Data models for the Water Quality Sentinel system.

Defines core data structures used across the application including sensor
readings and alert objects.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class AlertSeverity(str, Enum):
    """Severity levels for water quality alerts."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class WaterParameter(str, Enum):
    """Water quality parameters that can be monitored."""

    PH = "ph"
    DISSOLVED_OXYGEN = "dissolved_oxygen"
    TURBIDITY = "turbidity"
    TEMPERATURE = "temperature"
    CONDUCTIVITY = "conductivity"
    NITRATES = "nitrates"
    PHOSPHATES = "phosphates"


@dataclass
class SensorReading:
    """Represents a single reading from a water quality sensor.

    Attributes:
        parameter: The water quality parameter being measured.
        value: The measured value.
        unit: The unit of measurement (e.g., "mg/L", "NTU", "°C").
        sensor_id: Identifier for the sensor that produced the reading.
        timestamp: When the reading was taken (UTC).
        location: Optional location label for the sensor.
    """

    parameter: WaterParameter
    value: float
    unit: str
    sensor_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    location: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.parameter, WaterParameter):
            self.parameter = WaterParameter(self.parameter)
        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime object")

    def to_dict(self) -> dict:
        """Serialize the reading to a dictionary."""
        return {
            "parameter": self.parameter.value,
            "value": self.value,
            "unit": self.unit,
            "sensor_id": self.sensor_id,
            "timestamp": self.timestamp.isoformat(),
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SensorReading":
        """Deserialize a reading from a dictionary."""
        return cls(
            parameter=WaterParameter(data["parameter"]),
            value=float(data["value"]),
            unit=data["unit"],
            sensor_id=data["sensor_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            location=data.get("location"),
        )


@dataclass
class Alert:
    """Represents an alert triggered by a water quality threshold violation.

    Attributes:
        alert_id: Unique identifier for the alert.
        severity: The severity level of the alert.
        parameter: The water quality parameter that triggered the alert.
        reading: The sensor reading that caused the alert.
        message: Human-readable description of the alert.
        threshold_value: The threshold value that was exceeded.
        timestamp: When the alert was generated (UTC).
        acknowledged: Whether the alert has been acknowledged.
    """

    severity: AlertSeverity
    parameter: WaterParameter
    reading: SensorReading
    message: str
    threshold_value: float
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False

    def acknowledge(self) -> None:
        """Mark this alert as acknowledged."""
        self.acknowledged = True

    def to_dict(self) -> dict:
        """Serialize the alert to a dictionary."""
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "parameter": self.parameter.value,
            "reading": self.reading.to_dict(),
            "message": self.message,
            "threshold_value": self.threshold_value,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
        }
