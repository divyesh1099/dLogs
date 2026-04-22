# Troubleshooting

Common issues and their fixes.

## 1. "Datasource not found" Error

**Symptoms**: Dashboards load but show red error boxes saying "Datasource dlogs-prometheus not found".
**Cause**: Grafana's internal database UID for the datasource doesn't match the dashboard's expectation.
**Fix**:
Run the installer again. It forces a re-provision.

```powershell
.\install_dlogs.ps1
```

## 2. Host System Metrics Dashboard showing "No Data" or "N/A"

**Symptoms**: Graphs are empty.
**Cause**: The OS-specific host exporter is unavailable, or Grafana is pointed at a stale/non-live target.
**Fix**:
Check which host exporter dLogs selected:

```bash
dlogs status .
```

- On Linux, make sure the status output shows `Host exporter: up on localhost:9100`.
- On Windows, make sure `windows_exporter` is running and reachable on `host.docker.internal:9182`.
- On fallback setups, make sure the `dlogs-node-exporter` container is up.
- If you changed OS/runtime settings, restart the stack so Prometheus regenerates its target files.

## 3. Nvidia GPU Metrics Dashboard showing "No Data"

**Symptoms**: GPU panels are empty even though Grafana and Prometheus are up.
**Cause**: dLogs could not start a host-side `nvidia-smi` exporter, or the Docker daemon does not expose an Nvidia runtime.
**Fix**:
Check the runtime state first:

```bash
dlogs status .
```

- If the output shows `GPU exporter: up on localhost:9835`, Prometheus should scrape GPU metrics from the host.
- If GPU monitoring is not active, verify that `nvidia-smi` works on the host or that your Docker daemon has Nvidia runtime support.
- After fixing GPU access, run `dlogs down .` and `dlogs up .` so the generated Prometheus targets are refreshed.

## 4. Docker Dashboard Empty

**Symptoms**: "No Data" in Docker stats panels.
**Cause**: The `cadvisor` container is missing or crashed.
**Fix**:
Check container status:

```powershell
docker ps
```

If `dlogs-cadvisor` is missing, ensure you are running the latest version of the stack:

```powershell
git pull
.\install_dlogs.ps1
```

## 5. "Mountpoint is not a directory" Error

**Symptoms**: Docker fails to start with an error about mounting `promtail.yml`.
**Cause**: Docker tried to mount a file that didn't exist yet, so it created a directory instead.
**Fix**:
The latest `install_dlogs.ps1` fixes this automatically. Just run it again. It will detect the bad directory, delete it, and copy the correct file.
