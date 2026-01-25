# dLogs: The "1-Click" Observability Stack

[![PyPI version](https://badge.fury.io/py/motidivya-dlogs.svg)](https://badge.fury.io/py/motidivya-dlogs)
[![Docker Image](https://img.shields.io/docker/v/divyesh1099/dlogs?label=docker&logo=docker)](https://hub.docker.com/r/divyesh1099/dlogs)

> **Monitor Everything.** Windows Host, Docker Containers, Nvidia GPUs, and App Logs. All in one place.

`dLogs` is a pre-configured, high-performance observability stack built on top of the industry-standard LGTM stack (**L**oki, **G**rafana, **T**elegraf/Promtail, **M**onitoring/Prometheus), enhanced with automatic dashboard provisioning and Python integration.

---

## 🚀 Features

- **⚡ Instant Setup**: Install via pip or Docker.
- **🖥️ Full Windows Visibility**: CPU, RAM, Disk I/O, Network traffic, and Services.
- **🐳 Docker Stats**: CPU/Memory/Network per container (powered by cAdvisor).
- **🎮 Nvidia GPU Monitoring**: realtime usage, temperatures, and power draw (WSL2 supported).
- **📜 Centralized Logging**: Logs from your Python apps + Docker logs in one queryable UI.
- **🔔 Alerts**: Built-in `ntfy` server for push notifications.
- **🐍 Python SDK**: `dlogs` wrapper to start logging in 2 lines of code.

---

## 💿 Installation

### Option 1: Python (Recommended)

Install using pip (or pipx for isolation):

```bash
pip install motidivya-dlogs
```

Then initialize and start the stack:

```bash
# Create a folder for your stack
mkdir my-stack
cd my-stack

# Initialize configuration
dlogs init .

# Start the stack
dlogs up .
```

### Option 2: Docker

Run the CLI container directly:

```bash
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/app/work \
  divyesh1099/dlogs up /app/work
```

### Option 3: Installer Script (Windows)

```powershell
iwr -useb https://raw.githubusercontent.com/divyesh1099/dLogs/main/install_dlogs.ps1 | iex
```

---

## 🐍 Python Integration (`dLogs` SDK)

The `dlogs` package includes a zero-dependency wrapper to send logs directly to this stack.

**Usage:**

```python
from dlogs import dLogs

# Initialize (Automatically creates C:/Logs/my_app.json)
logger = dLogs("my_super_app")

# Log normal info (Shows in Loki/Grafana)
logger.log("Application started successfully.")

# Log errors (Highlights in Red)
try:
    1 / 0
except Exception as e:
    logger.alert(f"Critical math failure: {e}")
```

**How it works:**

- It writes structured JSON logs to `C:\Logs\app_name.json` (or configured directory).
- **Promtail** (running in Docker) watches that folder.
- It scrapes the new lines instantly and sends them to **Loki**.
- You view them in Grafana Explore (`{job="varlogs"} |= "my_super_app"`).

---

## 📊 Dashboards Guide

Grafana comes pre-provisioned. Go to [http://localhost:3000/dashboards](http://localhost:3000) (admin/admin) and open the **dLogs** folder.

### 1. 🪟 Windows Host

- **Real-time CPU/RAM**: Total system usage.
- **Network I/O**: Upload/Download speeds.
- **Disk Usage**: Space on C: drive.
- _Requirement: `windows_exporter` service running on port 9182._

### 2. 🐳 Docker Containers

- **CPU/Memory per Container**: identify resource hogs.
- **Network Traffic**: See which container is chatting the most.
- _Requirement: `cadvisor` container running._

### 3. 🟢 Nvidia GPU

- **Usage %**: Graphics load.
- **VRAM**: Memory allocation.
- **Temp/Power**: Thermal monitoring.
- _Requirement: `dlogs-gpu` container + Nvidia Drivers._

### 4. 🪵 Loki Logs

- **Search Engine**: Query logs using LogQL.
- **Filters**: Filter by app name, log level (INFO/ERROR).
- **Live Tail**: See logs as they happen.

---

## 🛠️ Architecture

The stack runs completely locally using Docker Compose:

| Component      | Port   | Purpose                                                                      |
| :------------- | :----- | :--------------------------------------------------------------------------- |
| **Grafana**    | `3000` | The Dashboard UI. Access via [http://localhost:3000](http://localhost:3000). |
| **Prometheus** | `9090` | Time-series database for metrics.                                            |
| **Loki**       | `3100` | Log aggregation system (like Splunk/ELK but lighter).                        |
| **Promtail**   | `—`    | Log collector. Watches log folder and sends to Loki.                         |
| **cAdvisor**   | `8090` | Container usage metrics (Google's official tool).                            |
| **GPU/Nvidia** | `9835` | `nvidia_gpu_exporter` for monitoring graphics cards.                         |
| **Windows**    | `9182` | `windows_exporter` MSI running natively on host.                             |
| **Ntfy**       | `8080` | Notification server (publish/subscribe).                                     |

---

_Moti❤️_
