"""Tests for the CLI interface."""

import pytest
from unittest.mock import patch

from water_quality_sentinel.cli import main
from water_quality_sentinel.models import WaterParameter


class TestCLIRead:
    def test_read_normal_value_no_alerts(self, capsys):
        main(["read", "--parameter", "ph", "--value", "7.0", "--sensor", "test-s"])
        captured = capsys.readouterr()
        assert "no threshold violations" in captured.out

    def test_read_critical_value_prints_alert(self, capsys):
        main(["read", "--parameter", "ph", "--value", "10.0", "--sensor", "test-s"])
        captured = capsys.readouterr()
        assert "alert(s) generated" in captured.out

    def test_read_with_location(self, capsys):
        main(
            [
                "read",
                "--parameter",
                "temperature",
                "--value",
                "20.0",
                "--sensor",
                "test-s",
                "--location",
                "Site A",
            ]
        )
        captured = capsys.readouterr()
        assert "no threshold violations" in captured.out


class TestCLIStatus:
    def test_status_shows_no_data_for_empty_monitor(self, capsys):
        main(["status"])
        captured = capsys.readouterr()
        assert "no data" in captured.out


class TestCLISimulate:
    def test_simulate_runs_fixed_rounds(self, capsys):
        main(["simulate", "--rounds", "5", "--interval", "0"])
        captured = capsys.readouterr()
        assert "5 readings processed" in captured.out
