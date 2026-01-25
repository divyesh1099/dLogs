# dLogs Installer - The Ultimate Stack
Write-Host "Installing dLogs... The fastest observability stack." -ForegroundColor Cyan

# Determine script location to copy files from
$ScriptPath = $PSScriptRoot

# 1. Create Directories
Write-Host "Creating directories..."
New-Item -ItemType Directory -Force -Path "C:\dLogs\data" | Out-Null
New-Item -ItemType Directory -Force -Path "C:\dLogs\config" | Out-Null
New-Item -ItemType Directory -Force -Path "C:\dLogs\provisioning\dashboards" | Out-Null
New-Item -ItemType Directory -Force -Path "C:\dLogs\provisioning\datasources" | Out-Null
New-Item -ItemType Directory -Force -Path "C:\dLogs\dashboards" | Out-Null
New-Item -ItemType Directory -Force -Path "C:\Logs" | Out-Null

# 2. Download Lightweight Native Collectors (The "Fastest" part)
Write-Host "Downloading collectors..."
# Windows Exporter (OS Stats)
Invoke-WebRequest -Uri "https://github.com/prometheus-community/windows_exporter/releases/download/v0.22.0/windows_exporter-0.22.0-amd64.msi" -OutFile "C:\dLogs\windows_exporter.msi"
# OpenHardwareMonitor (Temps)
Invoke-WebRequest -Uri "https://openhardwaremonitor.org/files/openhardwaremonitor-v0.9.6.zip" -OutFile "C:\dLogs\ohm.zip"

# 3. Install Collectors silently
Write-Host "Installing Native Collectors..."
Start-Process msiexec.exe -ArgumentList "/i C:\dLogs\windows_exporter.msi ENABLED_COLLECTORS=cpu,cs,logical_disk,net,os,service,system,textfile /qn" -Wait

# 4. Create Configuration Files (Auto-generated)
Write-Host "Generating configs..."
$prometheusConfig = @"
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'dlogs-agent'
    static_configs:
      - targets: ['host.docker.internal:9182'] # Windows Exporter
  - job_name: 'gpu-stats'
    static_configs:
      - targets: ['dlogs-gpu:9835'] # Internal Docker Network
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['dlogs-cadvisor:8080'] # cAdvisor
"@
Set-Content -Path "C:\dLogs\config\prometheus.yml" -Value $prometheusConfig

# Copy docker-compose and promtail config from the repo source
if (Test-Path "$ScriptPath\docker-compose.yml") {
    Copy-Item -Path "$ScriptPath\docker-compose.yml" -Destination "C:\dLogs\docker-compose.yml" -Force
}
else {
    Write-Warning "docker-compose.yml not found in script directory!"
}

if (Test-Path "$ScriptPath\config\promtail.yml") {
    # Fix: Docker creates a directory if file is missing. Remove it if it causes conflicts.
    if ((Test-Path "C:\dLogs\config\promtail.yml") -and (Get-Item "C:\dLogs\config\promtail.yml" | Where-Object { $_.PSIsContainer })) {
        Write-Warning "Removing directory mismatch at C:\dLogs\config\promtail.yml"
        Remove-Item "C:\dLogs\config\promtail.yml" -Recurse -Force
    }
    Copy-Item -Path "$ScriptPath\config\promtail.yml" -Destination "C:\dLogs\config\promtail.yml" -Force
}
else {
    Write-Warning "promtail.yml not found in script directory!"
}

# Copy Grafana provisioning + dashboards (so dashboards/datasources auto-load on boot)
if (Test-Path "$ScriptPath\provisioning") {
    Copy-Item -Path "$ScriptPath\provisioning\*" -Destination "C:\dLogs\provisioning" -Recurse -Force
}
else {
    Write-Warning "provisioning folder not found in script directory!"
}

if (Test-Path "$ScriptPath\dashboards") {
    Copy-Item -Path "$ScriptPath\dashboards\*" -Destination "C:\dLogs\dashboards" -Recurse -Force
}
else {
    Write-Warning "dashboards folder not found in script directory!"
}

# 5. Launch The Core (Docker)
Write-Host "Launching dLogs Core..."


# Check if Docker is running
Write-Host "Checking Docker status..."
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running or not accessible."
    }
}
catch {
    Write-Error "ERROR: Docker Desktop is not running!"
    Write-Warning "Please start Docker Desktop and run this script again."
    Write-Warning "Output: $_"
    exit 1
}

docker-compose -f "C:\dLogs\docker-compose.yml" up -d

Write-Host "dLogs is Live! Dashboard: http://localhost:3000" -ForegroundColor Green
