"""Tests for water quality sentinel data models."""

import pytest
from datetime import datetime, timezone

from water_quality_sentinel.models import (
    Alert,
    AlertSeverity,
    SensorReading,
    WaterParameter,
)


class TestSensorReading:
    def test_basic_creation(self):
        reading = SensorReading(
            parameter=WaterParameter.PH,
            value=7.0,
            unit="pH",
            sensor_id="s1",
        )
        assert reading.parameter == WaterParameter.PH
        assert reading.value == 7.0
        assert reading.unit == "pH"
        assert reading.sensor_id == "s1"
        assert reading.location is None
        assert reading.timestamp is not None

    def test_string_parameter_coercion(self):
        reading = SensorReading(
            parameter="ph",  # type: ignore[arg-type]
            value=7.0,
            unit="pH",
            sensor_id="s1",
        )
        assert reading.parameter == WaterParameter.PH

    def test_invalid_parameter_raises(self):
        with pytest.raises(ValueError):
            SensorReading(
                parameter="not_a_parameter",  # type: ignore[arg-type]
                value=7.0,
                unit="pH",
                sensor_id="s1",
            )

    def test_invalid_timestamp_raises(self):
        with pytest.raises(TypeError):
            SensorReading(
                parameter=WaterParameter.PH,
                value=7.0,
                unit="pH",
                sensor_id="s1",
                timestamp="2024-01-01",  # type: ignore[arg-type]
            )

    def test_to_dict(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        reading = SensorReading(
            parameter=WaterParameter.TEMPERATURE,
            value=20.5,
            unit="°C",
            sensor_id="s2",
            timestamp=ts,
            location="Lake A",
        )
        d = reading.to_dict()
        assert d["parameter"] == "temperature"
        assert d["value"] == 20.5
        assert d["unit"] == "°C"
        assert d["sensor_id"] == "s2"
        assert d["location"] == "Lake A"
        assert d["timestamp"] == ts.isoformat()

    def test_from_dict_roundtrip(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        original = SensorReading(
            parameter=WaterParameter.TURBIDITY,
            value=0.5,
            unit="NTU",
            sensor_id="s3",
            timestamp=ts,
            location="River B",
        )
        restored = SensorReading.from_dict(original.to_dict())
        assert restored.parameter == original.parameter
        assert restored.value == original.value
        assert restored.unit == original.unit
        assert restored.sensor_id == original.sensor_id
        assert restored.timestamp == original.timestamp
        assert restored.location == original.location


class TestAlert:
    def _make_reading(self, value: float = 9.5) -> SensorReading:
        return SensorReading(
            parameter=WaterParameter.PH,
            value=value,
            unit="pH",
            sensor_id="s1",
        )

    def test_basic_creation(self):
        reading = self._make_reading()
        alert = Alert(
            severity=AlertSeverity.WARNING,
            parameter=WaterParameter.PH,
            reading=reading,
            message="pH is too high",
            threshold_value=8.5,
        )
        assert alert.severity == AlertSeverity.WARNING
        assert not alert.acknowledged
        assert alert.alert_id  # has a value

    def test_acknowledge(self):
        reading = self._make_reading()
        alert = Alert(
            severity=AlertSeverity.CRITICAL,
            parameter=WaterParameter.PH,
            reading=reading,
            message="pH is critical",
            threshold_value=9.0,
        )
        assert not alert.acknowledged
        alert.acknowledge()
        assert alert.acknowledged

    def test_to_dict_contains_reading(self):
        reading = self._make_reading()
        alert = Alert(
            severity=AlertSeverity.WARNING,
            parameter=WaterParameter.PH,
            reading=reading,
            message="msg",
            threshold_value=8.5,
        )
        d = alert.to_dict()
        assert "reading" in d
        assert d["reading"]["parameter"] == "ph"
        assert d["severity"] == "warning"
        assert d["acknowledged"] is False
