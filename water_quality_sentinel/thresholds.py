"""
Threshold configuration for water quality parameters.

Defines acceptable ranges for each water quality parameter and provides
the logic to evaluate whether a reading violates configured thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from .models import AlertSeverity, WaterParameter


@dataclass
class ParameterThreshold:
    """Threshold configuration for a single water quality parameter.

    Attributes:
        parameter: The water quality parameter this threshold applies to.
        warning_min: Lower bound below which a WARNING alert is triggered.
        warning_max: Upper bound above which a WARNING alert is triggered.
        critical_min: Lower bound below which a CRITICAL alert is triggered.
        critical_max: Upper bound above which a CRITICAL alert is triggered.
        unit: The unit of measurement for display purposes.
    """

    parameter: WaterParameter
    warning_min: float
    warning_max: float
    critical_min: float
    critical_max: float
    unit: str

    def evaluate(self, value: float) -> Optional[Tuple[AlertSeverity, float]]:
        """Evaluate a value against the threshold.

        Returns:
            A tuple of (severity, threshold_value) if the value violates a
            threshold, or None if the value is within acceptable range.
        """
        if value <= self.critical_min:
            return AlertSeverity.CRITICAL, self.critical_min
        if value >= self.critical_max:
            return AlertSeverity.CRITICAL, self.critical_max
        if value <= self.warning_min:
            return AlertSeverity.WARNING, self.warning_min
        if value >= self.warning_max:
            return AlertSeverity.WARNING, self.warning_max
        return None


@dataclass
class ThresholdConfig:
    """Collection of threshold configurations for all monitored parameters.

    Attributes:
        thresholds: Mapping of parameter to its threshold configuration.
    """

    thresholds: Dict[WaterParameter, ParameterThreshold] = field(default_factory=dict)

    def add_threshold(self, threshold: ParameterThreshold) -> None:
        """Add or update a threshold configuration."""
        self.thresholds[threshold.parameter] = threshold

    def get_threshold(self, parameter: WaterParameter) -> Optional[ParameterThreshold]:
        """Get the threshold configuration for a parameter."""
        return self.thresholds.get(parameter)

    def evaluate(self, parameter: WaterParameter, value: float) -> Optional[Tuple[AlertSeverity, float]]:
        """Evaluate a value for a given parameter against its threshold.

        Returns:
            A tuple of (severity, threshold_value) if the value violates a
            threshold, or None if no threshold is configured or the value is
            within acceptable range.
        """
        threshold = self.get_threshold(parameter)
        if threshold is None:
            return None
        return threshold.evaluate(value)


# Default thresholds based on EPA and WHO water quality guidelines
DEFAULT_THRESHOLDS = ThresholdConfig(
    thresholds={
        WaterParameter.PH: ParameterThreshold(
            parameter=WaterParameter.PH,
            warning_min=6.5,
            warning_max=8.5,
            critical_min=6.0,
            critical_max=9.0,
            unit="pH",
        ),
        WaterParameter.DISSOLVED_OXYGEN: ParameterThreshold(
            parameter=WaterParameter.DISSOLVED_OXYGEN,
            warning_min=6.0,
            warning_max=14.0,
            critical_min=4.0,
            critical_max=16.0,
            unit="mg/L",
        ),
        WaterParameter.TURBIDITY: ParameterThreshold(
            parameter=WaterParameter.TURBIDITY,
            warning_min=0.0,
            warning_max=1.0,
            critical_min=0.0,
            critical_max=4.0,
            unit="NTU",
        ),
        WaterParameter.TEMPERATURE: ParameterThreshold(
            parameter=WaterParameter.TEMPERATURE,
            warning_min=5.0,
            warning_max=25.0,
            critical_min=0.0,
            critical_max=35.0,
            unit="°C",
        ),
        WaterParameter.CONDUCTIVITY: ParameterThreshold(
            parameter=WaterParameter.CONDUCTIVITY,
            warning_min=50.0,
            warning_max=500.0,
            critical_min=0.0,
            critical_max=1000.0,
            unit="µS/cm",
        ),
        WaterParameter.NITRATES: ParameterThreshold(
            parameter=WaterParameter.NITRATES,
            warning_min=0.0,
            warning_max=5.0,
            critical_min=0.0,
            critical_max=10.0,
            unit="mg/L",
        ),
        WaterParameter.PHOSPHATES: ParameterThreshold(
            parameter=WaterParameter.PHOSPHATES,
            warning_min=0.0,
            warning_max=0.1,
            critical_min=0.0,
            critical_max=0.5,
            unit="mg/L",
        ),
    }
)
