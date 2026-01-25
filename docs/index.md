# dLogs Documentation

**The "1-Click" Observability Stack for Windows, Docker, and Python.**

`dLogs` handles the complexity of setting up a monitoring stack (Grafana, Prometheus, Loki) so you can focus on building your app.

[![PyPI version](https://badge.fury.io/py/motidivya-dlogs.svg)](https://badge.fury.io/py/motidivya-dlogs)
[![Docker Image](https://img.shields.io/docker/v/divyesh1099/dlogs?label=docker&logo=docker)](https://hub.docker.com/r/divyesh1099/dlogs)

---

## What is dLogs?

It is a Python package and a set of Docker containers that gives you:

1.  **Observability**: Pre-configured dashboards for Host, Docker, and GPU.
2.  **Logging**: A Python SDK to send logs to the stack effortlessly.
3.  **Alerting**: Built-in notification server.

## Quick Start

### Install

```bash
pip install motidivya-dlogs
```

### Initialize & Run

```bash
mkdir my-stack
cd my-stack
dlogs init .
dlogs up .
```

Visit [http://localhost:3000](http://localhost:3000) (admin/admin).

---

## Next Steps

- [Installation Guide](getting-started/installation.md)
- [Python SDK Usage](features/sdk.md)
- [Dashboards Overview](features/dashboards.md)
