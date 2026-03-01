# DockWatch Community Posts

Ready-to-post drafts for community promotion. Adjust tone and details as needed before posting.

---

## Reddit r/selfhosted

**Title:** I built a lightweight Docker monitoring dashboard — one command install, no external DB

**Body:**

Hey r/selfhosted,

I've been running a small homelab and got tired of setting up Prometheus + Grafana just to keep an eye on my containers. So I built **DockWatch** — a self-hosted Docker monitoring dashboard that's intentionally minimal.

**What it does:**
- Real-time container monitoring (CPU, memory, network, disk I/O)
- Host metrics (CPU/GPU temperature, disk usage, load average)
- Anomaly detection with 6 built-in rules (CPU spikes, memory overflow, high temp, etc.)
- Telegram alerts with 30-min cooldown per alert type
- Dark-themed web dashboard with Chart.js charts

**Why I think you'd like it:**
- **One-liner install:** `git clone && bash install.sh` — interactive installer handles auth, HTTPS, Telegram setup
- **No external dependencies:** No Prometheus, no InfluxDB, no Grafana. Just SQLite with 7-day auto-retention
- **4 Python packages total:** FastAPI, uvicorn, aiodocker, httpx. That's it
- **Single HTML file** for the entire dashboard — no build step, no npm, no webpack
- **Lightweight:** Runs in one container, minimal resource usage
- **Secure by default:** Basic Auth, rate limiting, HTTPS (self-signed or Cloudflare Tunnel), read-only Docker socket

**Access options:**
1. Self-signed SSL (local/LAN)
2. Cloudflare Tunnel (public access, no port forwarding)

It's MIT licensed and open source: https://github.com/deep-on/dockwatch

Happy to answer questions or take feature requests!

---

## Reddit r/docker

**Title:** DockWatch — a zero-config Docker monitoring dashboard (alternative to Prometheus+Grafana for simple setups)

**Body:**

I built a monitoring tool for people who want container visibility without the overhead of a full observability stack.

**The problem:** I just wanted to see which containers are eating CPU/memory and get alerted when something goes wrong. Setting up Prometheus + Grafana + alertmanager felt like deploying a second infrastructure just to monitor the first one.

**The solution — DockWatch:**
- Connects to Docker socket (read-only) and collects container stats every 10 seconds
- Shows everything in a single dark-themed web dashboard
- Built-in anomaly detection: CPU spikes (3 consecutive checks >80%), memory overflow (>90%), restart detection, network surges
- Telegram notifications when anomalies trigger
- SQLite storage with automatic 7-day retention (no database to manage)

**Technical highlights:**
- FastAPI + uvicorn async stack
- `aiodocker` for non-blocking Docker API calls
- Single HTML file with vanilla JS + Chart.js (no React, no build step)
- 4 Python dependencies. Zero JS build dependencies
- Basic Auth + rate limiting + HTTPS out of the box

```bash
git clone https://github.com/deep-on/dockwatch.git && cd dockwatch && bash install.sh
```

It's not trying to replace Grafana for complex setups — it's for the "I just want to see what's happening" use case.

GitHub: https://github.com/deep-on/dockwatch

---

## Hacker News — Show HN

**Title:** Show HN: DockWatch – Lightweight Docker monitoring with anomaly detection (4 dependencies)

**Body:**

I built DockWatch, a self-hosted Docker monitoring dashboard focused on simplicity.

Design decisions that shaped the project:

1. **Single HTML file** — The entire dashboard is one HTML file with inline CSS and vanilla JS. No build step, no framework, no npm. Chart.js is the only frontend dependency (loaded via CDN).

2. **4 Python packages** — FastAPI, uvicorn, aiodocker, httpx. That's the entire backend. SQLite (stdlib) handles storage with WAL mode for concurrent reads during writes.

3. **Async everything** — aiodocker provides non-blocking Docker API access. The collector runs on a 10-second interval, persists to SQLite, and triggers anomaly detection in the same event loop.

4. **State machine anomaly detection** — CPU alerts require 3 consecutive readings above threshold (30 seconds) to avoid false positives from brief spikes. Other rules (memory, temperature, disk, restarts, network) trigger immediately.

5. **Zero configuration monitoring** — Connects to Docker socket, discovers all containers automatically. No per-container config, no labels, no service discovery setup.

6. **Built-in security** — Basic Auth with bcrypt, per-IP rate limiting (5 fails = 60s lockout), HTTPS via self-signed cert or Cloudflare Tunnel. Connection limit prevents session exhaustion.

The trade-off is clear: this doesn't scale to hundreds of hosts or provide PromQL-style queries. It's for the single-host or small-cluster use case where you want visibility in 60 seconds.

Install: `git clone https://github.com/deep-on/dockwatch.git && cd dockwatch && bash install.sh`

GitHub: https://github.com/deep-on/dockwatch
