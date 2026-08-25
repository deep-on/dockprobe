import os

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
AUTH_USER: str = os.getenv("AUTH_USER", "")
AUTH_PASS: str = os.getenv("AUTH_PASS", "")
MAX_CONNECTIONS: int = int(os.getenv("MAX_CONNECTIONS", "10"))
DB_PATH: str = os.getenv("DB_PATH", "/data/monitor.db")
COLLECT_INTERVAL: int = int(os.getenv("COLLECT_INTERVAL", "10"))
RETENTION_DAYS: int = 7
ALERT_COOLDOWN_MINUTES: int = 30

# Anomaly thresholds


def _default_cpu_threshold() -> float:
    """80% of the machine — not 80% of one core.

    Docker reports container CPU as a percentage where 100% is a single core, so
    a fixed 80 means "four fifths of one core". On a 32-core host that is two and
    a half percent of the machine: every ordinary worker sits above it forever,
    the alert never clears, and the one that matters arrives in a stream of
    hundreds that nobody reads any more.

    Scaling with the core count keeps the number meaning the same thing
    everywhere. Set CPU_THRESHOLD explicitly to override it.
    """
    return 80.0 * (os.cpu_count() or 1)


# An empty value counts as unset: compose passes the variable through whether or
# not anyone filled it in.
CPU_THRESHOLD: float = float(os.getenv("CPU_THRESHOLD") or _default_cpu_threshold())
CPU_CONSECUTIVE: int = 3
MEM_THRESHOLD: float = float(os.getenv("MEM_THRESHOLD", "90.0"))
HOST_TEMP_THRESHOLD: float = 85.0
DISK_THRESHOLD: float = 90.0
NET_SPIKE_MULTIPLIER: float = 10.0
NET_SPIKE_MIN_BYTES: int = 100 * 1024 * 1024  # 100MB
