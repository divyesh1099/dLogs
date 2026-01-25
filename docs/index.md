# dLogs: The Ultimate Observability Stack

[![Release](https://img.shields.io/github/v/release/divyesh1099/dLogs)](https://github.com/divyesh1099/dLogs/releases)
[![License](https://img.shields.io/github/license/divyesh1099/dLogs)](LICENSE)

**dLogs** is a pre-configured, production-ready observability stack designed for speed and simplicity. It allows you to monitor your **Windows Host**, **Docker Containers**, **Nvidia GPUs**, and **Python Applications** with zero configuration.

---

## 🚀 Why dLogs?

Most observability stacks (Prometheus/Grafana) take hours to configure properly—setting up scrape targets, finding dashboards, configuring port forwarding, and writing Docker Compose files.

**dLogs does this in 1 click.**

### Key Features

- **⚡ 1-Click Install**: A single PowerShell script handles everything.
- **🖥️ Full Windows Monitoring**: Native MSI integration for CPU, RAM, Disk, and Network stats.
- **🐳 Docker Visibility**: Auto-discovery of containers via cAdvisor.
- **🎮 GPU Profiling**: Instant Nvidia GPU metrics (Temp, Power, VRAM) via explicit internal networking.
- **📜 Application Logging**: A simple Python SDK (`dlogs`) to send JSON logs to Loki.
- **🔔 Push Notifications**: Built-in `ntfy` server for alerting.

---

## 📸 Screenshots

![Grafana Dashboard](https://grafana.com/static/assets/img/blog/loki_v2.0_release_blog_post_image_1.png)
_(Note: Actual screenshots of your stack would go here)_

## 📚 Quick Links

- [**Installation Guide**](getting-started/installation.md): Get up and running in 2 minutes.
- [**Python SDK**](features/sdk.md): Learn how to log from your code.
- [**Dashboards**](features/dashboards.md): Explore the pre-built visualizations.
- [**GitHub Repo**](https://github.com/divyesh1099/dLogs): Source code and issues.
