"""
Command-line interface for the Water Quality Sentinel.

Usage examples::

    # Start the sentinel with a simulated data feed
    python -m water_quality_sentinel simulate

    # Submit a single reading via CLI
    python -m water_quality_sentinel read --parameter ph --value 7.2 --sensor sensor-001

    # Show the current status of all monitored parameters
    python -m water_quality_sentinel status

    # List active alerts
    python -m water_quality_sentinel alerts
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import time
from datetime import datetime, timezone

from .handlers import ConsoleAlertHandler
from .models import SensorReading, WaterParameter
from .monitor import WaterQualityMonitor
from .thresholds import DEFAULT_THRESHOLDS


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="water-quality-sentinel",
        description="Water Quality Sentinel — monitor and alert on water quality parameters.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── read ──────────────────────────────────────────────────────────────────
    read_parser = subparsers.add_parser(
        "read",
        help="Submit a single sensor reading.",
    )
    read_parser.add_argument(
        "--parameter",
        required=True,
        choices=[p.value for p in WaterParameter],
        help="Water quality parameter to record.",
    )
    read_parser.add_argument("--value", type=float, required=True, help="Measured value.")
    read_parser.add_argument("--unit", default=None, help="Unit of measurement (optional).")
    read_parser.add_argument(
        "--sensor", default="cli-sensor", help="Sensor identifier (default: cli-sensor)."
    )
    read_parser.add_argument("--location", default=None, help="Location label (optional).")

    # ── status ────────────────────────────────────────────────────────────────
    subparsers.add_parser("status", help="Show the current status of all monitored parameters.")

    # ── alerts ────────────────────────────────────────────────────────────────
    alerts_parser = subparsers.add_parser("alerts", help="List active (unacknowledged) alerts.")
    alerts_parser.add_argument(
        "--all", action="store_true", dest="show_all", help="Show all alerts, including acknowledged."
    )

    # ── simulate ──────────────────────────────────────────────────────────────
    sim_parser = subparsers.add_parser(
        "simulate",
        help="Run a continuous simulation with randomised readings.",
    )
    sim_parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Seconds between simulated readings (default: 2).",
    )
    sim_parser.add_argument(
        "--rounds",
        type=int,
        default=20,
        help="Number of simulated readings to generate (default: 20; 0 = run forever).",
    )

    return parser


def _default_unit(parameter: WaterParameter) -> str:
    threshold = DEFAULT_THRESHOLDS.get_threshold(parameter)
    if threshold:
        return threshold.unit
    return ""


def cmd_read(args: argparse.Namespace, monitor: WaterQualityMonitor) -> None:
    param = WaterParameter(args.parameter)
    unit = args.unit or _default_unit(param)
    reading = SensorReading(
        parameter=param,
        value=args.value,
        unit=unit,
        sensor_id=args.sensor,
        location=args.location,
    )
    alerts = monitor.process(reading)
    if not alerts:
        print(f"✓ Reading accepted — no threshold violations detected.")
    else:
        print(f"⚠ Reading accepted — {len(alerts)} alert(s) generated.")


def cmd_status(monitor: WaterQualityMonitor) -> None:
    summary = monitor.get_status_summary()
    print("\nWater Quality Status")
    print("=" * 50)
    for param, info in summary.items():
        status = info.get("status", "no_data")
        if status == "no_data":
            print(f"  {param:25s} — no data")
        else:
            icon = {"ok": "✓", "warning": "⚠", "critical": "✗"}.get(status, "?")
            print(
                f"  {icon} {param:22s} {info['latest_value']:>10.4f} {info['unit']:<10s}"
                f"  [{status.upper()}]"
            )
    print()


def cmd_alerts(args: argparse.Namespace, monitor: WaterQualityMonitor) -> None:
    alerts = monitor.get_active_alerts() if not args.show_all else monitor.get_all_alerts()
    if not alerts:
        print("No active alerts.")
        return

    for alert in alerts:
        ack = " [ACK]" if alert.acknowledged else ""
        print(
            f"[{alert.severity.value.upper()}]{ack} {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')} "
            f"— {alert.message}"
        )
        print(f"  Alert ID: {alert.alert_id}")


# Simulated "normal" ranges for each parameter
_SIM_RANGES = {
    WaterParameter.PH: (5.8, 9.2),
    WaterParameter.DISSOLVED_OXYGEN: (3.5, 15.0),
    WaterParameter.TURBIDITY: (0.0, 5.0),
    WaterParameter.TEMPERATURE: (-1.0, 36.0),
    WaterParameter.CONDUCTIVITY: (0.0, 1100.0),
    WaterParameter.NITRATES: (0.0, 12.0),
    WaterParameter.PHOSPHATES: (0.0, 0.6),
}


def cmd_simulate(args: argparse.Namespace, monitor: WaterQualityMonitor) -> None:
    params = list(WaterParameter)
    count = 0
    print(f"Starting simulation — interval={args.interval}s, rounds={args.rounds or '∞'}")
    print("Press Ctrl+C to stop.\n")
    try:
        while True:
            param = random.choice(params)
            lo, hi = _SIM_RANGES[param]
            value = round(random.uniform(lo, hi), 4)
            unit = _default_unit(param)
            reading = SensorReading(
                parameter=param,
                value=value,
                unit=unit,
                sensor_id="sim-sensor-01",
                location="Simulation",
            )
            monitor.process(reading)
            count += 1
            if args.rounds and count >= args.rounds:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nSimulation stopped.")

    print(f"\nSimulation complete — {count} readings processed.")
    cmd_status(monitor)


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    monitor = WaterQualityMonitor(handlers=[ConsoleAlertHandler()])

    if args.command == "read":
        cmd_read(args, monitor)
    elif args.command == "status":
        cmd_status(monitor)
    elif args.command == "alerts":
        cmd_alerts(args, monitor)
    elif args.command == "simulate":
        cmd_simulate(args, monitor)


if __name__ == "__main__":
    main()
