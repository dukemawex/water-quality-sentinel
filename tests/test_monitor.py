"""Tests for the WaterQualityMonitor engine."""

import pytest
from unittest.mock import MagicMock

from water_quality_sentinel.handlers import AlertHandler
from water_quality_sentinel.models import Alert, AlertSeverity, SensorReading, WaterParameter
from water_quality_sentinel.monitor import WaterQualityMonitor
from water_quality_sentinel.thresholds import ThresholdConfig, ParameterThreshold


def _make_ph_monitor(handlers=None) -> WaterQualityMonitor:
    config = ThresholdConfig()
    config.add_threshold(
        ParameterThreshold(
            parameter=WaterParameter.PH,
            warning_min=6.5,
            warning_max=8.5,
            critical_min=6.0,
            critical_max=9.0,
            unit="pH",
        )
    )
    return WaterQualityMonitor(thresholds=config, handlers=handlers or [])


def _make_reading(value: float, param: WaterParameter = WaterParameter.PH) -> SensorReading:
    return SensorReading(
        parameter=param,
        value=value,
        unit="pH",
        sensor_id="test-sensor",
    )


class TestWaterQualityMonitor:
    def test_normal_reading_produces_no_alerts(self):
        monitor = _make_ph_monitor()
        alerts = monitor.process(_make_reading(7.0))
        assert alerts == []

    def test_warning_reading_produces_warning_alert(self):
        monitor = _make_ph_monitor()
        alerts = monitor.process(_make_reading(8.8))
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.WARNING

    def test_critical_reading_produces_critical_alert(self):
        monitor = _make_ph_monitor()
        alerts = monitor.process(_make_reading(9.5))
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.CRITICAL

    def test_alert_handler_is_called(self):
        handler = MagicMock(spec=AlertHandler)
        monitor = _make_ph_monitor(handlers=[handler])
        monitor.process(_make_reading(9.5))
        handler.notify.assert_called_once()
        call_arg = handler.notify.call_args[0][0]
        assert isinstance(call_arg, Alert)
        assert call_arg.severity == AlertSeverity.CRITICAL

    def test_no_handler_called_for_normal_reading(self):
        handler = MagicMock(spec=AlertHandler)
        monitor = _make_ph_monitor(handlers=[handler])
        monitor.process(_make_reading(7.0))
        handler.notify.assert_not_called()

    def test_reading_is_stored(self):
        monitor = _make_ph_monitor()
        reading = _make_reading(7.0)
        monitor.process(reading)
        assert monitor.get_latest_reading(WaterParameter.PH) is reading

    def test_get_active_alerts(self):
        monitor = _make_ph_monitor()
        monitor.process(_make_reading(9.5))
        active = monitor.get_active_alerts()
        assert len(active) == 1

    def test_acknowledge_alert(self):
        monitor = _make_ph_monitor()
        alerts = monitor.process(_make_reading(9.5))
        alert_id = alerts[0].alert_id
        assert monitor.acknowledge_alert(alert_id) is True
        assert monitor.get_active_alerts() == []

    def test_acknowledge_nonexistent_alert(self):
        monitor = _make_ph_monitor()
        assert monitor.acknowledge_alert("bad-id") is False

    def test_status_summary_no_data(self):
        monitor = _make_ph_monitor()
        summary = monitor.get_status_summary()
        assert summary[WaterParameter.PH.value]["status"] == "no_data"

    def test_status_summary_ok(self):
        monitor = _make_ph_monitor()
        monitor.process(_make_reading(7.0))
        summary = monitor.get_status_summary()
        assert summary[WaterParameter.PH.value]["status"] == "ok"

    def test_status_summary_warning(self):
        monitor = _make_ph_monitor()
        monitor.process(_make_reading(8.8))
        summary = monitor.get_status_summary()
        assert summary[WaterParameter.PH.value]["status"] == "warning"

    def test_status_summary_critical(self):
        monitor = _make_ph_monitor()
        monitor.process(_make_reading(9.5))
        summary = monitor.get_status_summary()
        assert summary[WaterParameter.PH.value]["status"] == "critical"

    def test_add_handler(self):
        monitor = _make_ph_monitor()
        handler = MagicMock(spec=AlertHandler)
        monitor.add_handler(handler)
        monitor.process(_make_reading(9.5))
        handler.notify.assert_called_once()

    def test_handler_error_does_not_propagate(self):
        handler = MagicMock(spec=AlertHandler)
        handler.notify.side_effect = RuntimeError("boom")
        monitor = _make_ph_monitor(handlers=[handler])
        # Should not raise
        alerts = monitor.process(_make_reading(9.5))
        assert len(alerts) == 1

    def test_alert_message_contains_direction(self):
        monitor = _make_ph_monitor()
        # Value above threshold
        alerts = monitor.process(_make_reading(9.5))
        assert "above" in alerts[0].message

        monitor2 = _make_ph_monitor()
        # Value below threshold
        alerts2 = monitor2.process(_make_reading(5.5))
        assert "below" in alerts2[0].message
