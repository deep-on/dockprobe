# DockProbe Promotion Posts

Copy-paste ready posts for each platform. Adjust links and screenshots before posting.

GitHub: https://github.com/deep-on/dockprobe
Screenshot: https://raw.githubusercontent.com/deep-on/dockprobe/main/docs/screenshots/dashboard-full.png

---

## Day 1: r/selfhosted

**Title:** I built a lightweight Docker monitoring dashboard — single container, zero config, Telegram alerts

**Body:**

Hey r/selfhosted,

I got tired of setting up Prometheus + Grafana just to check if my containers are healthy. So I built **DockProbe** — a monitoring dashboard that runs as a single Docker container.

**What it does:**

- Real-time dashboard — CPU, memory, network, block I/O for every container + host temps, disk, load average
- 6 anomaly detection rules — CPU spike (3 consecutive checks), memory overflow, high temp, disk full, restart loop, network surge
- Telegram alerts with 30-min cooldown per alert type
- Dark-themed web UI with Chart.js charts, sortable tables
- Basic Auth + self-signed HTTPS out of the box
- Cloudflare Tunnel support for remote access without port-forwarding

**What it is NOT:**

- Not a container manager — read-only monitoring, no start/stop/restart
- Not a Prometheus replacement — no custom metrics, no PromQL
- No external database — SQLite with 7-day retention, ~50MB memory

**Tech stack:** FastAPI + aiodocker + Chart.js + httpx. Only 4 Python packages. Single HTML file for the entire dashboard.

**Install:**

```bash
git clone https://github.com/deep-on/dockprobe.git && cd dockprobe && bash install.sh
```

The interactive installer sets up auth, Telegram alerts, and HTTPS in under a minute.

[Screenshot](https://raw.githubusercontent.com/deep-on/dockprobe/main/docs/screenshots/dashboard-full.png)

GitHub: https://github.com/deep-on/dockprobe

This is my first open-source project. Would love to hear what features you'd want next — or what I'm doing wrong. Thanks!

---

## Day 2: Dev.to Blog Post

**Title:** How I Built a Docker Monitoring Dashboard in a Single Container

**Tags:** docker, python, opensource, monitoring

**Body:**

### The Problem

I run about 10 Docker containers on a home server. Nothing crazy — nginx, postgres, redis, a few web apps. I wanted a simple way to check if everything was healthy.

The obvious answer was Prometheus + Grafana. But for my use case, it felt like bringing a firetruck to blow out a candle:

- Prometheus: separate container, config files, scrape targets, retention policies
- Grafana: another container, dashboards to build, data sources to configure
- Node Exporter: yet another container for host metrics
- cAdvisor: and another one for container metrics

That's 4 extra containers just to monitor 10 containers. Something felt wrong.

### The Idea

What if monitoring was just... one container? Mount the Docker socket, open a browser, done.

That's what I built. It's called **DockProbe**.

![DockProbe Dashboard](https://raw.githubusercontent.com/deep-on/dockprobe/main/docs/screenshots/dashboard-full.png)

### Architecture Decisions

**Why FastAPI?**

I needed async because Docker stats streaming is inherently async. FastAPI with uvicorn gave me:
- Async Docker API calls via aiodocker
- Built-in OpenAPI docs (useful during development)
- Single-process, low memory footprint

**Why SQLite?**

For a monitoring tool with 7-day retention, SQLite in WAL mode is perfect:
- No separate database container
- Handles the write pattern well (one insert every 10 seconds)
- Named volume for persistence across container restarts

**Why a Single HTML File?**

Zero build step. No npm, no webpack, no node_modules. The entire dashboard is one HTML file with inline CSS and JavaScript. Chart.js is loaded from CDN.

This means:
- `docker compose up -d` and you're done
- No frontend build pipeline to maintain
- Easy to customize — it's just one file

### Anomaly Detection

Instead of just showing numbers, DockProbe watches for problems. Six rules run on every collection cycle (10 seconds):

```python
# CPU: must be high for 3 consecutive checks (30 seconds)
# This avoids false alarms from brief spikes
if cpu_pct > CPU_THRESHOLD:
    cpu_counts[container] += 1
    if cpu_counts[container] >= 3:
        trigger_alert("cpu_high", container, cpu_pct)
else:
    cpu_counts[container] = 0
```

Each alert type has a 30-minute cooldown per target, so you won't get spammed if a container is consistently misbehaving.

Alerts go to Telegram via a simple httpx POST — no email server, no Slack webhook setup.

### The Result

- **4 Python packages:** fastapi, uvicorn, aiodocker, httpx
- **~50MB memory** usage
- **10-second** collection interval
- **7-day** data retention
- **One command** to install

```bash
git clone https://github.com/deep-on/dockprobe.git && cd dockprobe && bash install.sh
```

### What I Learned

1. **aiodocker's stats API** returns different formats depending on `stream=True` vs `stream=False`. Cost me hours of debugging.
2. **Self-signed HTTPS** is important even for local tools — browsers increasingly block HTTP features.
3. **Single-file dashboards** are underrated. No build step means no build breakage.

### What's Next

I'm considering:
- Container log viewer
- Custom alert thresholds per container
- Multi-host support
- Webhook integrations beyond Telegram

**GitHub:** https://github.com/deep-on/dockprobe

If you're running Docker containers and want simple monitoring without the Prometheus/Grafana overhead, give it a try. Feedback and stars are very welcome.

---

## Day 3: r/homelab

**Title:** DockProbe — dead simple Docker monitoring for your homelab (single container, Telegram alerts, zero config)

**Body:**

Hey homelabbers,

I built a Docker monitoring tool specifically for the homelab use case — where you don't need enterprise-grade observability, just a quick way to see if your containers are behaving.

**DockProbe** is a single container that gives you:

- Real-time dashboard with CPU, memory, network stats for every container
- Host monitoring — CPU/GPU temperature, disk usage, load average
- Anomaly detection — alerts you via Telegram when something goes wrong (CPU spike, memory overflow, disk full, high temp, restart loop, network surge)
- Dark-themed UI with historical charts
- HTTPS + Basic Auth by default
- Cloudflare Tunnel support for checking your lab remotely

**The homelab pitch:** It uses ~50MB of RAM, has zero dependencies beyond Docker, stores everything in SQLite (auto-cleans after 7 days), and installs with one command.

```bash
git clone https://github.com/deep-on/dockprobe.git && cd dockprobe && bash install.sh
```

[Dashboard screenshot](https://raw.githubusercontent.com/deep-on/dockprobe/main/docs/screenshots/dashboard-full.png)

GitHub: https://github.com/deep-on/dockprobe

Currently monitoring 10+ containers on my own homelab server. Would love to hear what you'd want added. Thanks!

---

## Day 4: Hacker News (Show HN)

**Title:** Show HN: DockProbe – Lightweight Docker monitoring with anomaly detection and Telegram alerts

**URL:** https://github.com/deep-on/dockprobe

**First Comment:**

I built this because existing monitoring solutions (Prometheus+Grafana, Portainer) felt like overkill for simply watching a few Docker containers.

DockProbe is a single container that provides:

- Real-time dashboard (CPU, memory, network, disk, temperature)
- 6 anomaly detection rules with Telegram alerts
- Self-signed HTTPS or Cloudflare Tunnel for remote access
- Single HTML file dashboard — no build step

Stack: FastAPI, aiodocker, Chart.js, SQLite. 4 Python dependencies total. ~50MB memory.

Design philosophy: do one thing well. Monitor containers, detect anomalies, send alerts. No container management, no custom metrics, no query language.

Install: `git clone ... && bash install.sh`

I'd love feedback on the architecture and what features would make this more useful. The anomaly detection rules in particular — are the default thresholds reasonable?

---

## Day 5: r/docker

**Title:** Built a monitoring dashboard that runs as a single Docker container — real-time metrics, anomaly detection, Telegram alerts

**Body:**

I wanted to monitor my Docker containers without adding a whole observability stack. So I built **DockProbe** — it runs as one container, mounts the Docker socket read-only, and gives you a real-time dashboard.

**Features:**
- Container metrics: CPU %, memory %, network I/O, block I/O, restart count
- Host metrics: CPU/GPU temp, disk usage, load average
- 6 anomaly detection rules with Telegram alerts (30-min cooldown)
- Historical charts (Chart.js, 7-day retention in SQLite)
- Basic Auth + HTTPS, optional Cloudflare Tunnel

**Architecture:**
- FastAPI + uvicorn (async, single process)
- aiodocker for Docker API
- Single HTML file dashboard (no build step)
- 4 Python packages, ~50MB memory

**docker-compose.yml** mounts:
- `/var/run/docker.sock` (read-only) — container stats
- `/sys` (read-only) — CPU temperature
- `/proc` (read-only) — load average
- `/` (read-only) — disk usage

No write access to anything on the host. Monitoring only.

```bash
git clone https://github.com/deep-on/dockprobe.git && cd dockprobe && bash install.sh
```

GitHub: https://github.com/deep-on/dockprobe

Feedback welcome — especially if you see any issues with the Docker socket usage or security model.

---

## Day 5: Twitter/X

**Post 1 (launch tweet):**

I built DockProbe — a Docker monitoring dashboard that runs as a single container.

Real-time metrics, anomaly detection, Telegram alerts. 4 Python packages, ~50MB RAM, zero config.

One command to install:
git clone + bash install.sh

GitHub: https://github.com/deep-on/dockprobe

#docker #opensource #devops #python #monitoring

**Post 2 (thread follow-up):**

Why I built it:

Prometheus + Grafana + Node Exporter + cAdvisor = 4 containers just to monitor containers.

DockProbe = 1 container. Mount the socket, open the browser, done.

[attach dashboard-full.png screenshot]

**Post 3 (feature highlight):**

DockProbe detects 6 types of anomalies automatically:

- CPU spike (3 consecutive checks)
- Memory overflow
- High temperature
- Disk full
- Restart loop
- Network surge

Alerts go straight to Telegram. No email server needed.

https://github.com/deep-on/dockprobe

---

## Week 2: awesome-selfhosted PR

**PR Title:** Add DockProbe to Monitoring section

**Entry to add** (in Monitoring section, alphabetical order):

```markdown
- [DockProbe](https://github.com/deep-on/dockprobe) - Lightweight Docker container monitoring dashboard with anomaly detection and Telegram alerts. Single container deployment. `MIT` `Python/Docker`
```

**Target file:** `README.md` in https://github.com/awesome-selfhosted/awesome-selfhosted

**Checklist** (from their contribution guidelines):
- [ ] Software is actively maintained
- [ ] Has a proper README with install instructions
- [ ] MIT licensed
- [ ] Self-hosted (not SaaS)
- [ ] Entry follows alphabetical order

---

## Week 2: awesome-docker PR

**PR Title:** Add DockProbe to Monitoring section

**Entry to add:**

```markdown
- [DockProbe](https://github.com/deep-on/dockprobe) - Lightweight monitoring dashboard with anomaly detection and Telegram alerts. Single container, 4 dependencies, ~50MB RAM. By [@deep-on](https://github.com/deep-on)
```

**Target:** https://github.com/veggiemonk/awesome-docker

---

## Week 2: Product Hunt

**Tagline:** Docker monitoring in one container — anomaly detection & Telegram alerts

**Description:**

DockProbe is a lightweight, self-hosted Docker monitoring dashboard. It runs as a single container and provides real-time CPU, memory, network, and disk metrics for all your containers and host machine.

6 built-in anomaly detection rules automatically watch for problems and send alerts to Telegram. No Prometheus, no Grafana, no complex setup — just mount the Docker socket and go.

**Topics:** Docker, Monitoring, DevOps, Open Source, Self-Hosted

**Gallery:** dashboard-full.png, container-table.png, charts.png

---

## Posting Schedule

| Day | Platform | Action |
|-----|----------|--------|
| Day 1 | r/selfhosted | Main launch post |
| Day 2 | Dev.to | Technical blog post |
| Day 3 | r/homelab | Homelab-focused post |
| Day 4 | Hacker News | Show HN submission |
| Day 5 | r/docker + Twitter/X | Docker community + social |
| Week 2 | awesome-selfhosted | PR to awesome list |
| Week 2 | awesome-docker | PR to awesome list |
| Week 2 | Product Hunt | Product launch |

## Tips

- **Respond to every comment** within the first 2 hours — engagement drives visibility
- **Don't cross-post the same day** — Reddit flags this as spam
- **HN timing:** Tuesday-Thursday, 9-11am US Eastern (11pm-1am KST)
- **Reddit timing:** Weekday mornings US time (10pm-midnight KST)
- **Be honest about limitations** — "it's not a Prometheus replacement" builds trust
- **Ask for feedback** — "what would you add?" drives comments, comments drive ranking
