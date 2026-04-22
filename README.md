# dLogs: The "1-Click" Observability Stack

[![PyPI version](https://badge.fury.io/py/motidivya-dlogs.svg)](https://badge.fury.io/py/motidivya-dlogs)
[![Docker Image](https://img.shields.io/docker/v/divyesh1099/dlogs?label=docker&logo=docker)](https://hub.docker.com/r/divyesh1099/dlogs)

> **Monitor Everything.** Host systems, Docker containers, Nvidia GPUs, and app logs. All in one place.

`dLogs` is a pre-configured, high-performance observability stack built on top of the industry-standard LGTM stack (**L**oki, **G**rafana, **T**elegraf/Promtail, **M**onitoring/Prometheus), enhanced with automatic dashboard provisioning and Python integration.

---

## 🚀 Features

- **⚡ Instant Setup**: Install via pip or Docker.
- **🖥️ OS-Aware Host Visibility**: CPU, RAM, disk, and network metrics across Windows, Linux, and fallback environments.
- **🐳 Docker Stats**: CPU/Memory/Network per container (powered by cAdvisor).
- **🎮 Nvidia GPU Monitoring**: realtime usage, temperatures, and power draw via host-side `nvidia-smi` or Docker's Nvidia runtime.
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

`dlogs init` auto-detects the host OS and writes `.env` with `DLOGS_LOG_DIR` for Docker Compose:

- Windows: `C:/Logs`
- Linux/macOS: `~/dlogs`

If you want a custom path, set `DLOGS_LOG_DIR` yourself before running `dlogs up .`.

GPU monitoring is auto-enabled only when an Nvidia runtime is detected. You can force it on or off with `DLOGS_ENABLE_GPU=1` or `DLOGS_ENABLE_GPU=0`.

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

# Initialize (Auto-detects the right log dir for your OS)
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

- It writes structured JSON logs to `C:/Logs/app_name.json` on Windows or `~/dlogs/app_name.json` on Linux/macOS.
- You can override the location with `DLOGS_LOG_DIR`.
- **Promtail** (running in Docker) watches that folder.
- It scrapes the new lines instantly and sends them to **Loki**.
- You view them in Grafana Explore (`{job="varlogs"} |= "my_super_app"`).

---

## 📊 Dashboards Guide

Grafana comes pre-provisioned. Go to [http://localhost:3000/dashboards](http://localhost:3000) (admin/admin) and open the **dLogs** folder.

### 1. 🖥️ Host System Metrics

- **Real-time CPU/RAM**: Total system usage.
- **Network I/O**: Upload/Download speeds.
- **Disk Usage**: Filesystem usage for the active host.
- _Requirements: Windows uses `windows_exporter` on port 9182, Linux uses the built-in dLogs host exporter on port 9100, and other OSes fall back to the bundled `node-exporter` container._

### 2. 🐳 Docker Containers

- **CPU/Memory per Container**: identify resource hogs.
- **Network Traffic**: See which container is chatting the most.
- _Requirement: `cadvisor` container running._

### 3. 🟢 Nvidia GPU

- **Usage %**: Graphics load.
- **VRAM**: Memory allocation.
- **Temp/Power**: Thermal monitoring.
- _Requirement: Nvidia drivers plus either host-side `nvidia-smi` or a Docker Nvidia runtime._

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
| **GPU Metrics** | `9835` | Host-side Nvidia exporter or Docker `nvidia_gpu_exporter`, depending on runtime support. |
| **Host Metrics** | `9100` / `9182` | Native Linux exporter on `9100`, `windows_exporter` on `9182`, or `node-exporter` fallback. |
| **Ntfy**       | `8080` | Notification server (publish/subscribe).                                     |

Prometheus target files under `.dlogs-state/prometheus/` are generated by `dlogs up` to match the active OS/runtime.

---

_Moti❤️_
