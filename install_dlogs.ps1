$ErrorActionPreference = "Stop"

Write-Host "Installing dlogs..." -ForegroundColor Cyan

# Prefer pipx (best for CLI tools)
$hasPipx = Get-Command pipx -ErrorAction SilentlyContinue
if ($hasPipx) {
  pipx install dlogs --force
  Write-Host "Done. Run: dlogs --help" -ForegroundColor Green
  exit 0
}

# fallback to pip
$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) {
  $py = Get-Command python -ErrorAction SilentlyContinue
}

if (-not $py) {
  Write-Host "Python not found. Install Python 3.9+ or use the binary from GitHub Releases." -ForegroundColor Yellow
  exit 1
}

& $py.Source -m pip install --upgrade pip
& $py.Source -m pip install --upgrade dlogs

Write-Host "Done. Run: dlogs --help" -ForegroundColor Green
