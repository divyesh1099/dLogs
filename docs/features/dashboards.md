# pre-Built Dashboards

dLogs comes with 4 production-grade dashboards out of the box.

## 1. Host System Metrics

**UID**: `IV0hu1m7z`

This dashboard monitors whichever host metrics source is active for the current OS.

- **Linux**: Uses the built-in dLogs host exporter on port `9100`.
- **Windows**: Uses `windows_exporter` on port `9182`.
- **Other/Fallback**: Uses the bundled `node-exporter` container when a native host exporter is not available.
- **Key Metrics**: CPU usage, memory pressure, filesystem usage, uptime, and network throughput.
- **Variables**: The host dropdown is populated from live Prometheus series so it only shows exporters that currently have data.

## 2. Docker Containers

**UID**: `4dMaCsRZz`

Powered by `cAdvisor`.

- **Granularity**: Per-container CPU, Memory, and Network usage.
- **Health**: See container uptime and restart counts.
- **Visuals**: Stacked graphs to see which container is hogging resources.

## 3. Nvidia GPU Metrics

**UID**: `vlvPlrgnk`

Essential for AI/ML workloads.

- **Metrics**: GPU utilization, memory (VRAM) used, temperature, clocks, fan speed, and power draw.
- **Sources**: Works with the native host-side `nvidia-smi` exporter or the Docker `nvidia_gpu_exporter` profile.
- **Fan Speed**: Monitor cooling performance.

## 4. dLogs App Logs (Loki)

**UID**: `loki_logs`

A dedicated Log Explorer interface.

- **Queries**: Pre-filtered to show logs from `dlogs.py` applications.
- **Color Coding**: INFO is Blue, WARN is Yellow, ERROR is Red.
- **Search**: Full-text search across all logs.
