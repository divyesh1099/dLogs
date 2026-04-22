# Configuration

dLogs uses standard configuration files for its components. When you run `dlogs init`, these files are copied to your project directory.

## File Structure

```
my-stack/
├── docker-compose.yml       # Service definitions
├── config/
│   ├── prometheus.yml       # Metrics collection config
│   └── promtail.yml         # Log collection config
├── dashboards/              # Grafana dashboard JSONs
└── provisioning/            # Grafana provisioning setups
```

## Configuring Services

### Prometheus (`config/prometheus.yml`)

Prometheus uses the checked-in jobs plus generated file-based targets under `.dlogs-state/prometheus/`. By default, it scrapes:

- Itself (`dlogs-prometheus:9090`)
- cAdvisor (`dlogs-cadvisor:8080`)
- Host Metrics (`host.docker.internal:9100`, `host.docker.internal:9182`, or `dlogs-node-exporter:9100`, depending on OS/runtime)
- GPU Metrics (`host.docker.internal:9835` or `dlogs-gpu:9835`, when Nvidia support is available)

### Promtail (`config/promtail.yml`)

Defines how logs are scraped. By default, it watches:

- `DLOGS_LOG_DIR/*.json` on the host
- `/var/log/host_logs/*.json` (Mapped inside Docker)

## Environment Variables

You can customize the stack behavior using environment variables in `docker-compose.yml`.

- `GF_SECURITY_ADMIN_PASSWORD`: Set the initial Grafana admin password.
- `DLOGS_LOG_DIR`: Host log directory. `dlogs init` auto-detects `C:/Logs` on Windows and `~/dlogs` on Linux/macOS.
- `DLOGS_ENABLE_GPU`: Set to `1` to force-enable the Nvidia exporter or `0` to force-disable it. By default, `dlogs up` auto-detects Nvidia support.
