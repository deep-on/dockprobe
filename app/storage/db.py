from __future__ import annotations

import json
import sqlite3
import time
from typing import Any

from app import config

_conn: sqlite3.Connection | None = None


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _init_tables(_conn)
    return _conn


def _init_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS container_stats (
            ts REAL NOT NULL,
            name TEXT NOT NULL,
            data TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_cs_name_ts ON container_stats(name, ts);

        CREATE TABLE IF NOT EXISTS host_stats (
            ts REAL NOT NULL,
            data TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_hs_ts ON host_stats(ts);

        CREATE TABLE IF NOT EXISTS alerts (
            ts REAL NOT NULL,
            type TEXT NOT NULL,
            target TEXT NOT NULL,
            value REAL,
            msg TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(ts);
    """)


def store_container_stats(stats: list[dict[str, Any]]) -> None:
    conn = get_conn()
    rows = [(s["ts"], s["name"], json.dumps(s)) for s in stats]
    conn.executemany("INSERT INTO container_stats (ts, name, data) VALUES (?, ?, ?)", rows)
    conn.commit()


def store_host_stats(stats: dict[str, Any]) -> None:
    conn = get_conn()
    conn.execute("INSERT INTO host_stats (ts, data) VALUES (?, ?)",
                 (stats["ts"], json.dumps(stats)))
    conn.commit()


def store_alert(alert: dict[str, Any]) -> None:
    conn = get_conn()
    conn.execute("INSERT INTO alerts (ts, type, target, value, msg) VALUES (?, ?, ?, ?, ?)",
                 (alert["ts"], alert["type"], alert["target"], alert.get("value"), alert.get("msg")))
    conn.commit()


def get_container_history(name: str, hours: float = 1) -> list[dict[str, Any]]:
    conn = get_conn()
    cutoff = time.time() - hours * 3600
    rows = conn.execute(
        "SELECT data FROM container_stats WHERE name = ? AND ts > ? ORDER BY ts",
        (name, cutoff),
    ).fetchall()
    return [json.loads(r["data"]) for r in rows]


def get_host_history(hours: float = 1) -> list[dict[str, Any]]:
    conn = get_conn()
    cutoff = time.time() - hours * 3600
    rows = conn.execute(
        "SELECT data FROM host_stats WHERE ts > ? ORDER BY ts",
        (cutoff,),
    ).fetchall()
    return [json.loads(r["data"]) for r in rows]


def get_alerts(hours: float = 24) -> list[dict[str, Any]]:
    conn = get_conn()
    cutoff = time.time() - hours * 3600
    rows = conn.execute(
        "SELECT ts, type, target, value, msg FROM alerts WHERE ts > ? ORDER BY ts DESC",
        (cutoff,),
    ).fetchall()
    return [dict(r) for r in rows]


def cleanup_old_data() -> int:
    """Delete data older than retention period. Returns deleted row count."""
    conn = get_conn()
    cutoff = time.time() - config.RETENTION_DAYS * 86400
    c1 = conn.execute("DELETE FROM container_stats WHERE ts < ?", (cutoff,)).rowcount
    c2 = conn.execute("DELETE FROM host_stats WHERE ts < ?", (cutoff,)).rowcount
    c3 = conn.execute("DELETE FROM alerts WHERE ts < ?", (cutoff,)).rowcount
    conn.commit()
    return c1 + c2 + c3
