from __future__ import annotations

import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from importlib import resources
from pathlib import Path

from rich import print


GPU_EXPORTER_PORT = 9835
HOST_EXPORTER_PORT = 9100
PROMETHEUS_TARGET_FILES = {
    "gpu": "gpu.json",
    "host-machine": "host-machine.json",
    "node-exporter": "node-exporter.json",
}
TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


def _run(cmd: list[str], env: dict[str, str] | None = None) -> int:
    env_vars = os.environ.copy()
    env_prefix = ""
    if env:
        env_vars.update(env)
        env_prefix = " ".join(f"{key}={value}" for key, value in env.items()) + " "

    print(f"[bold cyan]$ {env_prefix}{' '.join(cmd)}[/bold cyan]")
    return subprocess.call(cmd, env=env_vars)


def _assets_dir() -> Path:
    return Path(resources.files("dlogs")) / "assets"


def _docker_ping(env: dict[str, str] | None = None) -> bool:
    probe_env = os.environ.copy()
    if env:
        probe_env.update(env)

    result = subprocess.run(
        ["docker", "info", "--format", "{{json .ServerVersion}}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=probe_env,
    )
    return result.returncode == 0


def _docker_supports_gpu(env: dict[str, str] | None = None) -> bool:
    probe_env = os.environ.copy()
    if env:
        probe_env.update(env)

    result = subprocess.run(
        ["docker", "info", "--format", "{{json .Runtimes}}"],
        capture_output=True,
        text=True,
        env=probe_env,
    )
    return result.returncode == 0 and '"nvidia"' in result.stdout


def _http_text(url: str, timeout: float = 1.0) -> str | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                return None
            return response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def _http_contains(url: str, marker: str, timeout: float = 1.0) -> bool:
    body = _http_text(url, timeout=timeout)
    return body is not None and marker in body


def _wait_for_metric(url: str, marker: str, timeout_seconds: float = 5.0) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if _http_contains(url, marker, timeout=1.0):
            return True
        time.sleep(0.25)
    return False


def _docker_env() -> dict[str, str] | None:
    if os.getenv("DOCKER_HOST"):
        return None

    if _docker_ping():
        return None

    if platform.system() != "Linux":
        return None

    desktop_socket = Path.home() / ".docker" / "desktop" / "docker.sock"
    desktop_env = {"DOCKER_HOST": f"unix://{desktop_socket}"}

    if not desktop_socket.exists() and shutil.which("systemctl"):
        subprocess.run(
            ["systemctl", "--user", "start", "docker-desktop.service"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    if desktop_socket.exists() and _docker_ping(desktop_env):
        print(f"[cyan]Using Docker Desktop user socket:[/cyan] {desktop_socket}")
        return desktop_env

    return None


def _read_env_value(env_path: Path, key: str) -> str | None:
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", 1)
        if name.strip() == key:
            return value.strip().strip('"').strip("'")

    return None


def _default_log_dir() -> str | None:
    system = platform.system()
    if system == "Windows":
        return "C:/Logs"
    if system in {"Linux", "Darwin"}:
        return str(Path.home() / "dlogs")
    return None


def _resolve_log_dir(workdir: Path) -> tuple[str | None, str]:
    env_override = os.getenv("DLOGS_LOG_DIR")
    if env_override:
        return env_override, "environment"

    env_file_value = _read_env_value(workdir / ".env", "DLOGS_LOG_DIR")
    if env_file_value:
        return env_file_value, str(workdir / ".env")

    default_log_dir = _default_log_dir()
    if default_log_dir:
        return default_log_dir, f"auto-detected {platform.system()}"

    return None, platform.system() or "unknown OS"


def _write_env_value(env_path: Path, key: str, value: str) -> None:
    lines: list[str] = []
    found = False
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    new_lines: list[str] = []
    for line in lines:
        if line.split("=", 1)[0].strip() == key and "=" in line:
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)

    if not found:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.extend(
            [
                "# Auto-generated by dlogs. Override this if you want a custom host log directory.",
                f"{key}={value}",
            ]
        )

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _should_migrate_log_dir(existing_value: str, default_log_dir: str) -> bool:
    return existing_value == "/tmp/dlogs" and existing_value != default_log_dir


def _state_dir(workdir: Path) -> Path:
    return workdir / ".dlogs-state"


def _prometheus_generated_dir(workdir: Path) -> Path:
    return _state_dir(workdir) / "prometheus"


def _exporter_state_path(workdir: Path, name: str) -> Path:
    return _state_dir(workdir) / f"{name}.json"


def _ensure_state_dirs(workdir: Path) -> None:
    _prometheus_generated_dir(workdir).mkdir(parents=True, exist_ok=True)


def _load_state_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None
    return data


def _write_state_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _process_running(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False

    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _tail_file(path: Path, line_count: int = 20) -> str:
    if not path.exists():
        return ""
    return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-line_count:])


def _stop_exporter(workdir: Path, name: str) -> None:
    state_path = _exporter_state_path(workdir, name)
    state = _load_state_json(state_path)
    if not state:
        return

    pid = state.get("pid")
    if isinstance(pid, int) and _process_running(pid):
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass

            deadline = time.time() + 5
            while time.time() < deadline and _process_running(pid):
                time.sleep(0.2)

            if _process_running(pid):
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass

    state_path.unlink(missing_ok=True)


def _ensure_exporter_running(
    workdir: Path,
    name: str,
    module: str,
    port: int,
    marker: str,
) -> bool:
    url = f"http://127.0.0.1:{port}/metrics"
    if _http_contains(url, marker):
        return True

    state_path = _exporter_state_path(workdir, name)
    state = _load_state_json(state_path)
    if state:
        pid = state.get("pid")
        if isinstance(pid, int) and _process_running(pid) and _wait_for_metric(url, marker):
            return True

    _stop_exporter(workdir, name)

    log_path = _state_dir(workdir) / f"{name}.log"
    command = [sys.executable, "-m", module, "--host", "0.0.0.0", "--port", str(port)]
    stdout_handle = log_path.open("a", encoding="utf-8")
    try:
        popen_kwargs: dict[str, object] = {
            "stdout": stdout_handle,
            "stderr": subprocess.STDOUT,
            "stdin": subprocess.DEVNULL,
        }
        if os.name == "nt":
            creationflags = 0
            creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            creationflags |= getattr(subprocess, "DETACHED_PROCESS", 0)
            creationflags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
            popen_kwargs["creationflags"] = creationflags
        else:
            popen_kwargs["start_new_session"] = True

        process = subprocess.Popen(command, **popen_kwargs)
    finally:
        stdout_handle.close()

    _write_state_json(
        state_path,
        {
            "pid": process.pid,
            "module": module,
            "port": port,
            "log": str(log_path),
        },
    )

    if _wait_for_metric(url, marker):
        return True

    print(
        f"[yellow]Warning:[/yellow] {name} did not become healthy on port {port}.\n"
        f"{_tail_file(log_path)}"
    )
    return False


def _bool_env(name: str) -> bool | None:
    raw_value = os.getenv(name)
    if raw_value is None:
        return None

    normalized = raw_value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return None


def _host_gpu_available() -> bool:
    return bool(shutil.which("nvidia-smi") or Path("/dev/nvidiactl").exists())


def _write_target_file(path: Path, targets: list[str], labels: dict[str, str] | None = None) -> None:
    groups: list[dict[str, object]] = []
    if targets:
        group: dict[str, object] = {"targets": targets}
        if labels:
            group["labels"] = labels
        groups.append(group)
    path.write_text(json.dumps(groups, indent=2) + "\n", encoding="utf-8")


def _write_prometheus_targets(
    workdir: Path,
    node_targets: list[str],
    host_targets: list[str],
    gpu_targets: list[str],
) -> None:
    generated_dir = _prometheus_generated_dir(workdir)
    _write_target_file(
        generated_dir / PROMETHEUS_TARGET_FILES["node-exporter"],
        node_targets,
        {"source": "host" if any("host.docker.internal" in target for target in node_targets) else "docker"},
    )
    _write_target_file(
        generated_dir / PROMETHEUS_TARGET_FILES["host-machine"],
        host_targets,
        {"source": "host"},
    )
    _write_target_file(
        generated_dir / PROMETHEUS_TARGET_FILES["gpu"],
        gpu_targets,
        {"source": "host" if any("host.docker.internal" in target for target in gpu_targets) else "docker"},
    )


def _clear_prometheus_targets(workdir: Path) -> None:
    _ensure_state_dirs(workdir)
    _write_prometheus_targets(workdir, [], [], [])


def _prepare_runtime(workdir: Path) -> dict[str, str] | None:
    _ensure_state_dirs(workdir)

    docker_env = _docker_env() or {}
    compose_env = dict(docker_env)
    node_targets: list[str] = []
    host_targets: list[str] = []
    gpu_targets: list[str] = []

    system = platform.system()
    if system == "Linux":
        if _ensure_exporter_running(
            workdir,
            "host-exporter",
            "dlogs.host_exporter",
            HOST_EXPORTER_PORT,
            "node_cpu_seconds_total",
        ):
            node_targets = [f"host.docker.internal:{HOST_EXPORTER_PORT}"]
            print("[cyan]Host metrics:[/cyan] using native Linux exporter on port 9100")
        else:
            node_targets = ["dlogs-node-exporter:9100"]
            print("[yellow]Host metrics:[/yellow] falling back to container node-exporter")
    elif system == "Windows":
        _stop_exporter(workdir, "host-exporter")
        host_targets = ["host.docker.internal:9182"]
        print("[cyan]Host metrics:[/cyan] using Windows exporter on port 9182")
    else:
        _stop_exporter(workdir, "host-exporter")
        node_targets = ["dlogs-node-exporter:9100"]
        print("[yellow]Host metrics:[/yellow] falling back to container node-exporter on this OS")

    gpu_override = _bool_env("DLOGS_ENABLE_GPU")
    gpu_mode: str | None = None
    if gpu_override is False:
        print("[cyan]GPU monitoring:[/cyan] disabled by DLOGS_ENABLE_GPU")
        _stop_exporter(workdir, "gpu-exporter")
    else:
        if _host_gpu_available() and _ensure_exporter_running(
            workdir,
            "gpu-exporter",
            "dlogs.gpu_exporter",
            GPU_EXPORTER_PORT,
            "nvidia_smi_gpu_info",
        ):
            gpu_mode = "host"
            print("[cyan]GPU monitoring:[/cyan] using native host exporter on port 9835")
        elif _docker_supports_gpu(docker_env):
            gpu_mode = "docker"
            print("[cyan]GPU monitoring:[/cyan] using Docker Nvidia runtime")
        else:
            _stop_exporter(workdir, "gpu-exporter")
            if _host_gpu_available():
                print(
                    "[yellow]GPU monitoring:[/yellow] host GPU detected, but no compatible exporter or Docker Nvidia runtime is available"
                )

    if gpu_mode == "host":
        gpu_targets = [f"host.docker.internal:{GPU_EXPORTER_PORT}"]
    elif gpu_mode == "docker":
        gpu_targets = ["dlogs-gpu:9835"]
        compose_env["COMPOSE_PROFILES"] = "gpu"

    _write_prometheus_targets(workdir, node_targets, host_targets, gpu_targets)
    return compose_env or None


def _ensure_runtime_config(workdir: Path) -> int:
    log_dir, source = _resolve_log_dir(workdir)
    if not log_dir:
        print(
            "[red]ERROR:[/red] Could not detect a default log directory for this OS.\n"
            "Set [bold]DLOGS_LOG_DIR[/bold] in your shell or in "
            f"{workdir / '.env'} and retry."
        )
        return 2

    try:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"[red]ERROR:[/red] Could not create log directory {log_dir}: {exc}")
        return 2

    env_path = workdir / ".env"
    existing_value = _read_env_value(env_path, "DLOGS_LOG_DIR")
    default_log_dir = _default_log_dir()
    if existing_value and default_log_dir and _should_migrate_log_dir(existing_value, default_log_dir):
        log_dir = default_log_dir
        try:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(f"[red]ERROR:[/red] Could not create log directory {log_dir}: {exc}")
            return 2
        _write_env_value(env_path, "DLOGS_LOG_DIR", log_dir)
        source = f"migrated legacy {existing_value} -> {log_dir}"
    elif not existing_value:
        _write_env_value(env_path, "DLOGS_LOG_DIR", log_dir)
        source = f"{source} -> wrote {env_path.name}"

    _ensure_state_dirs(workdir)
    print(f"[cyan]Host log directory:[/cyan] {log_dir} [dim]({source})[/dim]")
    return 0


def _print_exporter_status(workdir: Path) -> None:
    statuses = [
        ("Host exporter", HOST_EXPORTER_PORT, "node_cpu_seconds_total"),
        ("GPU exporter", GPU_EXPORTER_PORT, "nvidia_smi_gpu_info"),
    ]
    for label, port, marker in statuses:
        if _http_contains(f"http://127.0.0.1:{port}/metrics", marker):
            print(f"[cyan]{label}:[/cyan] up on localhost:{port}")


def cmd_init(out_dir: Path) -> int:
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    src = _assets_dir()
    if not src.exists():
        print("[red]ERROR:[/red] assets folder missing in package build.")
        return 2

    for name in ["docker-compose.yml", "config", "dashboards", "provisioning"]:
        asset = src / name
        if not asset.exists():
            continue

        destination = out_dir / name
        if asset.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(asset, destination)
        else:
            shutil.copy2(asset, destination)

    rc = _ensure_runtime_config(out_dir)
    if rc != 0:
        return rc

    _clear_prometheus_targets(out_dir)
    print(f"[green]✅ Initialized stack files at:[/green] {out_dir}")
    return 0


def cmd_up(workdir: Path) -> int:
    compose = workdir / "docker-compose.yml"
    if not compose.exists():
        print("[yellow]Compose not found. Running init first...[/yellow]")
        rc = cmd_init(workdir)
        if rc != 0:
            return rc
    else:
        rc = _ensure_runtime_config(workdir)
        if rc != 0:
            return rc

    compose_env = _prepare_runtime(workdir)
    return _run(["docker", "compose", "-f", str(compose), "up", "-d"], env=compose_env)


def cmd_down(workdir: Path) -> int:
    compose = workdir / "docker-compose.yml"
    if not compose.exists():
        print("[red]No docker-compose.yml found in workdir[/red]")
        return 2

    docker_env = _docker_env()
    rc = _run(["docker", "compose", "-f", str(compose), "down"], env=docker_env)
    _stop_exporter(workdir, "gpu-exporter")
    _stop_exporter(workdir, "host-exporter")
    _clear_prometheus_targets(workdir)
    return rc


def cmd_status(workdir: Path) -> int:
    compose = workdir / "docker-compose.yml"
    if not compose.exists():
        print("[red]No docker-compose.yml found in workdir[/red]")
        return 2

    docker_env = _docker_env()
    rc = _run(["docker", "compose", "-f", str(compose), "ps"], env=docker_env)
    _print_exporter_status(workdir)
    return rc


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ["--help", "-h"]:
        print(
            "[bold]dlogs[/bold]\n"
            "Commands:\n"
            "  init <dir>\n"
            "  up <dir>\n"
            "  down <dir>\n"
            "  status <dir>\n"
        )
        sys.exit(0)

    cmd = sys.argv[1].lower()
    workdir = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path.cwd()

    if cmd == "init":
        sys.exit(cmd_init(workdir))
    if cmd == "up":
        sys.exit(cmd_up(workdir))
    if cmd == "down":
        sys.exit(cmd_down(workdir))
    if cmd == "status":
        sys.exit(cmd_status(workdir))

    print(f"[red]Unknown command:[/red] {cmd}")
    sys.exit(2)


if __name__ == "__main__":
    main()
