# Water Quality Sentinel

A Python monitoring system for water quality parameters. It ingests sensor
readings, evaluates them against configurable thresholds, and dispatches
alerts when water quality falls outside safe ranges.

## Features

- **Multi-parameter monitoring** — pH, dissolved oxygen, turbidity, temperature,
  conductivity, nitrates, and phosphates.
- **Two-level alerting** — WARNING and CRITICAL thresholds based on EPA / WHO
  water-quality guidelines (fully customisable).
- **Pluggable notification handlers** — built-in support for logging, console
  output, and file-based logs; extend easily with your own handlers.
- **Persistent storage** — optional JSON-backed storage for readings and alerts
  across restarts.
- **CLI interface** — submit readings, view live status, list alerts, and run
  a simulated data feed from the command line.
- **Zero runtime dependencies** — requires only the Python standard library.

## Quick Start

### Installation

```bash
pip install water-quality-sentinel
```

Or install from source:

```bash
git clone https://github.com/dukemawex/water-quality-sentinel.git
cd water-quality-sentinel
pip install -e ".[dev]"
```

### CLI Usage

```bash
# Submit a single sensor reading
water-quality-sentinel read --parameter ph --value 7.2 --sensor sensor-001

# View current status of all monitored parameters
water-quality-sentinel status

# List active (unacknowledged) alerts
water-quality-sentinel alerts

# Run a simulation with randomised readings
water-quality-sentinel simulate --rounds 20 --interval 1
```

### Python API

```python
from water_quality_sentinel import (
    WaterQualityMonitor,
    SensorReading,
    WaterParameter,
)
from water_quality_sentinel.handlers import ConsoleAlertHandler

# Create a monitor with console alert output
monitor = WaterQualityMonitor(handlers=[ConsoleAlertHandler()])

# Submit a sensor reading
reading = SensorReading(
    parameter=WaterParameter.PH,
    value=9.5,           # exceeds critical threshold of 9.0
    unit="pH",
    sensor_id="sensor-001",
    location="Intake A",
)
alerts = monitor.process(reading)
# → prints a CRITICAL alert to the console

# Check the current status of all parameters
print(monitor.get_status_summary())

# Acknowledge an alert
if alerts:
    monitor.acknowledge_alert(alerts[0].alert_id)
```

## Monitored Parameters and Default Thresholds

| Parameter           | Unit   | Warning Range | Critical Range |
|---------------------|--------|---------------|----------------|
| pH                  | pH     | 6.5 – 8.5     | 6.0 – 9.0      |
| Dissolved Oxygen    | mg/L   | 6.0 – 14.0    | 4.0 – 16.0     |
| Turbidity           | NTU    | 0.0 – 1.0     | 0.0 – 4.0      |
| Temperature         | °C     | 5.0 – 25.0    | 0.0 – 35.0     |
| Conductivity        | µS/cm  | 50 – 500      | 0 – 1000       |
| Nitrates            | mg/L   | 0.0 – 5.0     | 0.0 – 10.0     |
| Phosphates          | mg/L   | 0.0 – 0.1     | 0.0 – 0.5      |

## Custom Thresholds

```python
from water_quality_sentinel.thresholds import ThresholdConfig, ParameterThreshold
from water_quality_sentinel.models import WaterParameter

config = ThresholdConfig()
config.add_threshold(
    ParameterThreshold(
        parameter=WaterParameter.PH,
        warning_min=6.8,
        warning_max=7.8,
        critical_min=6.0,
        critical_max=9.0,
        unit="pH",
    )
)

monitor = WaterQualityMonitor(thresholds=config)
```

## Custom Alert Handlers

```python
from water_quality_sentinel.handlers import AlertHandler
from water_quality_sentinel.models import Alert

class WebhookAlertHandler(AlertHandler):
    def notify(self, alert: Alert) -> None:
        # Post alert to an external webhook, e.g. Slack, PagerDuty, etc.
        payload = alert.to_dict()
        ...

monitor = WaterQualityMonitor(handlers=[WebhookAlertHandler()])
```

## Persistent Storage

```python
from pathlib import Path
from water_quality_sentinel.storage import ReadingStore, AlertStore

monitor = WaterQualityMonitor(
    reading_store=ReadingStore(storage_path=Path("readings.json")),
    alert_store=AlertStore(storage_path=Path("alerts.json")),
)
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=water_quality_sentinel
```

## Architecture

```
water_quality_sentinel/
├── __init__.py        Public API
├── __main__.py        python -m entry point
├── cli.py             Command-line interface
├── models.py          SensorReading, Alert, WaterParameter, AlertSeverity
├── thresholds.py      ParameterThreshold, ThresholdConfig, DEFAULT_THRESHOLDS
├── monitor.py         WaterQualityMonitor (core engine)
├── storage.py         ReadingStore, AlertStore
└── handlers.py        AlertHandler, LoggingAlertHandler, ConsoleAlertHandler,
                       FileAlertHandler, CompositeAlertHandler
```

## License

MIT — see [LICENSE](LICENSE) for details.