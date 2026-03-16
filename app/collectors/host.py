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
        "memory": _memory_usage(),
        "load_avg": _load_avg(),
        "cpu_cores": os.cpu_count() or 1,
        "cpu_pct": _cpu_percent(),
        "ts": time.time(),
    }


# ── Host CPU % via /proc/stat ──

_prev_cpu: list[int] | None = None


def _read_cpu_times() -> list[int] | None:
    """Read aggregate CPU times from /host_proc/stat (or /proc/stat)."""
    for path in ("/host_proc/stat", "/proc/stat"):
        try:
            with open(path) as f:
                for line in f:
                    if line.startswith("cpu "):
                        # user nice system idle iowait irq softirq steal
                        return [int(x) for x in line.split()[1:9]]
        except OSError:
            continue
    return None


def _cpu_percent() -> float | None:
    """Calculate host CPU usage % between two collection cycles."""
    global _prev_cpu
    cur = _read_cpu_times()
    if cur is None:
        return None
    if _prev_cpu is None:
        _prev_cpu = cur
        return None  # need two samples

    deltas = [c - p for c, p in zip(cur, _prev_cpu)]
    _prev_cpu = cur
    total = sum(deltas)
    if total <= 0:
        return 0.0
    idle = deltas[3] + deltas[4]  # idle + iowait
    return round((1 - idle / total) * 100, 1)


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


def _memory_usage() -> dict[str, Any] | None:
    """Read host memory usage from /proc/meminfo."""
    for path in ("/host_proc/meminfo", "/proc/meminfo"):
        try:
            info: dict[str, int] = {}
            with open(path) as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2 and parts[0].rstrip(":") in (
                        "MemTotal", "MemAvailable", "Buffers", "Cached", "MemFree",
                    ):
                        info[parts[0].rstrip(":")] = int(parts[1]) * 1024  # kB -> bytes
            total = info.get("MemTotal", 0)
            if total <= 0:
                continue
            available = info.get("MemAvailable")
            if available is not None:
                used = total - available
            else:
                used = total - info.get("MemFree", 0) - info.get("Buffers", 0) - info.get("Cached", 0)
            pct = round(used / total * 100, 1) if total > 0 else 0.0
            return {"total": total, "used": used, "available": total - used, "pct": pct}
        except (OSError, ValueError):
            continue
    return None


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
