# 🐳 DockWatch

🌐 [한국어](README.ko.md) | **English**

**Lightweight Docker container monitoring dashboard with anomaly detection & Telegram alerts.**

One container. One command. Full visibility.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.12-green)
![Docker](https://img.shields.io/badge/docker-compose-blue)

---

## Features

- **Real-time dashboard** — Dark-themed web UI with auto-refresh (10s)
- **Container monitoring** — CPU, memory, network I/O, block I/O, restart count
- **Host monitoring** — CPU/GPU temperature, disk usage, load average
- **Anomaly detection** — Configurable rules with state machine (CPU spike, memory overflow, disk full, network spike, container restart)
- **Telegram alerts** — Instant notifications with 30-min cooldown per alert type
- **Rate-limited auth** — Basic Auth + brute-force protection (5 attempts / 60s lockout)
- **HTTPS** — Self-signed SSL or Cloudflare Tunnel (zero port-forwarding)
- **SQLite time-series** — 7-day retention, lightweight, no external DB needed
- **One-liner install** — Interactive setup script, works in seconds

## Quick Start

```bash
git clone https://github.com/deep-on/dockwatch.git
cd dockwatch
bash install.sh
```

That's it. Open `https://localhost:9090` in your browser.

## Dashboard

| Section | Details |
|---------|---------|
| Host Cards | CPU temp, GPU temp, disk %, load average |
| Container Table | Sortable by CPU/memory/network, color-coded anomalies |
| Charts | Container CPU & memory trends, host temperature & load (Chart.js) |
| Docker Disk | Images, build cache, volumes, container RW layers |
| Alert History | Last 24h with timestamps |

## Anomaly Detection Rules

| Rule | Condition | Action |
|------|-----------|--------|
| Container CPU | >80% for 3 consecutive checks (30s) | Telegram + red highlight |
| Container Memory | >90% of limit | Immediate alert |
| Host CPU Temp | >85°C | Immediate alert |
| Host Disk | >90% usage | Immediate alert |
| Container Restart | restart_count increased | Immediate alert |
| Network Spike | RX 10x surge + >100MB | Immediate alert |

All thresholds are configurable via environment variables.

## Architecture

```
┌─────────────────────────────────────────┐
│  DockWatch Container                    │
│                                         │
│  FastAPI + uvicorn (port 9090)          │
│  ├── collectors/                        │
│  │   ├── containers.py  (aiodocker)     │
│  │   ├── host.py        (/proc, /sys)   │
│  │   └── images.py      (system df)     │
│  ├── alerting/                          │
│  │   ├── detector.py    (state machine) │
│  │   └── telegram.py    (httpx)         │
│  ├── storage/                           │
│  │   └── db.py          (SQLite)        │
│  └── static/                            │
│      └── index.html     (Chart.js)      │
│                                         │
│  Volumes:                               │
│    docker.sock (ro), /sys (ro),         │
│    /proc (ro), SQLite named volume      │
└─────────────────────────────────────────┘
```

**Dependencies (4 packages only):**
- `fastapi` — Web framework
- `uvicorn` — ASGI server
- `aiodocker` — Async Docker API client
- `httpx` — Async HTTP client (Telegram API)

## Configuration

All settings via `.env` file:

```env
# Authentication
AUTH_USER=admin
AUTH_PASS=your-password

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Thresholds (optional)
CPU_THRESHOLD=80
MEM_THRESHOLD=90

# Cloudflare Tunnel (optional)
CF_TUNNEL_TOKEN=your-tunnel-token
```

## Access Modes

### Local (self-signed SSL)
```bash
# Default mode — generates self-signed cert automatically
bash install.sh  # choose option 1
```
Access via `https://localhost:9090` or `https://<your-ip>:9090`

### Cloudflare Tunnel (no port-forwarding needed)
```bash
# Public HTTPS via Cloudflare — no router config required
bash install.sh  # choose option 2, paste tunnel token
```
Access via your Cloudflare tunnel domain with real HTTPS certificate.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard HTML |
| `GET /api/current` | Latest snapshot (containers + host + images + anomalies) |
| `GET /api/history/{name}?hours=1` | Container time-series |
| `GET /api/history/host?hours=1` | Host time-series |
| `GET /api/alerts?hours=24` | Alert history |
| `GET /api/health` | Health check (no auth required) |

## Security

- **Basic Auth** on all endpoints (except `/api/health`)
- **Rate limiting** — 5 failed login attempts → 60s lockout per IP
- **HTTPS** — Self-signed or Cloudflare Tunnel
- **Read-only mounts** — Docker socket, /sys, /proc all mounted read-only
- **No write access** — Dashboard is monitoring-only, no container control

## Manual Setup

If you prefer manual configuration over the install script:

```bash
git clone https://github.com/deep-on/dockwatch.git
cd dockwatch

# Create .env
cp .env.example .env
vi .env

# Generate SSL cert
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -subj "/CN=dockwatch"

# Start
docker compose up -d --build
```

## License

MIT License — see [LICENSE](LICENSE)

---

Built with 🔧 by [DeepOn Inc.](https://github.com/deep-on)
