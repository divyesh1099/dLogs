#!/usr/bin/env bash
set -e

echo "Installing dlogs..."

if command -v pipx >/dev/null 2>&1; then
  pipx install dlogs --force
  echo "Done. Run: dlogs --help"
  exit 0
fi

if command -v python3 >/dev/null 2>&1; then
  python3 -m pip install --upgrade pip
  python3 -m pip install --upgrade dlogs
  echo "Done. Run: dlogs --help"
  exit 0
fi

echo "Python3 not found. Install Python3.9+ or download binary from GitHub Releases."
exit 1
