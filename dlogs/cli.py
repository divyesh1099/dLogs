import os
import sys
import urllib.request
import json

# --- 1. THE CONFIGURATION WIZARD ---
def ask(question, default):
    """Asks the user a question with a default answer."""
    response = input(f"[?] {question} (Default: {default}): ").strip()
    return response if response else default

def download_file(url, path):
    print(f"Downloading {url} -> {path}...")
    try:
        with urllib.request.urlopen(url) as response:
            with open(path, 'wb') as f:
                f.write(response.read())
    except Exception as e:
        print(f"[!] Failed to download {url}: {e}")

    "enable_alerts": ask("Enable Mobile Alerts (ntfy)? (y/n)", "y").lower().startswith('y'),
}

if config["enable_alerts"]:
    import random
    default_topic = f"dlogs-{random.randint(1000,9999)}"
    config["ntfy_topic"] = ask("Enter your unique ntfy topic name", default_topic)

if config["enable_remote"]:
    config["cloudflare_token"] = ask("Enter Cloudflare Tunnel Token (Press Enter to skip/add later)", "")

# --- 2. PREPARE DIRECTORIES ---
dirs = [
    "config", 
    "provisioning/datasources", 
    "provisioning/dashboards", 
    "dashboards"
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- 3. GENERATE PROVISIONING CONFIGS ---

# Datasources
datasources_yml = """apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    uid: dlogs-prometheus
    access: proxy
    url: http://dlogs-prometheus:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    uid: dlogs-loki
    access: proxy
    url: http://dlogs-loki:3100
    editable: false
"""
with open("provisioning/datasources/dlogs.yml", "w") as f:
    f.write(datasources_yml)

# Dashboards Provider
dashboards_yml = """apiVersion: 1

providers:
  - name: 'dLogs'
    orgId: 1
    folder: 'dLogs'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 60
    allowUiUpdates: false
    options:
      path: /etc/grafana/dashboards
"""
with open("provisioning/dashboards/dlogs.yml", "w") as f:
    f.write(dashboards_yml)

# --- 4. DOWNLOAD DASHBOARDS ---
# We use the Grafana API to get the JSON for the dashboard revisions
dashboards_to_download = [
    {"id": 14694, "name": "windows_exporter.json"}, # Windows Host
    {"id": 10619, "name": "docker_containers.json"}, # Docker
    {"id": 13639, "name": "loki_logs.json"},       # Logs
]

if config["enable_gpu"]:
    dashboards_to_download.append({"id": 14574, "name": "nvidia_gpu.json"})

print("\n--- Downloading Dashboards ---")
for db in dashboards_to_download:
    url = f"https://grafana.com/api/dashboards/{db['id']}/revisions/latest/download"
    download_file(url, f"dashboards/{db['name']}")

# --- 4b. PATCH DASHBOARDS (Fix Datasource Variables) ---
print("--- Patching Dashboards ---")
for db in dashboards_to_download:
    path = f"dashboards/{db['name']}"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace template placeholders with actual datasource UIDs
        # defined in provisioning/datasources/dlogs.yml
        content = content.replace('${DS_PROMETHEUS}', 'dlogs-prometheus')
        content = content.replace('${DS_LOKI}', 'dlogs-loki')
        
        # Generic catch-all for JSON references
        content = content.replace('"datasource": "${DS_PROMETHEUS}"', '"datasource": {"type": "prometheus", "uid": "dlogs-prometheus"}')
        content = content.replace('"datasource": "${DS_LOKI}"', '"datasource": {"type": "loki", "uid": "dlogs-loki"}')
        
        # Fix: Sometimes inputs are used
        content = content.replace('"uid": "${DS_PROMETHEUS}"', '"uid": "dlogs-prometheus"')
        content = content.replace('"uid": "${DS_LOKI}"', '"uid": "dlogs-loki"')

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[✔] Patched {db['name']}")
    except Exception as e:
        print(f"[!] Failed to patch {db['name']}: {e}")

if __name__ == "__main__":
    main()



# --- 5. GENERATE TEMPLATES ---

# Base Docker Compose
docker_compose = f"""version: "3.8"

services:
  # --- DASHBOARD ---
  grafana:
    image: grafana/grafana:latest
    container_name: dlogs-grafana
    ports: ["{config['grafana_port']}:3000"]
    restart: unless-stopped
    volumes:
      - grafana-storage:/var/lib/grafana
      # Auto-Provisioning
      - ./provisioning:/etc/grafana/provisioning
      - ./dashboards:/etc/grafana/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on: [prometheus, loki]

  # --- METRICS DB ---
  prometheus:
    image: prom/prometheus:latest
    container_name: dlogs-prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time={config["retention_days"]}d'
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-storage:/prometheus
    extra_hosts:
      - "host.docker.internal:host-gateway"

  # --- LOGS DB ---
  loki:
    image: grafana/loki:latest
    container_name: dlogs-loki
    restart: unless-stopped
    command: -config.file=/etc/loki/local-config.yaml -table-manager.retention-period={config["retention_days"]}d
    ports: ["3100:3100"]

  # --- LOG COLLECTOR ---
  promtail:
    image: grafana/promtail:latest
    container_name: dlogs-promtail
    restart: unless-stopped
    volumes:
      - ./config/promtail.yml:/etc/promtail/config.yml
      - /var/log:/var/log
      # Host logs from Windows C:/Logs
      - C:/Logs:/var/log/host_logs
    command: -config.file=/etc/promtail/config.yml

  # --- CONTAINER METRICS (cAdvisor) ---
  cadvisor:
    image: google/cadvisor:latest
    container_name: dlogs-cadvisor
    restart: unless-stopped
    ports:
      - "8090:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    devices:
      - /dev/kmsg
"""

# Optional: GPU Support
if config["enable_gpu"]:
    docker_compose += """
  # --- GPU MONITORING (WSL2 FIX) ---
  nvidia-exporter:
    image: utkuozdemir/nvidia_gpu_exporter:1.4.1
    container_name: dlogs-gpu
    restart: unless-stopped
    ports: ["9835:9835"]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
"""

# Optional: Alerts
if config["enable_alerts"]:
    docker_compose += f"""
  # --- ALERTS (ntfy) ---
  ntfy:
    image: binwiederhier/ntfy
    container_name: dlogs-ntfy
    command: serve
    environment:
      - NTFY_BASE_URL=https://ntfy.sh
    ports: ["8080:80"]
"""

# Optional: Cloudflare Tunnel
if config["enable_remote"] and config["cloudflare_token"]:
    docker_compose += f"""
  # --- REMOTE ACCESS ---
  tunnel:
    image: cloudflare/cloudflared
    container_name: dlogs-tunnel
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN={config['cloudflare_token']}
"""

docker_compose += """
volumes:
  grafana-storage:
  prometheus-storage:
"""

# --- 6. WRITE CONFIG FILES ---

# Write docker-compose.yml
with open("docker-compose.yml", "w") as f:
    f.write(docker_compose)

# Write Prometheus Config (Dynamic Scrape Targets)
scrape_targets = ["'dlogs-prometheus:9090'", "'dlogs-cadvisor:8080'"]
if config["enable_gpu"]:
    scrape_targets.append("'dlogs-gpu:9835'")

prometheus_conf = f"""global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'dlogs-internal'
    static_configs:
      - targets: [{", ".join(scrape_targets)}]
  
  # Connect to Host Machine (Windows/Linux Native)
  - job_name: 'host-machine'
    static_configs:
      - targets: ['host.docker.internal:9182'] # Windows Exporter default
"""

try:
    with open("config/prometheus.yml", "w") as f:
        f.write(prometheus_conf)
except PermissionError:
    print("\n[!] Error: Could not write to config/prometheus.yml")
    print("    This is likely because Docker is running and using the file.")
    print("    Please run 'docker-compose down' and try again.")
    # sys.exit(1) # Don't exit, just warn, since other parts might have succeeded

# Write Promtail Config
promtail_conf = """server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://dlogs-loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: varlogs
          __path__: /var/log/host_logs/*.json
"""

with open("config/promtail.yml", "w") as f:
    f.write(promtail_conf)

print("\n\n[✔] Configuration & Provisioning complete!")
print("[✔] Datasources auto-configured (Prometheus, Loki).")
print("[✔] Dashboards downloaded and linked.")
print(f"\nTo start dLogs, run:\n  docker-compose up -d --force-recreate")
if config["enable_alerts"]:
    print(f"\nYour Alert Topic: https://ntfy.sh/{config['ntfy_topic']}")
