"""Tests for the ReadingStore and AlertStore storage backends."""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from water_quality_sentinel.models import (
    Alert,
    AlertSeverity,
    SensorReading,
    WaterParameter,
)
from water_quality_sentinel.storage import AlertStore, ReadingStore


def _make_reading(
    param: WaterParameter = WaterParameter.PH,
    value: float = 7.0,
    sensor_id: str = "s1",
) -> SensorReading:
    return SensorReading(
        parameter=param,
        value=value,
        unit="pH",
        sensor_id=sensor_id,
    )


def _make_alert(reading: SensorReading | None = None) -> Alert:
    if reading is None:
        reading = _make_reading(value=9.5)
    return Alert(
        severity=AlertSeverity.WARNING,
        parameter=reading.parameter,
        reading=reading,
        message="test alert",
        threshold_value=8.5,
    )


class TestReadingStore:
    def test_add_and_get_latest(self):
        store = ReadingStore()
        r1 = _make_reading(value=7.0)
        r2 = _make_reading(value=7.5)
        store.add(r1)
        store.add(r2)
        assert store.get_latest(WaterParameter.PH) is r2

    def test_get_latest_empty_returns_none(self):
        store = ReadingStore()
        assert store.get_latest(WaterParameter.PH) is None

    def test_get_all(self):
        store = ReadingStore()
        r1 = _make_reading(value=7.0)
        r2 = _make_reading(value=7.5)
        store.add(r1)
        store.add(r2)
        all_readings = store.get_all(WaterParameter.PH)
        assert len(all_readings) == 2

    def test_max_readings_pruning(self):
        store = ReadingStore(max_readings_per_parameter=3)
        for i in range(5):
            store.add(_make_reading(value=float(i)))
        readings = store.get_all(WaterParameter.PH)
        assert len(readings) == 3
        # Oldest readings should have been pruned
        assert readings[0].value == 2.0

    def test_get_readings_since(self):
        store = ReadingStore()
        cutoff = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        before = SensorReading(
            parameter=WaterParameter.PH,
            value=7.0,
            unit="pH",
            sensor_id="s1",
            timestamp=datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
        )
        after = SensorReading(
            parameter=WaterParameter.PH,
            value=7.5,
            unit="pH",
            sensor_id="s1",
            timestamp=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        )
        store.add(before)
        store.add(after)
        result = store.get_readings_since(WaterParameter.PH, cutoff)
        assert len(result) == 1
        assert result[0].value == 7.5

    def test_persistence_roundtrip(self, tmp_path):
        path = tmp_path / "readings.json"
        store = ReadingStore(storage_path=path)
        store.add(_make_reading(value=7.2))
        store.add(_make_reading(value=7.8, param=WaterParameter.TEMPERATURE, sensor_id="s2"))

        # Load from same file
        store2 = ReadingStore(storage_path=path)
        assert store2.get_latest(WaterParameter.PH).value == 7.2


class TestAlertStore:
    def test_add_and_get_active(self):
        store = AlertStore()
        alert = _make_alert()
        store.add(alert)
        active = store.get_active()
        assert len(active) == 1
        assert active[0].alert_id == alert.alert_id

    def test_acknowledged_alerts_excluded_from_active(self):
        store = AlertStore()
        alert = _make_alert()
        store.add(alert)
        store.acknowledge(alert.alert_id)
        assert store.get_active() == []

    def test_acknowledge_returns_false_for_unknown_id(self):
        store = AlertStore()
        assert store.acknowledge("nonexistent-id") is False

    def test_get_all_includes_acknowledged(self):
        store = AlertStore()
        a1 = _make_alert()
        a2 = _make_alert()
        store.add(a1)
        store.add(a2)
        store.acknowledge(a1.alert_id)
        assert len(store.get_all()) == 2

    def test_max_alerts_pruning(self):
        store = AlertStore(max_alerts=2)
        for _ in range(4):
            store.add(_make_alert())
        assert len(store.get_all()) == 2

    def test_get_by_id(self):
        store = AlertStore()
        alert = _make_alert()
        store.add(alert)
        found = store.get_by_id(alert.alert_id)
        assert found is alert

    def test_get_by_id_missing_returns_none(self):
        store = AlertStore()
        assert store.get_by_id("no-such-id") is None

    def test_persistence_roundtrip(self, tmp_path):
        path = tmp_path / "alerts.json"
        store = AlertStore(storage_path=path)
        alert = _make_alert()
        store.add(alert)
        store.acknowledge(alert.alert_id)

        store2 = AlertStore(storage_path=path)
        loaded = store2.get_by_id(alert.alert_id)
        assert loaded is not None
        assert loaded.acknowledged is True
