# pre-Built Dashboards

dLogs comes with 4 production-grade dashboards out of the box.

## 1. Windows Host Overview

**UID**: `IV0hu1m7z`

This dashboard monitors the physical machine hosting the stack.

- **Key Metrics**: CPU Usage (User/System), RAM Available, Disk I/O Latency, Network Bandwidth.
- **Variables**: Select different Hosts via the dropdown.

## 2. Docker Containers

**UID**: `4dMaCsRZz`

Powered by `cAdvisor`.

- **Granularity**: Per-container CPU, Memory, and Network usage.
- **Health**: See container uptime and restart counts.
- **Visuals**: Stacked graphs to see which container is hogging resources.

## 3. Nvidia GPU Metrics

**UID**: `vlvPlrgnk`

Essential for AI/ML workloads.

- **Metrics**: GPU Utilization %, Memory (VRAM) Used, Temperature (C), Power Draw (Watts).
- **Fan Speed**: Monitor cooling performance.

## 4. dLogs App Logs (Loki)

**UID**: `loki_logs`

A dedicated Log Explorer interface.

- **Queries**: Pre-filtered to show logs from `dlogs.py` applications.
- **Color Coding**: INFO is Blue, WARN is Yellow, ERROR is Red.
- **Search**: Full-text search across all logs.
