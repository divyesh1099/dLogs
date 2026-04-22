# Python SDK

The `motidivya-dlogs` package includes a simple, zero-dependency SDK for Python applications.

## Installation

```bash
pip install motidivya-dlogs
```

## Usage

### Basic Initialization

```python
from dlogs import dLogs

# Initialize logger for your application
# This writes to the default OS-specific log directory
# Windows: C:/Logs/my-app.json
# Linux/macOS: ~/dlogs/my-app.json
# You can override both with DLOGS_LOG_DIR
logger = dLogs("my-app")

logger.log("Info message")
logger.alert("Error message")
```

### Advanced Usage

The `dLogs` class automatically handles JSON formatting so that Promtail can parse it into key-value pairs in Loki.

**Structure:**

```json
{
  "time": "2023-10-27 10:00:00",
  "app": "my-app",
  "level": "INFO",
  "msg": "Info message"
}
```

This structure allows you to query in Grafana:
`{app="my-app"} |= "Info message"`
