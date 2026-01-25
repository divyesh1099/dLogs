# dLogs: The "1-Click" Observability Stack

> **Monitor Everything.** Windows Host, Docker Containers, Nvidia GPUs, and App Logs. All in one place.

`dLogs` is a pre-configured, high-performance observability stack built on top of the industry-standard LGTM stack (**L**oki, **G**rafana, **T**elegraf/Promtail, **M**onitoring/Prometheus), enhanced with automatic dashboard provisioning and Python integration.

---

## 🚀 Features

- **⚡ Instant Setup**: One script installs everything. No manual config editing required.
- **🖥️ Full Windows Visibility**: CPU, RAM, Disk I/O, Network traffic, and Services.
- **🐳 Docker Stats**: CPU/Memory/Network per container (powered by cAdvisor).
- **🎮 Nvidia GPU Monitoring**: realtime usage, temperatures, and power draw (WSL2 supported).
- **📜 Centralized Logging**: Logs from your Python apps + Docker logs in one queryable UI.
- **🔔 Alerts**: Built-in `ntfy` server for push notifications.
- **🐍 Python SDK**: `dlogs.py` wrapper to start logging in 2 lines of code.

---

## 🛠️ Architecture

The stack runs completely locally using Docker Compose:

| Component      | Port   | Purpose                                                                      |
| :------------- | :----- | :--------------------------------------------------------------------------- |
| **Grafana**    | `3000` | The Dashboard UI. Access via [http://localhost:3000](http://localhost:3000). |
| **Prometheus** | `9090` | Time-series database for metrics.                                            |
| **Loki**       | `3100` | Log aggregation system (like Splunk/ELK but lighter).                        |
| **Promtail**   | `—`    | Log collector. Watches `C:\Logs` and sends to Loki.                          |
| **cAdvisor**   | `8090` | Container usage metrics (Google's official tool).                            |
| **GPU/Nvidia** | `9835` | `nvidia_gpu_exporter` for monitoring graphics cards.                         |
| **Windows**    | `9182` | `windows_exporter` MSI running natively on host.                             |
| **Ntfy**       | `8080` | Notification server (publish/subscribe).                                     |

---

## 💿 Installation

### ✅ Windows (Recommended)

We provide a PowerShell automation script that handles everything: directories, file downloads, and Docker startup.

**Prerequisites:**

1.  **Docker Desktop** (Running).
2.  **PowerShell** (Admin).

**Steps:**

1.  Open PowerShell as Administrator.
2.  Navigate to the `dLogs` folder.
3.  Run the installer:
    ```powershell
    .\install_dlogs.ps1
    ```
    _This script will:_
    - _Create `C:\dLogs` and `C:\Logs`._
    - _Download & Configure `windows_exporter`._
    - _Patch configuration files with correct ports._
    - _Boot the Docker stack._

**Fixing Missing Metrics:**
If you see "No Data" for Windows or Docker, run the helper fixes:

1.  **Windows Exporter**: Run `.\fix_windows_metrics.ps1` (Installs MSI + Firewall Rule).
2.  **Docker Metrics**: Run `.\install_dlogs.ps1` again (Updates configs for cAdvisor).

---

### 🐧 Linux / 🍏 macOS

The core stack is standard Docker Compose. The `install_dlogs.ps1` script is Windows-specific, but you can run the stack manually:

1.  **Ensure Docker is running.**
2.  **Edit `docker-compose.yml`**:
    - Change volume `C:/Logs:/var/log/host_logs` to a valid Linux path (e.g., `./logs:/var/log/host_logs`).
    - Remove `windows_exporter` references or replace with `node_exporter`.
3.  **Run:**
    ```bash
    python setup.py  # (Optional) Guidelines through configuration
    docker-compose up -d --build
    ```

---

## 🐍 Python Integration (`dLogs` SDK)

We provide `dlogs.py`, a zero-dependency wrapper to send logs directly to this stack.

**Usage:**

1.  Copy `dlogs.py` to your project.
2.  Import and use:

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

- It writes structured JSON logs to `C:\Logs\app_name.json`.
- **Promtail** (running in Docker) watches that folder.
- It scrapes the new lines instantly and sends them to **Loki**.
- You view them in Grafana Explore (`{job="varlogs"} |= "my_super_app"`).

---

## 📊 Dashboards Guide

Grafana comes pre-provisioned. Go to [http://localhost:3000/dashboards](http://localhost:3000) and open the **dLogs** folder.

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

## ❓ Troubleshooting

**Q: "Datasource not found" error?**

> Run `.\install_dlogs.ps1` again. It regenerates the correct UIDs (`dlogs-prometheus`, `dlogs-loki`) and provisions them.

**Q: "Windows Dashboard has N/A data"?**

> Run `.\fix_windows_metrics.ps1` as Administrator. Ensure Port 9182 is allowed in Firewall.

**Q: "Docker Dashboard is empty"?**

> Ensure `dlogs-cadvisor` is running (`docker ps`). If missing, pull the latest code and re-run installer.

**Q: "GPU Dashboard empty"?**

> Only works on machines with Nvidia GPUs. Ensure connection to `dlogs-gpu:9835` is working.

---

_Moti❤️_
