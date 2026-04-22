from __future__ import annotations

import argparse
import os
from pathlib import Path

from dlogs.exporter_utils import metric_line, run_metrics_server


def _read_boot_time() -> float:
    with Path("/proc/stat").open(encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("btime "):
                return float(line.split()[1])
    raise RuntimeError("Could not read boot time from /proc/stat")


def _collect_uname_metrics() -> list[str]:
    uname = os.uname()
    return [
        metric_line(
            "node_uname_info",
            1,
            {
                "sysname": uname.sysname,
                "release": uname.release,
                "version": uname.version,
                "machine": uname.machine,
                "nodename": uname.nodename,
                "domainname": "",
            },
        )
    ]


def _collect_cpu_metrics() -> list[str]:
    metrics: list[str] = []
    clock_ticks = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
    mode_names = ["user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal"]

    with Path("/proc/stat").open(encoding="utf-8") as handle:
        for line in handle:
            if not line.startswith("cpu") or line.startswith("cpu "):
                continue

            fields = line.split()
            cpu = fields[0][3:]
            values = fields[1 : 1 + len(mode_names)]
            for mode, raw_value in zip(mode_names, values, strict=True):
                metrics.append(
                    metric_line(
                        "node_cpu_seconds_total",
                        float(raw_value) / clock_ticks,
                        {"cpu": cpu, "mode": mode},
                    )
                )

    return metrics


def _collect_memory_metrics() -> list[str]:
    wanted = {
        "MemTotal": "node_memory_MemTotal_bytes",
        "MemAvailable": "node_memory_MemAvailable_bytes",
        "MemFree": "node_memory_MemFree_bytes",
        "Active": "node_memory_Active_bytes",
        "Inactive": "node_memory_Inactive_bytes",
        "Dirty": "node_memory_Dirty_bytes",
        "KernelStack": "node_memory_KernelStack_bytes",
    }
    metrics: list[str] = []

    with Path("/proc/meminfo").open(encoding="utf-8") as handle:
        for line in handle:
            name, raw_value = line.split(":", 1)
            metric_name = wanted.get(name)
            if not metric_name:
                continue

            value = int(raw_value.strip().split()[0]) * 1024
            metrics.append(metric_line(metric_name, value))

    return metrics


def _collect_load_metrics() -> list[str]:
    load1, load5, load15, *_ = Path("/proc/loadavg").read_text(encoding="utf-8").split()
    return [
        metric_line("node_load1", float(load1)),
        metric_line("node_load5", float(load5)),
        metric_line("node_load15", float(load15)),
    ]


def _collect_filesystem_metrics() -> list[str]:
    metrics: list[str] = []
    seen_mounts: set[str] = set()

    with Path("/proc/self/mounts").open(encoding="utf-8") as handle:
        for line in handle:
            device, mountpoint, fstype, *_ = line.split()
            mountpoint = mountpoint.replace("\\040", " ")
            if mountpoint in seen_mounts:
                continue

            seen_mounts.add(mountpoint)
            try:
                stats = os.statvfs(mountpoint)
            except OSError:
                continue

            labels = {
                "device": device,
                "mountpoint": mountpoint,
                "fstype": fstype,
            }
            block_size = stats.f_frsize or stats.f_bsize
            metrics.extend(
                [
                    metric_line("node_filesystem_size_bytes", stats.f_blocks * block_size, labels),
                    metric_line("node_filesystem_free_bytes", stats.f_bfree * block_size, labels),
                    metric_line("node_filesystem_avail_bytes", stats.f_bavail * block_size, labels),
                ]
            )

    return metrics


def _collect_disk_metrics() -> list[str]:
    metrics: list[str] = []
    with Path("/proc/diskstats").open(encoding="utf-8") as handle:
        for line in handle:
            fields = line.split()
            if len(fields) < 10:
                continue

            device = fields[2]
            sectors_read = int(fields[5])
            sectors_written = int(fields[9])
            metrics.extend(
                [
                    metric_line("node_disk_read_bytes_total", sectors_read * 512, {"device": device}),
                    metric_line(
                        "node_disk_written_bytes_total",
                        sectors_written * 512,
                        {"device": device},
                    ),
                ]
            )

    return metrics


def _collect_network_metrics() -> list[str]:
    metrics: list[str] = []
    with Path("/proc/net/dev").open(encoding="utf-8") as handle:
        for line in handle.readlines()[2:]:
            name, raw_values = line.split(":", 1)
            values = raw_values.split()
            device = name.strip()
            metrics.extend(
                [
                    metric_line("node_network_receive_bytes_total", int(values[0]), {"device": device}),
                    metric_line("node_network_transmit_bytes_total", int(values[8]), {"device": device}),
                ]
            )

    return metrics


def collect_metrics() -> str:
    metrics = [
        metric_line("node_boot_time_seconds", _read_boot_time()),
        metric_line("dlogs_host_exporter_info", 1, {"platform": "linux"}),
    ]
    metrics.extend(_collect_uname_metrics())
    metrics.extend(_collect_cpu_metrics())
    metrics.extend(_collect_memory_metrics())
    metrics.extend(_collect_load_metrics())
    metrics.extend(_collect_filesystem_metrics())
    metrics.extend(_collect_disk_metrics())
    metrics.extend(_collect_network_metrics())
    return "".join(metrics)


def main() -> None:
    parser = argparse.ArgumentParser(description="dLogs Linux host metrics exporter")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9100)
    args = parser.parse_args()
    run_metrics_server(args.host, args.port, collect_metrics)


if __name__ == "__main__":
    main()
