<p align="center">
  <img src="app/static/logo.png" width="80" alt="DockWatch">
</p>

<h1 align="center">DockWatch</h1>

<p align="center">
  <b>Lightweight Docker monitoring dashboard with anomaly detection & Telegram alerts.</b><br>
  One container. One command. Full visibility.
</p>

<p align="center">
  <b>English</b> | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | <a href="README.de.md">Deutsch</a> | <a href="README.fr.md">Français</a> | <a href="README.es.md">Español</a> | <a href="README.pt.md">Português</a> | <a href="README.it.md">Italiano</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.12-green" alt="Python">
  <img src="https://img.shields.io/badge/docker-compose-blue" alt="Docker">
  <img src="https://img.shields.io/badge/dependencies-4_only-brightgreen" alt="Deps">
</p>

---

## Quick Start

```bash
git clone https://github.com/deep-on/dockwatch.git && cd dockwatch && bash install.sh
```

That's it. The interactive installer sets up authentication, Telegram alerts, and HTTPS — then opens `https://localhost:9090`.

> **Requirements:** Docker (with Compose v2), Git, OpenSSL

---

## Dashboard Preview

<p align="center">
  <img src="docs/screenshots/dashboard-full.png" alt="DockWatch Dashboard" width="800">
</p>

---

## Features

| Category | What you get |
|----------|-------------|
| **Real-time Dashboard** | Dark-themed web UI, 10s auto-refresh, sortable tables, Chart.js charts |
| **Container Monitoring** | CPU %, memory %, network I/O, block I/O, restart count |
| **Host Monitoring** | CPU/GPU temperature, disk usage, load average |
| **Anomaly Detection** | 6 rules — CPU spike, memory overflow, high temp, disk full, restart, network spike |
| **Telegram Alerts** | Instant notification with 30-min cooldown per alert type |
| **Security** | Basic Auth, rate limiting (5 fails = 60s lockout), HTTPS |
| **Session Management** | Active connection tracking, configurable max connections, live IP display |
| **Password Management** | Change username/password via dashboard UI |
| **Settings UI** | Adjust max connections at runtime from the dashboard |
| **Access Modes** | Self-signed SSL (default) or Cloudflare Tunnel (no port-forwarding) |
| **Lightweight** | 4 Python packages, single HTML file, SQLite with 7-day retention |

---

## Dashboard

| Section | Details |
|---------|---------|
| Session Bar | Logged-in user, IP, active connections / max limit |
| Host Cards | CPU temp, GPU temp, disk %, load average |
| Container Table | Sortable by CPU/memory/network, color-coded anomalies |
| Charts (4) | Container CPU & memory trends, host temperature & load |
| Docker Disk | Images, build cache, volumes, container RW layers |
| Alert History | Last 24h with timestamps |

---

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

---

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
│  │   └── db.py          (SQLite WAL)    │
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

---

## Configuration

All settings via `.env` file:

```env
# Authentication (required)
AUTH_USER=admin
AUTH_PASS=your-password

# Telegram alerts (optional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Thresholds (optional, shown with defaults)
CPU_THRESHOLD=80
MEM_THRESHOLD=90

# Connection limit (optional, 0 = unlimited)
MAX_CONNECTIONS=3

# Cloudflare Tunnel (optional)
CF_TUNNEL_TOKEN=your-tunnel-token
```

---

## Access Modes

### Option 1: Local (self-signed SSL) — default

```bash
bash install.sh   # choose option 1
```

Access via `https://localhost:9090` or `https://<your-ip>:9090`

### Option 2: Cloudflare Tunnel (no port-forwarding needed)

```bash
bash install.sh   # choose option 2, paste tunnel token
```

Public HTTPS via your Cloudflare tunnel domain — no router config required.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard HTML |
| `/api/current` | GET | Latest snapshot (containers + host + images + anomalies) |
| `/api/history/{name}?hours=1` | GET | Container time-series |
| `/api/history/host?hours=1` | GET | Host time-series |
| `/api/alerts?hours=24` | GET | Alert history |
| `/api/session` | GET | Current user, IP, active connections |
| `/api/settings` | GET/POST | Runtime settings (max_connections) |
| `/api/change-password` | POST | Change username/password |
| `/api/health` | GET | Health check (no auth required) |

---

## Security

- **Basic Auth** on all endpoints (except `/api/health`)
- **Rate limiting** — 5 failed login attempts → 60s lockout per IP
- **HTTPS** — Self-signed or Cloudflare Tunnel
- **Connection limit** — Configurable max simultaneous users
- **Read-only mounts** — Docker socket, /sys, /proc all mounted read-only
- **No write access** — Monitoring-only, no container control

---

## Manual Setup

If you prefer manual configuration over the install script:

```bash
git clone https://github.com/deep-on/dockwatch.git
cd dockwatch

# Create .env
cp .env.example .env
vi .env

# Generate SSL cert (optional)
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -subj "/CN=dockwatch"

# Start
docker compose up -d --build
```

---

## License

MIT License — see [LICENSE](LICENSE)

**Attribution:** Modified or redistributed versions must retain the DeepOn logo and "Powered by DeepOn Inc." notice in the UI.

---

<p align="center">
  <img src="app/static/logo.png" width="24" alt="DeepOn">
  Built by <a href="https://deep-on.com">DeepOn Inc.</a>
</p>
