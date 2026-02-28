import os

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
AUTH_USER: str = os.getenv("AUTH_USER", "")
AUTH_PASS: str = os.getenv("AUTH_PASS", "")
DB_PATH: str = os.getenv("DB_PATH", "/data/monitor.db")
COLLECT_INTERVAL: int = int(os.getenv("COLLECT_INTERVAL", "10"))
RETENTION_DAYS: int = 7
ALERT_COOLDOWN_MINUTES: int = 30

# Anomaly thresholds
CPU_THRESHOLD: float = float(os.getenv("CPU_THRESHOLD", "80.0"))
CPU_CONSECUTIVE: int = 3
MEM_THRESHOLD: float = float(os.getenv("MEM_THRESHOLD", "90.0"))
HOST_TEMP_THRESHOLD: float = 85.0
DISK_THRESHOLD: float = 90.0
NET_SPIKE_MULTIPLIER: float = 10.0
NET_SPIKE_MIN_BYTES: int = 100 * 1024 * 1024  # 100MB
