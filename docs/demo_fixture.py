#!/usr/bin/env python3
"""A DockProbe that monitors nothing.

Serves the real dashboard against invented data, so the screenshots in the
README can be produced without pointing a camera at somebody's actual machine.
The previous approach — capture a live dashboard, then paint rectangles over the
container names — shipped a picture with the original text still legible between
the rectangles. Data that was never real cannot leak.

Deliberately dependency-free: the standard library only, so anyone who clones
the repository can regenerate the screenshots.

    python3 docs/demo_fixture.py 8900     # then open http://127.0.0.1:8900

Samples advance per request rather than per second. Chrome's --virtual-time-budget
fires the page's ten-second refresh as fast as it can, so the charts fill with ten
minutes of history in the time it takes to make sixty requests to localhost — and
they come out identical on every run.
"""
from __future__ import annotations

import json
import math
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"

# A plausible host: sixteen cores, a GPU, a week of uptime. Nothing here exists.
CORES = 16
CONTAINERS = [
    # name, base cpu %, memory bytes, restarts, running
    ("web-api",        22.0,  512 * 2**20, 0, True),
    ("worker-queue",   64.0,  892 * 2**20, 0, True),
    ("postgres-main",  18.0, 2400 * 2**20, 0, True),
    ("redis-cache",     3.5,  180 * 2**20, 0, True),
    ("nginx-edge",      1.8,   64 * 2**20, 0, True),
    ("ml-inference",  310.0, 6100 * 2**20, 0, True),
    ("media-encoder", 480.0, 1800 * 2**20, 2, True),
    ("auth-service",    6.2,  220 * 2**20, 0, True),
    ("search-index",   28.0, 1500 * 2**20, 0, True),
    ("metrics-agent",   2.1,   96 * 2**20, 0, True),
    ("dockprobe",       0.9,   48 * 2**20, 0, True),
    ("backup-runner",   0.0,            0, 1, False),
]

SECURITY = [
    ("critical", "Container: media-encoder", "Runs as root",
     "Add a non-root USER to the image, or run with --user 1000:1000."),
    ("warning", "Container: web-api", "No memory limit set",
     "docker update --memory=2g web-api"),
    ("warning", "Container: postgres-main", "Port published on 0.0.0.0",
     "Bind to 127.0.0.1 and reach it through the internal network instead."),
    ("info", "Host", "Docker socket mounted read-only", "No action needed."),
]

_tick = 0


def sample(i: int) -> float:
    """A repeatable wobble in [0.55, 1.45] — the same on every run."""
    return 1.0 + 0.30 * math.sin(i / 3.7) + 0.15 * math.sin(i / 1.3)


def host_now(i: int) -> dict:
    used = int((26.0 + 5.0 * sample(i)) * 2**30)
    return {
        "ts": time.time(),
        "cpu_pct": round(min(99.0, 26.0 + 16.0 * sample(i)), 1),
        "cpu_cores": CORES,
        "cpu_temp": round(46.0 + 7.0 * sample(i), 1),
        "gpu_temp": round(58.0 + 6.0 * sample(i + 2), 1),
        "gpu_util": round(min(99.0, 34.0 + 28.0 * sample(i + 5)), 1),
        "memory": {"used": used, "total": 64 * 2**30,
                   "pct": round(used / (64 * 2**30) * 100, 1)},
        "disk": [{"mount": "/", "used": 611 * 2**30, "total": 916 * 2**30, "pct": 66.7}],
        "load_avg": [round(2.4 + 1.4 * sample(i), 2),
                     round(2.2 + 0.9 * sample(i + 1), 2),
                     round(2.0 + 0.5 * sample(i + 2), 2)],
    }


def containers_now(i: int) -> list[dict]:
    out = []
    for n, (name, cpu, mem, restarts, running) in enumerate(CONTAINERS):
        wobble = sample(i + n * 2)
        out.append({
            "name": name,
            "status": "running" if running else "exited",
            "cpu_pct": round(cpu * wobble, 1) if running else 0.0,
            "mem_pct": round(mem / (64 * 2**30) * 100, 1) if running else 0.0,
            "mem_usage": int(mem * (0.94 + 0.12 * wobble)) if running else 0,
            "net_rx": int((1.4 + 0.4 * n) * 2**30),
            "net_tx": int((0.8 + 0.3 * n) * 2**30),
            "blk_read": int((120 + 40 * n) * 2**20),
            "blk_write": int((60 + 25 * n) * 2**20),
            "restart_count": restarts,
        })
    return out


def anomalies_now(i: int) -> list[dict]:
    """One live anomaly, so the screenshot shows the feature doing its job."""
    return [{
        "ts": time.time(), "type": "cpu_high", "target": "media-encoder",
        "value": round(480.0 * sample(i), 1),
        "msg": f"Container media-encoder CPU {480.0 * sample(i):.1f}% (>400.0% x3)",
        "rec": "docker stats media-encoder | docker restart media-encoder | "
               "Set CPU limit: docker update --cpus=4 media-encoder",
    }]


def alerts_history() -> list[dict]:
    now = time.time()
    rows = [
        (420, "cpu_high", "media-encoder", "Container media-encoder CPU 612.4% (>400.0% x3)"),
        (1860, "restart", "backup-runner", "Container backup-runner restarted (count 0 -> 1)"),
        (5400, "mem_high", "ml-inference", "Container ml-inference Memory 91.2% (>90.0%)"),
        (9900, "cpu_high", "worker-queue", "Container worker-queue CPU 428.7% (>400.0% x3)"),
        (18000, "disk_high", "/", "Host disk / at 91.4% (>90.0%)"),
        (26400, "net_spike", "web-api", "Container web-api Network RX spike: 1.2 GB -> 14.8 GB"),
    ]
    return [{"ts": now - ago, "type": t, "target": g, "value": None, "msg": m}
            for ago, t, g, m in rows]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep the capture output readable
        pass

    def _send(self, body: bytes, ctype: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj) -> None:
        self._send(json.dumps(obj).encode(), "application/json")

    def do_GET(self):  # noqa: N802 — BaseHTTPRequestHandler's spelling
        global _tick
        path = urlparse(self.path).path

        if path == "/":
            return self._send((STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path.startswith("/static/"):
            name = Path(path).name
            target = (STATIC / name).resolve()
            if target.parent == STATIC.resolve() and target.is_file():
                kind = "image/png" if name.endswith(".png") else "application/octet-stream"
                return self._send(target.read_bytes(), kind)
            self.send_response(404); self.send_header("Content-Length", "0"); self.end_headers()
            return

        if path == "/api/health":
            return self._json({"status": "ok", "version": "1.0.0", "uptime_cycles": 60480})
        if path == "/api/current":
            _tick += 1
            i = _tick
            return self._json({
                "ts": time.time(),
                "host": host_now(i),
                "containers": containers_now(i),
                "anomalies": anomalies_now(i),
                "images": {"image_size": 41 * 2**30, "image_count": 38,
                           "cache_size": 7 * 2**30, "volume_size": 22 * 2**30,
                           "volume_count": 11, "container_rw_size": 3 * 2**30},
                "security": {
                    "warnings": [{"severity": s, "target": t, "title": ti, "recommendation": r}
                                 for s, t, ti, r in SECURITY],
                    "summary": {"critical": 1, "warning": 2, "info": 1,
                                "unavailable": 0, "total": 4},
                    "last_scan_ts": time.time() - 90,
                },
            })
        if path == "/api/v2/summary":
            i = max(_tick, 1)
            host = host_now(i)
            running = [c for c in containers_now(i) if c["status"] == "running"]
            return self._json({
                "host": {"cpu_pct": host["cpu_pct"], "mem_pct": host["memory"]["pct"],
                         "disk_pct": host["disk"][0]["pct"], "gpu_temp": host["gpu_temp"],
                         "gpu_util": host["gpu_util"]},
                "containers": {"total": len(CONTAINERS), "running": len(running),
                               "stopped": len(CONTAINERS) - len(running)},
                "anomalies": {"active": 1, "last_message": anomalies_now(i)[0]["msg"]},
                "version": "1.0.0"})
        if path.startswith("/api/alerts"):
            return self._json(alerts_history())
        if path == "/api/session":
            return self._json({"user": "demo", "ip": "10.0.1.50",
                               "active_connections": 1, "max_connections": 5,
                               "active_ips": ["10.0.1.50"]})
        if path == "/api/settings":
            return self._json({"max_connections": 5, "refresh_interval": 10})
        if path == "/api/security":
            return self._json({"warnings": [], "summary": {"critical": 0, "warning": 0,
                                                           "info": 0, "unavailable": 0, "total": 0}})
        if path == "/api/github-stats":
            return self._json({"stars": 20, "forks": 0, "watchers": 20, "open_issues": 0,
                               "repo": "deep-on/dockprobe",
                               "url": "https://github.com/deep-on/dockprobe"})

        self.send_response(404); self.send_header("Content-Length", "0"); self.end_headers()


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8900
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"demo fixture on http://127.0.0.1:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
