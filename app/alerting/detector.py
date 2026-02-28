from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app import config


@dataclass
class AnomalyDetector:
    """Stateful anomaly detection across collection cycles."""

    # Container CPU consecutive high counts: {container_name: count}
    _cpu_counts: dict[str, int] = field(default_factory=dict)
    # Previous restart counts: {container_name: count}
    _prev_restarts: dict[str, int] = field(default_factory=dict)
    # Previous network RX: {container_name: bytes}
    _prev_net_rx: dict[str, int] = field(default_factory=dict)
    # Active anomalies for dashboard display
    active_anomalies: list[dict[str, Any]] = field(default_factory=list)

    def check(
        self,
        containers: list[dict[str, Any]],
        host: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Run all detection rules; return list of new alerts."""
        alerts: list[dict[str, Any]] = []
        now = time.time()
        self.active_anomalies = []

        for c in containers:
            name = c["name"]

            # --- Container CPU ---
            if c["cpu_pct"] > config.CPU_THRESHOLD:
                self._cpu_counts[name] = self._cpu_counts.get(name, 0) + 1
            else:
                self._cpu_counts[name] = 0

            if self._cpu_counts.get(name, 0) >= config.CPU_CONSECUTIVE:
                a = {"type": "cpu_high", "target": name,
                     "value": c["cpu_pct"], "ts": now,
                     "msg": f"Container {name} CPU {c['cpu_pct']:.1f}% (>{config.CPU_THRESHOLD}% x{config.CPU_CONSECUTIVE})"}
                alerts.append(a)
                self.active_anomalies.append(a)

            # --- Container Memory ---
            if c["mem_pct"] > config.MEM_THRESHOLD:
                a = {"type": "mem_high", "target": name,
                     "value": c["mem_pct"], "ts": now,
                     "msg": f"Container {name} Memory {c['mem_pct']:.1f}% (>{config.MEM_THRESHOLD}%)"}
                alerts.append(a)
                self.active_anomalies.append(a)

            # --- Restart count ---
            prev = self._prev_restarts.get(name)
            cur = c.get("restart_count", 0)
            if prev is not None and cur > prev:
                a = {"type": "restart", "target": name,
                     "value": cur, "ts": now,
                     "msg": f"Container {name} restarted (count {prev} -> {cur})"}
                alerts.append(a)
                self.active_anomalies.append(a)
            self._prev_restarts[name] = cur

            # --- Network spike ---
            prev_rx = self._prev_net_rx.get(name)
            cur_rx = c.get("net_rx", 0)
            if prev_rx is not None and prev_rx > 0:
                if cur_rx > prev_rx * config.NET_SPIKE_MULTIPLIER and cur_rx > config.NET_SPIKE_MIN_BYTES:
                    a = {"type": "net_spike", "target": name,
                         "value": cur_rx, "ts": now,
                         "msg": f"Container {name} Network RX spike: {_fmt_bytes(prev_rx)} -> {_fmt_bytes(cur_rx)}"}
                    alerts.append(a)
                    self.active_anomalies.append(a)
            self._prev_net_rx[name] = cur_rx

        # --- Host CPU Temperature ---
        cpu_temp = host.get("cpu_temp")
        if cpu_temp is not None and cpu_temp > config.HOST_TEMP_THRESHOLD:
            a = {"type": "host_temp", "target": "host",
                 "value": cpu_temp, "ts": now,
                 "msg": f"Host CPU temperature {cpu_temp}°C (>{config.HOST_TEMP_THRESHOLD}°C)"}
            alerts.append(a)
            self.active_anomalies.append(a)

        # --- Host Disk ---
        for d in host.get("disk", []):
            if d["pct"] > config.DISK_THRESHOLD:
                a = {"type": "disk_high", "target": d["mount"],
                     "value": d["pct"], "ts": now,
                     "msg": f"Host disk {d['mount']} usage {d['pct']:.1f}% (>{config.DISK_THRESHOLD}%)"}
                alerts.append(a)
                self.active_anomalies.append(a)

        return alerts


def _fmt_bytes(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024  # type: ignore[assignment]
    return f"{b:.1f}PB"
