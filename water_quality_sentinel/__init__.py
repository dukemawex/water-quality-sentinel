"""
Water Quality Sentinel - A monitoring system for water quality parameters.

This package provides tools to monitor, analyze, and alert on water quality data
from various sensors measuring pH, dissolved oxygen, turbidity, temperature,
conductivity, nitrates, and phosphates.
"""

__version__ = "1.0.0"
__author__ = "Water Quality Sentinel Contributors"

from .models import SensorReading, Alert, AlertSeverity
from .monitor import WaterQualityMonitor
from .thresholds import ThresholdConfig, DEFAULT_THRESHOLDS

__all__ = [
    "SensorReading",
    "Alert",
    "AlertSeverity",
    "WaterQualityMonitor",
    "ThresholdConfig",
    "DEFAULT_THRESHOLDS",
]
