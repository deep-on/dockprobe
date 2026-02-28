from __future__ import annotations

from typing import Any

import aiodocker


async def collect_image_stats() -> dict[str, Any]:
    """Collect Docker image and disk usage info."""
    docker = aiodocker.Docker()
    try:
        # Get system df info
        resp = await docker._query_json("system/df")
        images = resp.get("Images") or []
        total_image_size = sum(img.get("Size", 0) for img in images)
        image_count = len(images)

        build_cache = resp.get("BuildCache") or []
        total_cache_size = sum(bc.get("Size", 0) for bc in build_cache)

        volumes = resp.get("Volumes") or []
        total_volume_size = sum((v.get("UsageData") or {}).get("Size", 0) for v in volumes)

        containers = resp.get("Containers") or []
        total_container_size = sum(c.get("SizeRw", 0) for c in containers)

        return {
            "image_count": image_count,
            "image_size": total_image_size,
            "cache_size": total_cache_size,
            "volume_count": len(volumes),
            "volume_size": total_volume_size,
            "container_rw_size": total_container_size,
        }
    finally:
        await docker.close()
