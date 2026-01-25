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

Add new scrap targets here. By default, it scrapes:

- Itself (`dlogs-prometheus:9090`)
- cAdvisor (`dlogs-cadvisor:8080`)
- GPU Exporter (`dlogs-gpu:9835`)
- Windows Host (`host.docker.internal:9182`)

### Promtail (`config/promtail.yml`)

Defines how logs are scraped. By default, it watches:

- `C:/Logs/*.json` (Windows)
- `/var/log/host_logs/*.json` (Mapped inside Docker)

## Environment Variables

You can customize the stack behavior using environment variables in `docker-compose.yml`.

- `GF_SECURITY_ADMIN_PASSWORD`: Set the initial Grafana admin password.
