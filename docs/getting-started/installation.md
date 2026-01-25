# Installation

dLogs is designed to be installed as a Python package or run via Docker.

## Methods

### 1. Python (Recommended)

Requires Python 3.9+.

```bash
pip install motidivya-dlogs
```

**Usage:**

The CLI provides commands to manage the stack.

```bash
# 1. Create a directory for your stack configuration
mkdir my-monitoring
cd my-monitoring

# 2. Initialize the configuration files
dlogs init .

# 3. Start the services
dlogs up .

# 4. Check status
dlogs status .

# 5. Stop services
dlogs down .
```

### 2. Docker

If you don't want to install Python, you can use the official Docker image.

```bash
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/app/work \
  divyesh1099/dlogs up /app/work
```

### 3. Windows PowerShell Script

For a purely native experience on Windows (downloads `windows_exporter` MSI automatically):

```powershell
iwr -useb https://raw.githubusercontent.com/divyesh1099/dLogs/main/install_dlogs.ps1 | iex
```

## Post-Installation

Once the stack is running, you can access the services:

- **Grafana**: [http://localhost:3000](http://localhost:3000) (User: `admin`, Password: `admin`)
- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **Loki**: [http://localhost:3100](http://localhost:3100)
- **Ntfy**: [http://localhost:8080](http://localhost:8080)
