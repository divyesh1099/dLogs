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

## 2. Windows Dashboard showing "No Data" or "N/A"

**Symptoms**: Graphs are empty.
**Cause**: The `windows_exporter` service is not running or Firewall is blocking port 9182.
**Fix**:
Run the specific fix script as Administrator:

```powershell
.\fix_windows_metrics.ps1
```

This restarts the service and re-applies firewall rules.

## 3. Docker Dashboard Empty

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

## 4. "Mountpoint is not a directory" Error

**Symptoms**: Docker fails to start with an error about mounting `promtail.yml`.
**Cause**: Docker tried to mount a file that didn't exist yet, so it created a directory instead.
**Fix**:
The latest `install_dlogs.ps1` fixes this automatically. Just run it again. It will detect the bad directory, delete it, and copy the correct file.
