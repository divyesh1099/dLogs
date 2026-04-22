from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from typing import Callable


def _escape_label_value(value: object) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace('"', '\\"')
    )


def metric_line(name: str, value: float | int, labels: dict[str, object] | None = None) -> str:
    label_text = ""
    if labels:
        label_text = "{" + ",".join(
            f'{key}="{_escape_label_value(labels[key])}"' for key in sorted(labels)
        ) + "}"
    return f"{name}{label_text} {value}\n"


class _ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def run_metrics_server(host: str, port: int, collector: Callable[[], str]) -> None:
    class MetricsHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path not in {"/", "/metrics"}:
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                return

            try:
                body = collector().encode("utf-8")
                self.send_response(HTTPStatus.OK)
            except Exception as exc:  # pragma: no cover - exporter runtime safeguard
                body = f"exporter_scrape_error {exc}\n".encode("utf-8", errors="replace")
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)

            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    with _ThreadedHTTPServer((host, port), MetricsHandler) as server:
        server.serve_forever()
