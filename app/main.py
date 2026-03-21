from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import base64
import hashlib
import json
import os
import secrets
from collections import defaultdict

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response

from app import config
from app.alerting.detector import AnomalyDetector
from app.alerting.telegram import send_alert
from app.collectors.containers import collect_container_stats
from app.collectors.host import collect_host_stats
from app.collectors.images import collect_image_stats
from app.security.scanner import scan as security_scan
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

            # Security scan every 30th cycle (~5 min)
            security: dict[str, Any] = _latest.get("security", {})
            if cycle % 30 == 0:
                try:
                    import aiodocker as _aio
                    docker = _aio.Docker()
                    try:
                        scan_warnings = await security_scan(docker)
                        summary = {"critical": 0, "warning": 0, "info": 0, "unavailable": 0, "total": len(scan_warnings)}
                        for w in scan_warnings:
                            summary[w["severity"]] = summary.get(w["severity"], 0) + 1
                        security = {"warnings": scan_warnings, "summary": summary, "last_scan_ts": time.time()}
                    finally:
                        await docker.close()
                except Exception as e:
                    logger.warning("Security scan failed: %s", e)

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
                "security": security,
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


VERSION = (Path(__file__).resolve().parent.parent / "VERSION").read_text().strip()

app = FastAPI(
    title="DockProbe", version=VERSION, lifespan=lifespan,
    docs_url=None, redoc_url=None, openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],  # no cross-origin access
    allow_methods=["GET", "POST"],
    allow_headers=[],
)

STATIC_DIR = Path(__file__).parent / "static"


# ── Auth credentials (file-based, falls back to env) ──

AUTH_FILE = Path(config.DB_PATH).parent / "auth.json"
SETTINGS_FILE = Path(config.DB_PATH).parent / "settings.json"


def _load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_settings(data: dict) -> None:
    current = _load_settings()
    current.update(data)
    SETTINGS_FILE.write_text(json.dumps(current))


def _get_max_connections() -> int:
    s = _load_settings()
    return s.get("max_connections", config.MAX_CONNECTIONS)


def _hash_pw(pw: str, salt: str | None = None) -> str:
    """Hash password with PBKDF2-SHA256 + random salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), iterations=600_000)
    return f"{salt}${dk.hex()}"


def _verify_pw(pw: str, stored: str) -> bool:
    """Verify password against stored hash. Supports legacy SHA-256 and PBKDF2."""
    if "$" in stored:
        salt, _ = stored.split("$", 1)
        return secrets.compare_digest(_hash_pw(pw, salt), stored)
    # Legacy: unsalted SHA-256 (auto-migrated on next password change)
    return secrets.compare_digest(hashlib.sha256(pw.encode()).hexdigest(), stored)


def _load_auth() -> tuple[str, str]:
    """Load credentials: auth.json first, then env vars."""
    if AUTH_FILE.exists():
        try:
            data = json.loads(AUTH_FILE.read_text())
            return data["user"], data["hash"]
        except Exception:
            pass
    if config.AUTH_USER and config.AUTH_PASS:
        return config.AUTH_USER, _hash_pw(config.AUTH_PASS)
    return "", ""


def _save_auth(user: str, pw: str) -> None:
    AUTH_FILE.write_text(json.dumps({"user": user, "hash": _hash_pw(pw)}))


# ── Active sessions: {ip: last_seen_timestamp} ──

_active_sessions: dict[str, float] = {}
SESSION_TIMEOUT = 60  # consider inactive after 60s


def _touch_session(ip: str) -> None:
    _active_sessions[ip] = time.time()


def _get_active_count() -> int:
    now = time.time()
    return sum(1 for t in _active_sessions.values() if now - t < SESSION_TIMEOUT)


def _get_active_ips() -> list[str]:
    now = time.time()
    return [ip for ip, t in _active_sessions.items() if now - t < SESSION_TIMEOUT]


def _is_connection_allowed(ip: str) -> bool:
    max_conn = _get_max_connections()
    if max_conn <= 0:
        return True
    # Already active — always allowed
    now = time.time()
    if ip in _active_sessions and now - _active_sessions[ip] < SESSION_TIMEOUT:
        return True
    return _get_active_count() < max_conn


# ── Rate limiting ──

_fail_log: dict[str, list[float]] = defaultdict(list)
RATE_MAX_FAILS = 5
RATE_WINDOW = 60


TRUSTED_PROXIES = os.environ.get("TRUSTED_PROXIES", "").split(",")


def _get_client_ip(request: Request) -> str:
    """Get client IP. Only trust X-Forwarded-For from trusted proxy IPs."""
    real_ip = request.client.host if request.client else "unknown"
    if real_ip in TRUSTED_PROXIES:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return real_ip


def _is_rate_limited(ip: str) -> bool:
    now = time.time()
    _fail_log[ip] = [t for t in _fail_log[ip] if now - t < RATE_WINDOW]
    return len(_fail_log[ip]) >= RATE_MAX_FAILS


def _record_fail(ip: str) -> None:
    _fail_log[ip].append(time.time())


def _check_auth(request: Request) -> Response | None:
    """Validate Basic Auth with rate limiting."""
    auth_user, auth_hash = _load_auth()
    if not auth_user or not auth_hash:
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
            if secrets.compare_digest(user, auth_user) and _verify_pw(pw, auth_hash):
                return None
        except Exception:
            pass

    _record_fail(ip)
    remaining = RATE_MAX_FAILS - len(_fail_log[ip])
    logger.warning("Auth failed from %s (%d attempts left)", ip, max(remaining, 0))
    # Return HTML body so mobile browsers redirect properly after Basic Auth
    return Response(
        status_code=401,
        headers={
            "WWW-Authenticate": 'Basic realm="Docker Monitor"',
            "Content-Type": "text/html; charset=utf-8",
        },
        content='<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0;url=/"></head>'
                '<body><p>Unauthorized. <a href="/">Login</a></p></body></html>',
    )


def _get_current_user(request: Request) -> str | None:
    """Extract username from valid Basic Auth header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth[6:]).decode()
            return decoded.split(":", 1)[0]
        except Exception:
            pass
    return None


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path == "/api/health":
        return await call_next(request)
    resp = _check_auth(request)
    if resp is not None:
        return resp
    # CSRF protection: POST requests must include X-Requested-With header
    if request.method == "POST":
        if not request.headers.get("X-Requested-With"):
            return JSONResponse({"ok": False, "error": "Missing X-Requested-With header"}, status_code=403)
    # Connection limit check (after auth passes)
    ip = _get_client_ip(request)
    if not _is_connection_allowed(ip):
        logger.warning("Max connections reached, rejected: %s", ip)
        return Response(status_code=503, content="Max connections reached. Try again later.")
    _touch_session(ip)
    return await call_next(request)


@app.get("/")
async def dashboard():
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


@app.get("/static/{filename}")
async def static_file(filename: str):
    path = (STATIC_DIR / filename).resolve()
    if not path.is_relative_to(STATIC_DIR.resolve()):
        return Response(status_code=403)
    if path.exists() and path.is_file():
        return FileResponse(path)
    return Response(status_code=404)


@app.get("/api/current")
async def api_current():
    return JSONResponse(_latest or {"containers": [], "host": {}, "images": {}, "anomalies": [], "security": {}})


@app.get("/api/security")
async def api_security():
    security = _latest.get("security", {})
    if not security:
        return JSONResponse({"warnings": [], "summary": {"critical": 0, "warning": 0, "info": 0, "unavailable": 0, "total": 0}, "last_scan_ts": None})
    return JSONResponse(security)


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


@app.post("/api/change-password")
async def api_change_password(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)

    current_pw = body.get("current_password", "")
    new_user = body.get("new_username", "").strip()
    new_pw = body.get("new_password", "")

    if not new_pw or len(new_pw) < 8:
        return JSONResponse({"ok": False, "error": "New password must be at least 8 characters"}, status_code=400)

    auth_user, auth_hash = _load_auth()
    if auth_user and auth_hash:
        if not _verify_pw(current_pw, auth_hash):
            return JSONResponse({"ok": False, "error": "Current password is incorrect"}, status_code=403)

    username = new_user if new_user else (auth_user or "admin")
    _save_auth(username, new_pw)
    logger.info("Password changed for user: %s", username)
    return JSONResponse({"ok": True, "message": "Password changed. Please re-login."})


@app.get("/api/session")
async def api_session(request: Request):
    ip = _get_client_ip(request)
    user = _get_current_user(request) or "anonymous"
    ua = request.headers.get("User-Agent", "")
    active_ips = _get_active_ips()
    return JSONResponse({
        "user": user,
        "ip": ip,
        "user_agent": ua,
        "active_connections": len(active_ips),
        "max_connections": _get_max_connections(),
        "active_ips": active_ips,
    })


def _get_refresh_interval() -> int:
    s = _load_settings()
    return s.get("refresh_interval", 10)


@app.get("/api/settings")
async def api_get_settings():
    return JSONResponse({
        "max_connections": _get_max_connections(),
        "refresh_interval": _get_refresh_interval(),
    })


@app.post("/api/settings")
async def api_update_settings(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)

    updated = {}
    if "max_connections" in body:
        try:
            val = int(body["max_connections"])
            if val < 0 or val > 100:
                return JSONResponse({"ok": False, "error": "max_connections must be 0-100 (0=unlimited)"}, status_code=400)
            updated["max_connections"] = val
        except (ValueError, TypeError):
            return JSONResponse({"ok": False, "error": "max_connections must be a number"}, status_code=400)

    if "refresh_interval" in body:
        try:
            val = int(body["refresh_interval"])
            if val < 5 or val > 60:
                return JSONResponse({"ok": False, "error": "refresh_interval must be 5-60 seconds"}, status_code=400)
            updated["refresh_interval"] = val
        except (ValueError, TypeError):
            return JSONResponse({"ok": False, "error": "refresh_interval must be a number"}, status_code=400)

    if not updated:
        return JSONResponse({"ok": False, "error": "No valid settings provided"}, status_code=400)

    _save_settings(updated)
    logger.info("Settings updated: %s", updated)
    return JSONResponse({"ok": True, "settings": updated})


# ── GitHub repo stats (cached 10 min) ──
_gh_cache: dict[str, Any] = {"data": None, "ts": 0}
GH_REPO = "deep-on/dockprobe"
GH_CACHE_TTL = 600


@app.get("/api/github-stats")
async def api_github_stats():
    import httpx as _httpx

    now = time.time()
    if _gh_cache["data"] and now - _gh_cache["ts"] < GH_CACHE_TTL:
        return JSONResponse(_gh_cache["data"])
    try:
        async with _httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"https://api.github.com/repos/{GH_REPO}")
            if resp.status_code == 200:
                d = resp.json()
                data = {
                    "stars": d.get("stargazers_count", 0),
                    "forks": d.get("forks_count", 0),
                    "watchers": d.get("subscribers_count", 0),
                    "open_issues": d.get("open_issues_count", 0),
                    "repo": GH_REPO,
                    "url": d.get("html_url", ""),
                }
                _gh_cache["data"] = data
                _gh_cache["ts"] = now
                return JSONResponse(data)
    except Exception as e:
        logger.warning("GitHub stats fetch failed: %s", e)
    return JSONResponse(_gh_cache["data"] or {"stars": 0, "forks": 0, "watchers": 0, "open_issues": 0, "repo": GH_REPO, "url": ""})


@app.get("/api/health")
async def api_health():
    return {"status": "ok", "version": VERSION, "uptime_cycles": _latest.get("ts", 0)}
