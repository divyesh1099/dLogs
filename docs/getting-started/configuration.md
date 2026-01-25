# Configuration

## Directory Structure

dLogs uses a strict directory structure to ensure persistence and ease of access.

| Path              | Purpose                                                      |
| :---------------- | :----------------------------------------------------------- |
| `C:\dLogs`        | Application Root. Contains configs and Docker files.         |
| `C:\Logs`         | **Log Ingestion Folder**. Drop `.json` or `.log` files here. |
| `C:\dLogs\config` | Contains `prometheus.yml` and `promtail.yml`.                |
| `C:\dLogs\data`   | Persistent storage for Grafana/Prometheus databases.         |

---

## 🔥 Firewall Settings

The installer attempts to open necessary ports, but if you have a strict firewall, allow the following:

- **TCP 3000**: Grafana UI (Web Access).
- **TCP 9090**: Prometheus (Metrics DB).
- **TCP 3100**: Loki (Logs DB).
- **TCP 9182**: Windows Exporter (Host Metrics).
- **TCP 9835**: Nvidia GPU Exporter.

## ⚙️ Customizing Prometheus

To add new scrape targets (e.g., another server or a new microservice), edit:
`C:\dLogs\config\prometheus.yml`

```yaml
scrape_configs:
  - job_name: "my-new-app"
    static_configs:
      - targets: ["192.168.1.50:8080"]
```

Then restart the stack:

```powershell
docker container restart dlogs-prometheus
```
