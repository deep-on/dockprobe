from __future__ import annotations

import os
import subprocess
import time
from typing import Any


def collect_host_stats() -> dict[str, Any]:
    """Collect host system stats via /host_sys, /host_proc, /host_root."""
    return {
        "cpu_temp": _cpu_temp(),
        "gpu_temp": _gpu_temp(),
        "disk": _disk_usage(),
        "load_avg": _load_avg(),
        "ts": time.time(),
    }


def _cpu_temp() -> float | None:
    """Read CPU temperature from thermal zones."""
    base = "/host_sys/class/thermal"
    if not os.path.isdir(base):
        return None
    temps: list[float] = []
    try:
        for tz in os.listdir(base):
            tpath = os.path.join(base, tz, "temp")
            if os.path.isfile(tpath):
                with open(tpath) as f:
                    val = int(f.read().strip())
                    temps.append(val / 1000.0)
    except (OSError, ValueError):
        pass
    return round(max(temps), 1) if temps else None


def _gpu_temp() -> float | None:
    """Read GPU temp via nvidia-smi."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            timeout=5, text=True,
        )
        temps = [float(line.strip()) for line in out.strip().splitlines() if line.strip()]
        return max(temps) if temps else None
    except (FileNotFoundError, subprocess.SubprocessError, ValueError):
        return None


def _disk_usage() -> list[dict[str, Any]]:
    """Disk usage for /host_root mount."""
    disks: list[dict[str, Any]] = []
    root = "/host_root"
    try:
        st = os.statvfs(root)
        total = st.f_blocks * st.f_frsize
        free = st.f_bfree * st.f_frsize
        used = total - free
        pct = (used / total * 100.0) if total > 0 else 0.0
        disks.append({
            "mount": "/",
            "total": total,
            "used": used,
            "free": free,
            "pct": round(pct, 1),
        })
    except OSError:
        pass
    return disks


def _load_avg() -> list[float]:
    """Read load average from /host_proc/loadavg."""
    try:
        with open("/host_proc/loadavg") as f:
            parts = f.read().strip().split()
            return [float(parts[0]), float(parts[1]), float(parts[2])]
    except (OSError, ValueError, IndexError):
        try:
            load = os.getloadavg()
            return [round(load[0], 2), round(load[1], 2), round(load[2], 2)]
        except OSError:
            return [0.0, 0.0, 0.0]
