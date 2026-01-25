import os
import sys
import shutil
import subprocess
from pathlib import Path
from importlib import resources

from rich import print


def _run(cmd: list[str]) -> int:
    print(f"[bold cyan]$ {' '.join(cmd)}[/bold cyan]")
    return subprocess.call(cmd)


def _assets_dir() -> Path:
    # dlogs/assets packaged inside wheel
    return Path(resources.files("dlogs")) / "assets"


def cmd_init(out_dir: Path) -> int:
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    src = _assets_dir()
    if not src.exists():
        print("[red]ERROR:[/red] assets folder missing in package build.")
        return 2

    # Copy assets into project folder
    for name in ["docker-compose.yml", "config", "dashboards", "provisioning"]:
        p = src / name
        if not p.exists():
            continue

        dest = out_dir / name
        if p.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(p, dest)
        else:
            shutil.copy2(p, dest)

    print(f"[green]✅ Initialized stack files at:[/green] {out_dir}")
    return 0


def cmd_up(workdir: Path) -> int:
    compose = workdir / "docker-compose.yml"
    if not compose.exists():
        print("[yellow]Compose not found. Running init first...[/yellow]")
        rc = cmd_init(workdir)
        if rc != 0:
            return rc

    return _run(["docker", "compose", "-f", str(compose), "up", "-d"])


def cmd_down(workdir: Path) -> int:
    compose = workdir / "docker-compose.yml"
    if not compose.exists():
        print("[red]No docker-compose.yml found in workdir[/red]")
        return 2
    return _run(["docker", "compose", "-f", str(compose), "down"])


def cmd_status(workdir: Path) -> int:
    compose = workdir / "docker-compose.yml"
    if not compose.exists():
        print("[red]No docker-compose.yml found in workdir[/red]")
        return 2
    return _run(["docker", "compose", "-f", str(compose), "ps"])


def main():
    # super simple argparse (no extra deps)
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
