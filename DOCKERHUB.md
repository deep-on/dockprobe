# DockProbe

**Lightweight Docker monitoring dashboard with anomaly detection & Telegram alerts.**

One container. One command. Full visibility.

[![GitHub](https://img.shields.io/badge/GitHub-deep--on%2Fdockprobe-blue)](https://github.com/deep-on/dockprobe)
[![License](https://img.shields.io/badge/license-Apache_2.0-blue)](https://github.com/deep-on/dockprobe/blob/main/LICENSE)

---

## Quick Start

```bash
# 1. Download compose file and env template
curl -fsSL https://raw.githubusercontent.com/deep-on/dockprobe/main/docker-compose.hub.yaml -o docker-compose.yaml
curl -fsSL https://raw.githubusercontent.com/deep-on/dockprobe/main/.env.example -o .env

# 2. Set your credentials
vi .env

# 3. (Optional) Generate self-signed SSL cert
mkdir -p certs && openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 825 -subj "/CN=dockprobe"

# 4. Start
docker compose up -d
```

Open `https://localhost:9090` and log in.

---

## Features

- **Real-time Dashboard** — Dark-themed web UI, 10s auto-refresh, interactive Chart.js charts
- **Container Monitoring** — CPU %, memory %, network I/O, block I/O, restart count
- **Host Monitoring** — CPU/GPU temperature & utilization, memory, disk, load average
- **Anomaly Detection** — 6 rules with recommended actions (CPU spike, memory overflow, high temp, disk full, restart loop, network surge)
- **Telegram Alerts** — Instant notification with 30-min cooldown
- **Security Scanner** — 16 automated checks every 5 minutes (container/host/network)
- **Chart Solo Mode** — Click any legend item to isolate a single container's line
- **Basic Auth + HTTPS** — PBKDF2-SHA256 hashing, CSRF protection, rate limiting
- **Non-root Container** — Runs as `appuser`, read-only mounts
- **Multi-arch** — `linux/amd64` and `linux/arm64`

---

## Configuration

All settings via `.env` file:

```env
# Required
AUTH_USER=admin
AUTH_PASS=your-strong-password

# Optional
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
CPU_THRESHOLD=80
MAX_CONNECTIONS=3
MONITOR_PORT=9090
TRUSTED_PROXIES=
```

---

## Volumes

| Mount | Purpose |
|-------|---------|
| `/var/run/docker.sock:/var/run/docker.sock:ro` | Docker API access (read-only) |
| `/sys:/host_sys:ro` | CPU/GPU temperature |
| `/proc:/host_proc:ro` | Load average, memory info |
| `/:/host_root:ro` | Disk usage (statvfs) |
| `monitor_data:/data` | SQLite DB, auth, settings |
| `./certs:/certs:ro` | SSL certificates (optional) |

---

## GPU Monitoring (NVIDIA)

For GPU temperature and utilization, use the GPU override:

```bash
docker compose -f docker-compose.yaml -f docker-compose.gpu.yaml up -d
```

---

## Update

```bash
docker compose pull && docker compose up -d
```

---

## Links

- **GitHub:** [deep-on/dockprobe](https://github.com/deep-on/dockprobe)
- **Issues:** [Report a bug or request a feature](https://github.com/deep-on/dockprobe/issues)
- **License:** Apache 2.0 — DeepOn branding must be retained in modified versions

---

Built by [DeepOn Inc.](https://deep-on.com)
