from __future__ import annotations

import asyncio
import time
from typing import Any

import aiodocker


async def collect_container_stats() -> list[dict[str, Any]]:
    """Collect stats for all running containers via Docker API."""
    results: list[dict[str, Any]] = []
    docker = aiodocker.Docker()
    try:
        containers = await docker.containers.list()
        tasks = [_get_one_stat(c) for c in containers]
        stats_list = await asyncio.gather(*tasks, return_exceptions=True)
        for s in stats_list:
            if isinstance(s, dict):
                results.append(s)
    finally:
        await docker.close()
    return results


async def _get_one_stat(container: aiodocker.docker.DockerContainer) -> dict[str, Any]:
    info = await container.show()
    name = info["Name"].lstrip("/")
    state = info["State"]
    restart_count = info.get("RestartCount", 0)

    # One-shot stats (stream=False) returns a list with one entry
    stats_result = await container.stats(stream=False)

    if not stats_result:
        return _empty_stat(name, state, restart_count)

    stats = stats_result[0] if isinstance(stats_result, list) else stats_result

    cpu_pct = _calc_cpu_percent_oneshot(stats)
    mem_usage, mem_limit, mem_pct = _calc_mem(stats)
    net_rx, net_tx = _calc_net(stats)
    blk_read, blk_write = _calc_blkio(stats)

    return {
        "name": name,
        "id": info["Id"][:12],
        "image": info["Config"]["Image"],
        "status": state.get("Status", "unknown"),
        "started_at": state.get("StartedAt", ""),
        "restart_count": restart_count,
        "cpu_pct": round(cpu_pct, 2),
        "mem_usage": mem_usage,
        "mem_limit": mem_limit,
        "mem_pct": round(mem_pct, 2),
        "net_rx": net_rx,
        "net_tx": net_tx,
        "blk_read": blk_read,
        "blk_write": blk_write,
        "ts": time.time(),
    }


def _empty_stat(name: str, state: dict, restart_count: int) -> dict[str, Any]:
    return {
        "name": name, "id": "", "image": "", "status": state.get("Status", "unknown"),
        "started_at": "", "restart_count": restart_count,
        "cpu_pct": 0.0, "mem_usage": 0, "mem_limit": 0, "mem_pct": 0.0,
        "net_rx": 0, "net_tx": 0, "blk_read": 0, "blk_write": 0,
        "ts": time.time(),
    }


def _calc_cpu_percent_oneshot(stats: dict) -> float:
    """Calculate CPU% from one-shot stats using cpu_stats vs precpu_stats."""
    cpu = stats.get("cpu_stats", {})
    precpu = stats.get("precpu_stats", {})
    cpu_delta = (
        cpu.get("cpu_usage", {}).get("total_usage", 0)
        - precpu.get("cpu_usage", {}).get("total_usage", 0)
    )
    sys_delta = (
        cpu.get("system_cpu_usage", 0)
        - precpu.get("system_cpu_usage", 0)
    )
    n_cpus = cpu.get("online_cpus") or len(
        cpu.get("cpu_usage", {}).get("percpu_usage", [1])
    )
    if sys_delta > 0 and cpu_delta >= 0:
        return (cpu_delta / sys_delta) * n_cpus * 100.0
    return 0.0


def _calc_mem(stats: dict) -> tuple[int, int, float]:
    mem = stats.get("memory_stats", {})
    usage = mem.get("usage", 0) - mem.get("stats", {}).get("cache", 0)
    if usage < 0:
        usage = mem.get("usage", 0)
    limit = mem.get("limit", 0)
    pct = (usage / limit * 100.0) if limit > 0 else 0.0
    return usage, limit, pct


def _calc_net(stats: dict) -> tuple[int, int]:
    networks = stats.get("networks", {})
    rx = sum(v.get("rx_bytes", 0) for v in networks.values())
    tx = sum(v.get("tx_bytes", 0) for v in networks.values())
    return rx, tx


def _calc_blkio(stats: dict) -> tuple[int, int]:
    blkio = stats.get("blkio_stats", {})
    entries = blkio.get("io_service_bytes_recursive") or []
    read = sum(e["value"] for e in entries if e.get("op") == "read")
    write = sum(e["value"] for e in entries if e.get("op") == "write")
    return read, write
