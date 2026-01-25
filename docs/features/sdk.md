# Python SDK (`dlogs`)

The `dLogs` library provides a wrapper around the standard Python `logging` module to integrate seamlessly with the dLogs stack.

## Installation

```bash
pip install dlogs
```

## Setup in Code

It takes just two lines to start logging structured JSON data that Loki can index.

```python
from dlogs import dLogs

# 1. Initialize
# This creates a file at C:/Logs/my_app_name.json
logger = dLogs("my_app_name")

# 2. Log Information
logger.log("Connecting to database...")

# 3. Log Alerts
# This will be highlighted in Grafana and can trigger notifications
try:
    result = 10 / 0
except ZeroDivisionError:
    logger.alert("Critical Failure: Division by zero!")
```

## How It Works

1.  **File Creation**: The SDK uses a `RotatingFileHandler` to write to `C:/Logs/{app_name}.json`.
2.  **Formatting**: It formats the log record as a single-line JSON object:
    ```json
    {
      "time": "2023-10-25 10:00:00",
      "app": "my_app_name",
      "level": "INFO",
      "msg": "..."
    }
    ```
3.  **Promtail**: The Promtail container has a volume mount on `C:/Logs`. It watches for new lines in `*.json`.
4.  **Ingestion**: Promtail pushes the JSON to Loki with the label `job="varlogs"`.

## Advanced Usage

Since `logger.logger` is a standard `logging.Logger` object, you can pass it to other libraries.

```python
import requests

# Pass the underlying logger to other libs
my_lib.run(logger=logger.logger)
```
