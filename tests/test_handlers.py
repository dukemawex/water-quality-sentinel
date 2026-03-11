"""Tests for alert notification handlers."""

import io
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from water_quality_sentinel.handlers import (
    AlertHandler,
    CompositeAlertHandler,
    ConsoleAlertHandler,
    FileAlertHandler,
    LoggingAlertHandler,
)
from water_quality_sentinel.models import Alert, AlertSeverity, SensorReading, WaterParameter


def _make_alert(severity: AlertSeverity = AlertSeverity.WARNING) -> Alert:
    reading = SensorReading(
        parameter=WaterParameter.PH,
        value=9.0,
        unit="pH",
        sensor_id="s1",
        location="Test Site",
    )
    return Alert(
        severity=severity,
        parameter=WaterParameter.PH,
        reading=reading,
        message="pH is high",
        threshold_value=8.5,
    )


class TestLoggingAlertHandler:
    def test_warning_alert_uses_warning_log(self):
        handler = LoggingAlertHandler()
        with patch.object(handler._log, "warning") as mock_warn:
            alert = _make_alert(AlertSeverity.WARNING)
            handler.notify(alert)
            mock_warn.assert_called_once()

    def test_critical_alert_uses_critical_log(self):
        handler = LoggingAlertHandler()
        with patch.object(handler._log, "critical") as mock_crit:
            alert = _make_alert(AlertSeverity.CRITICAL)
            handler.notify(alert)
            mock_crit.assert_called_once()

    def test_info_alert_uses_info_log(self):
        handler = LoggingAlertHandler()
        with patch.object(handler._log, "info") as mock_info:
            alert = _make_alert(AlertSeverity.INFO)
            handler.notify(alert)
            mock_info.assert_called_once()


class TestConsoleAlertHandler:
    def test_notify_prints_to_stdout(self, capsys):
        handler = ConsoleAlertHandler()
        alert = _make_alert(AlertSeverity.CRITICAL)
        handler.notify(alert)
        captured = capsys.readouterr()
        assert "CRITICAL" in captured.out
        assert "pH is high" in captured.out
        assert alert.alert_id in captured.out

    def test_notify_includes_sensor_location(self, capsys):
        handler = ConsoleAlertHandler()
        alert = _make_alert()
        handler.notify(alert)
        captured = capsys.readouterr()
        assert "Test Site" in captured.out


class TestFileAlertHandler:
    def test_notify_writes_to_file(self, tmp_path):
        log_file = tmp_path / "alerts.log"
        handler = FileAlertHandler(log_file)
        alert = _make_alert(AlertSeverity.WARNING)
        handler.notify(alert)
        content = log_file.read_text()
        assert "WARNING" in content
        assert "pH is high" in content

    def test_notify_appends_multiple_alerts(self, tmp_path):
        log_file = tmp_path / "alerts.log"
        handler = FileAlertHandler(log_file)
        handler.notify(_make_alert(AlertSeverity.WARNING))
        handler.notify(_make_alert(AlertSeverity.CRITICAL))
        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 2


class TestCompositeAlertHandler:
    def test_delegates_to_all_handlers(self):
        h1 = MagicMock(spec=AlertHandler)
        h2 = MagicMock(spec=AlertHandler)
        composite = CompositeAlertHandler([h1, h2])
        alert = _make_alert()
        composite.notify(alert)
        h1.notify.assert_called_once_with(alert)
        h2.notify.assert_called_once_with(alert)

    def test_continues_after_handler_error(self):
        h1 = MagicMock(spec=AlertHandler)
        h1.notify.side_effect = RuntimeError("fail")
        h2 = MagicMock(spec=AlertHandler)
        composite = CompositeAlertHandler([h1, h2])
        composite.notify(_make_alert())
        h2.notify.assert_called_once()

    def test_add_handler(self):
        composite = CompositeAlertHandler([])
        h = MagicMock(spec=AlertHandler)
        composite.add_handler(h)
        composite.notify(_make_alert())
        h.notify.assert_called_once()
