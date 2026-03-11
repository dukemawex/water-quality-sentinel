"""Tests for threshold configuration and evaluation logic."""

import pytest

from water_quality_sentinel.models import AlertSeverity, WaterParameter
from water_quality_sentinel.thresholds import (
    DEFAULT_THRESHOLDS,
    ParameterThreshold,
    ThresholdConfig,
)


class TestParameterThreshold:
    def _make_ph_threshold(self) -> ParameterThreshold:
        return ParameterThreshold(
            parameter=WaterParameter.PH,
            warning_min=6.5,
            warning_max=8.5,
            critical_min=6.0,
            critical_max=9.0,
            unit="pH",
        )

    def test_value_in_range_returns_none(self):
        threshold = self._make_ph_threshold()
        assert threshold.evaluate(7.0) is None

    def test_warning_high(self):
        threshold = self._make_ph_threshold()
        result = threshold.evaluate(8.8)
        assert result is not None
        severity, threshold_val = result
        assert severity == AlertSeverity.WARNING
        assert threshold_val == 8.5

    def test_warning_low(self):
        threshold = self._make_ph_threshold()
        result = threshold.evaluate(6.4)
        assert result is not None
        severity, _ = result
        assert severity == AlertSeverity.WARNING

    def test_critical_high(self):
        threshold = self._make_ph_threshold()
        result = threshold.evaluate(9.5)
        assert result is not None
        severity, threshold_val = result
        assert severity == AlertSeverity.CRITICAL
        assert threshold_val == 9.0

    def test_critical_low(self):
        threshold = self._make_ph_threshold()
        result = threshold.evaluate(5.5)
        assert result is not None
        severity, _ = result
        assert severity == AlertSeverity.CRITICAL

    def test_boundary_at_warning_max(self):
        threshold = self._make_ph_threshold()
        # Value exactly equal to warning_max should trigger WARNING
        result = threshold.evaluate(8.5)
        assert result is not None
        severity, _ = result
        assert severity == AlertSeverity.WARNING

    def test_boundary_at_critical_max(self):
        threshold = self._make_ph_threshold()
        result = threshold.evaluate(9.0)
        assert result is not None
        severity, _ = result
        assert severity == AlertSeverity.CRITICAL


class TestThresholdConfig:
    def test_add_and_get_threshold(self):
        config = ThresholdConfig()
        threshold = ParameterThreshold(
            parameter=WaterParameter.PH,
            warning_min=6.5,
            warning_max=8.5,
            critical_min=6.0,
            critical_max=9.0,
            unit="pH",
        )
        config.add_threshold(threshold)
        assert config.get_threshold(WaterParameter.PH) is threshold

    def test_get_missing_threshold_returns_none(self):
        config = ThresholdConfig()
        assert config.get_threshold(WaterParameter.PH) is None

    def test_evaluate_missing_parameter_returns_none(self):
        config = ThresholdConfig()
        assert config.evaluate(WaterParameter.PH, 7.0) is None

    def test_evaluate_delegates_to_parameter_threshold(self):
        config = ThresholdConfig()
        threshold = ParameterThreshold(
            parameter=WaterParameter.TEMPERATURE,
            warning_min=5.0,
            warning_max=25.0,
            critical_min=0.0,
            critical_max=35.0,
            unit="°C",
        )
        config.add_threshold(threshold)
        result = config.evaluate(WaterParameter.TEMPERATURE, 30.0)
        assert result is not None
        assert result[0] == AlertSeverity.WARNING


class TestDefaultThresholds:
    def test_all_parameters_have_thresholds(self):
        for param in WaterParameter:
            threshold = DEFAULT_THRESHOLDS.get_threshold(param)
            assert threshold is not None, f"No default threshold for {param}"

    def test_ph_normal_value(self):
        result = DEFAULT_THRESHOLDS.evaluate(WaterParameter.PH, 7.0)
        assert result is None

    def test_ph_critical_high(self):
        result = DEFAULT_THRESHOLDS.evaluate(WaterParameter.PH, 9.5)
        assert result is not None
        assert result[0] == AlertSeverity.CRITICAL

    def test_dissolved_oxygen_critical_low(self):
        result = DEFAULT_THRESHOLDS.evaluate(WaterParameter.DISSOLVED_OXYGEN, 3.0)
        assert result is not None
        assert result[0] == AlertSeverity.CRITICAL

    def test_turbidity_warning_high(self):
        result = DEFAULT_THRESHOLDS.evaluate(WaterParameter.TURBIDITY, 2.0)
        assert result is not None
        assert result[0] == AlertSeverity.WARNING
