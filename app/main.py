from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import base64
import secrets
from collections import defaultdict

from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from app import config
from app.alerting.detector import AnomalyDetector
from app.alerting.telegram import send_alert
from app.collectors.containers import collect_container_stats
from app.collectors.host import collect_host_stats
from app.collectors.images import collect_image_stats
from app.storage.db import (
    cleanup_old_data,
    get_alerts,
    get_container_history,
    get_host_history,
    store_alert,
    store_container_stats,
    store_host_stats,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("monitor")

# Shared state
_latest: dict[str, Any] = {}
_detector = AnomalyDetector()
_collect_task: asyncio.Task | None = None


async def _collection_loop() -> None:
    """Background loop: collect stats, detect anomalies, send alerts."""
    cycle = 0
    while True:
        try:
            # Collect
            containers = await collect_container_stats()
            host = collect_host_stats()

            # Store to SQLite
            if containers:
                store_container_stats(containers)
            store_host_stats(host)

            # Collect images less frequently (every 6th cycle ~ 1 min)
            images: dict[str, Any] = _latest.get("images", {})
            if cycle % 6 == 0:
                try:
                    images = await collect_image_stats()
                except Exception as e:
                    logger.warning("Image stats collection failed: %s", e)

            # Detect anomalies
            alerts = _detector.check(containers, host)
            for a in alerts:
                store_alert(a)
                await send_alert(a)

            # Update shared state
            _latest.update({
                "containers": containers,
                "host": host,
                "images": images,
                "anomalies": _detector.active_anomalies,
                "ts": time.time(),
            })

            # Cleanup old data daily (every ~8640 cycles at 10s interval)
            if cycle % 8640 == 0 and cycle > 0:
                deleted = cleanup_old_data()
                if deleted:
                    logger.info("Cleaned up %d old records", deleted)

            cycle += 1
        except Exception:
            logger.exception("Collection cycle error")

        await asyncio.sleep(config.COLLECT_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _collect_task
    logger.info("Starting collection loop (interval=%ds)", config.COLLECT_INTERVAL)
    _collect_task = asyncio.create_task(_collection_loop())
    yield
    _collect_task.cancel()
    try:
        await _collect_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Docker Monitor", lifespan=lifespan)

STATIC_DIR = Path(__file__).parent / "static"


# Rate limiting: {ip: [fail_timestamp, ...]}
_fail_log: dict[str, list[float]] = defaultdict(list)
RATE_MAX_FAILS = 5
RATE_WINDOW = 60  # seconds


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _is_rate_limited(ip: str) -> bool:
    now = time.time()
    # Purge old entries
    _fail_log[ip] = [t for t in _fail_log[ip] if now - t < RATE_WINDOW]
    return len(_fail_log[ip]) >= RATE_MAX_FAILS


def _record_fail(ip: str) -> None:
    _fail_log[ip].append(time.time())


def _check_auth(request: Request) -> Response | None:
    """Validate Basic Auth with rate limiting."""
    if not config.AUTH_USER or not config.AUTH_PASS:
        return None

    ip = _get_client_ip(request)

    if _is_rate_limited(ip):
        logger.warning("Rate limited: %s", ip)
        return Response(status_code=429, content="Too Many Requests. Try again later.")

    auth = request.headers.get("Authorization", "")
    if auth.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth[6:]).decode()
            user, pw = decoded.split(":", 1)
            if secrets.compare_digest(user, config.AUTH_USER) and secrets.compare_digest(pw, config.AUTH_PASS):
                return None
        except Exception:
            pass

    _record_fail(ip)
    remaining = RATE_MAX_FAILS - len(_fail_log[ip])
    logger.warning("Auth failed from %s (%d attempts left)", ip, max(remaining, 0))
    return Response(
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="Docker Monitor"'},
        content="Unauthorized",
    )


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path == "/api/health":
        return await call_next(request)
    resp = _check_auth(request)
    if resp is not None:
        return resp
    return await call_next(request)


@app.get("/")
async def dashboard():
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


@app.get("/api/current")
async def api_current():
    return JSONResponse(_latest or {"containers": [], "host": {}, "images": {}, "anomalies": []})


@app.get("/api/history/{name}")
async def api_container_history(name: str, hours: float = Query(1, ge=0.1, le=168)):
    data = get_container_history(name, hours)
    return JSONResponse(data)


@app.get("/api/history/host")
async def api_host_history(hours: float = Query(1, ge=0.1, le=168)):
    data = get_host_history(hours)
    return JSONResponse(data)


@app.get("/api/alerts")
async def api_alerts(hours: float = Query(24, ge=1, le=168)):
    data = get_alerts(hours)
    return JSONResponse(data)


@app.get("/api/health")
async def api_health():
    return {"status": "ok", "uptime_cycles": _latest.get("ts", 0)}
