from __future__ import annotations

import argparse
import csv
import subprocess
from io import StringIO

from dlogs.exporter_utils import metric_line, run_metrics_server


GPU_QUERY_FIELDS = [
    "index",
    "uuid",
    "name",
    "driver_version",
    "vbios_version",
    "temperature.gpu",
    "utilization.gpu",
    "utilization.memory",
    "memory.total",
    "memory.used",
    "power.draw",
    "power.limit",
    "fan.speed",
    "clocks.current.graphics",
    "clocks.max.graphics",
    "clocks.current.memory",
    "clocks.max.memory",
]


def _read_gpu_rows() -> list[dict[str, str]]:
    command = [
        "nvidia-smi",
        f"--query-gpu={','.join(GPU_QUERY_FIELDS)}",
        "--format=csv,noheader,nounits",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    reader = csv.reader(StringIO(result.stdout))
    rows: list[dict[str, str]] = []
    for values in reader:
        if not values:
            continue
        rows.append({field: value.strip() for field, value in zip(GPU_QUERY_FIELDS, values, strict=True)})
    return rows


def _float_value(raw_value: str) -> float | None:
    if raw_value in {"N/A", "[N/A]", "[Not Supported]", "Not Supported", ""}:
        return None
    return float(raw_value)


def collect_metrics() -> str:
    rows = _read_gpu_rows()
    metrics = [metric_line("dlogs_gpu_exporter_info", 1)]

    for row in rows:
        labels = {
            "gpu": row["index"],
            "uuid": row["uuid"],
            "name": row["name"],
            "driver_version": row["driver_version"],
            "vbios_version": row["vbios_version"],
        }
        metrics.extend(
            [
                metric_line("nvidia_smi_gpu_info", 1, labels),
                metric_line("nvidia_smi_index", float(row["index"]), labels),
            ]
        )

        maybe_metrics = {
            "nvidia_smi_temperature_gpu": _float_value(row["temperature.gpu"]),
            "nvidia_smi_utilization_gpu_ratio": (
                None
                if _float_value(row["utilization.gpu"]) is None
                else _float_value(row["utilization.gpu"]) / 100.0
            ),
            "nvidia_smi_utilization_memory_ratio": (
                None
                if _float_value(row["utilization.memory"]) is None
                else _float_value(row["utilization.memory"]) / 100.0
            ),
            "nvidia_smi_memory_total_bytes": (
                None
                if _float_value(row["memory.total"]) is None
                else _float_value(row["memory.total"]) * 1024 * 1024
            ),
            "nvidia_smi_memory_used_bytes": (
                None
                if _float_value(row["memory.used"]) is None
                else _float_value(row["memory.used"]) * 1024 * 1024
            ),
            "nvidia_smi_power_draw_watts": _float_value(row["power.draw"]),
            "nvidia_smi_power_default_limit_watts": _float_value(row["power.limit"]),
            "nvidia_smi_fan_speed_ratio": (
                None
                if _float_value(row["fan.speed"]) is None
                else _float_value(row["fan.speed"]) / 100.0
            ),
            "nvidia_smi_clocks_current_graphics_clock_hz": (
                None
                if _float_value(row["clocks.current.graphics"]) is None
                else _float_value(row["clocks.current.graphics"]) * 1_000_000
            ),
            "nvidia_smi_clocks_max_graphics_clock_hz": (
                None
                if _float_value(row["clocks.max.graphics"]) is None
                else _float_value(row["clocks.max.graphics"]) * 1_000_000
            ),
            "nvidia_smi_clocks_current_memory_clock_hz": (
                None
                if _float_value(row["clocks.current.memory"]) is None
                else _float_value(row["clocks.current.memory"]) * 1_000_000
            ),
            "nvidia_smi_clocks_max_memory_clock_hz": (
                None
                if _float_value(row["clocks.max.memory"]) is None
                else _float_value(row["clocks.max.memory"]) * 1_000_000
            ),
        }

        for metric_name, value in maybe_metrics.items():
            if value is None:
                continue
            metrics.append(metric_line(metric_name, value, labels))

    return "".join(metrics)


def main() -> None:
    parser = argparse.ArgumentParser(description="dLogs Nvidia GPU metrics exporter")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9835)
    args = parser.parse_args()
    run_metrics_server(args.host, args.port, collect_metrics)


if __name__ == "__main__":
    main()
