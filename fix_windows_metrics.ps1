# fix_windows_metrics.ps1
# Installs Windows Exporter and opens Firewall ports

# --- Self-Elevation to Admin ---
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "This script requires Administrator privileges to install services and firewall rules."
    Write-Host "Attempting to restart with Admin rights..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}
# -------------------------------

Write-Host "Fixing Windows Metrics..." -ForegroundColor Cyan

# 1. Download Windows Exporter
$url = "https://github.com/prometheus-community/windows_exporter/releases/download/v0.22.0/windows_exporter-0.22.0-amd64.msi"
$output = "C:\dLogs\windows_exporter.msi"

if (-not (Test-Path "C:\dLogs")) {
    New-Item -ItemType Directory -Force -Path "C:\dLogs" | Out-Null
}

Write-Host "Downloading Windows Exporter..."
try {
    Invoke-WebRequest -Uri $url -OutFile $output
}
catch {
    Write-Error "Failed to download exporter: $_"
    exit 1
}

# 2. Install (if not already running)
Write-Host "Installing/Repairing Windows Exporter..."
# Stop if running to ensure clean install/update
Stop-Service windows_exporter -ErrorAction SilentlyContinue

# Install with default collectors + textfile for custom metrics
$args = "/i $output ENABLED_COLLECTORS=cpu,cs,logical_disk,net,os,service,system,textfile LISTEN_PORT=9182 /qn"
Start-Process msiexec.exe -ArgumentList $args -Wait

# 3. Firewall Rule
Write-Host "Configuring Firewall..."
# Remove existing rule to be safe
Remove-NetFirewallRule -DisplayName "dLogs Windows Exporter" -ErrorAction SilentlyContinue

# Add new rule allowing Docker subnet (usually 172.x.x.x) or all local traffic
# Allowing all local subnet traffic for simplicity in dev setups
New-NetFirewallRule -DisplayName "dLogs Windows Exporter" -Direction Inbound -LocalPort 9182 -Protocol TCP -Action Allow -Profile Any | Out-Null

# 4. Verify
Write-Host "Verifying Service..."
Start-Sleep -Seconds 5
if (Get-Service windows_exporter -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Running' }) {
    Write-Host " [OK] Windows Exporter is RUNNING." -ForegroundColor Green
}
else {
    Write-Warning " [!] Windows Exporter service is NOT running. Please check Event Viewer."
    Start-Service windows_exporter
}

# Check Port
$portCheck = Get-NetTCPConnection -LocalPort 9182 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host " [OK] Port 9182 is LISTENING." -ForegroundColor Green
}
else {
    Write-Error " [!] Port 9182 is CLOSED. Metrics will fail."
}

Write-Host "`nDone. Windows Dashboard should show data within 30 seconds."
