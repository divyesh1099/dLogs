# Installation Guide

dLogs relies on **Docker** for the backend infrastructure and **PowerShell** for automation on Windows.

## Prerequisites

- **Operating System**: Windows 10/11 Pro or Enterprise (with Hyper-V/WSL2 support).
- **Docker Desktop**: Must be installed and running. [Download Here](https://www.docker.com/products/docker-desktop).
- **Python 3.8+**: Required for the CLI tool (optional if just using the script).
- **Administrator Privileges**: Required to install Windows Services and Open Firewall Ports.

---

## ⚡ Quick Start (Windows)

1.  **Download the Installer**:
    Download the latest `install_dlogs.ps1` from our [Releases Page](https://github.com/divyesh1099/dLogs/releases).

2.  **Run as Administrator**:
    Open PowerShell as Admin, navigate to the folder, and run:

    ```powershell
    .\install_dlogs.ps1
    ```

    ??? info "What does this script do?"
    _ Creates `C:\dLogs` (App) and `C:\Logs` (Data).
    _ Downloads `windows_exporter.msi`.
    _ Generates config files (`prometheus.yml`, `promtail.yml`) dynamically.
    _ Runs `docker-compose up -d`.

3.  **Verify Status**:
    Open your browser to [http://localhost:3000](http://localhost:3000).
    - **Username**: `admin`
    - **Password**: `admin` (You will be prompted to change this).

---

## 🛠️ Manual Installation (Linux/Mac)

While the automation script is Windows-focused, the stack is pure Docker.

1.  **Clone the Repo**:

    ```bash
    git clone https://github.com/divyesh1099/dLogs.git
    cd dLogs
    ```

2.  **Configure Environment**:
    Edit `docker-compose.yml`:
    - Update volume paths (change `C:/Logs` to `./logs`).
    - Remove `windows_exporter` / `nvidia_exporter` if not applicable.

3.  **Run**:
    ```bash
    docker-compose up -d
    ```
