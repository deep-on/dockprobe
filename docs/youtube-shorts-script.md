# DockWatch — YouTube Shorts Script (60s)

## Storyboard

| Time | Scene | Script (Voiceover / Text Overlay) | Visual |
|------|-------|-----------------------------------|--------|
| 0–5s | **Hook** | "Monitor all your Docker containers in 60 seconds — no Prometheus, no Grafana." | Quick cuts: terminal → dashboard → Telegram alert |
| 5–12s | **Install** | "One command. That's it." | Terminal: `git clone ... && bash install.sh` running. Show interactive prompts being answered |
| 12–20s | **Dashboard Tour — Overview** | "Real-time dashboard with auto-refresh every 10 seconds." | Browser opens `https://localhost:9090`. Show session bar, host cards |
| 20–28s | **Dashboard Tour — Containers** | "Every container. CPU, memory, network — all sortable." | Scroll to container table, click column headers to sort |
| 28–36s | **Dashboard Tour — Charts** | "Live charts for CPU trends, memory, temperature, and load." | Scroll to charts section, hover over Chart.js graphs |
| 36–44s | **Anomaly Detection** | "Built-in anomaly detection. CPU spike? Memory overflow? You get a Telegram alert instantly." | Show a red-highlighted container row → cut to Telegram notification on phone |
| 44–50s | **Tech Stack** | "4 Python packages. Single HTML file. SQLite. Nothing else." | Text overlay listing: FastAPI, uvicorn, aiodocker, httpx. Show the single index.html file |
| 50–57s | **Why It's Different** | "No database to manage. No YAML config files. Just clone, install, done." | Side-by-side comparison: Prometheus+Grafana stack diagram vs DockWatch single container |
| 57–60s | **CTA** | "Link in bio. Star it on GitHub." | DockWatch logo + GitHub URL + star button animation |

---

## Filming Guide

### Resolution & Format
- **Aspect ratio:** 9:16 (vertical / 1080×1920)
- **Resolution:** 1080p minimum, 4K preferred for quality downscale
- **Frame rate:** 30fps (screen recordings), 60fps (face cam if used)

### Screen Recording Settings
- **Terminal font size:** 20pt+ (must be readable on mobile)
- **Browser zoom:** 125–150% (dashboard elements must be visible at 1080px wide crop)
- **Dark mode:** Use the default DockWatch dark theme
- **Clean desktop:** Hide taskbar, notifications, bookmarks bar

### Dashboard Capture Tips
- Run at least 3–5 containers to show meaningful data in tables and charts
- Let the dashboard collect data for 5+ minutes before recording so charts have visible trends
- Trigger a test anomaly (e.g., `stress --cpu 4` in a container) to show the red highlight + Telegram alert

### Editing Tips
- Add subtle zoom-in transitions when showing specific UI sections
- Use arrow/highlight overlays to draw attention to key metrics
- Text overlays: white text, semi-transparent dark background, bottom 1/3 of screen
- Background music: lo-fi or tech ambient, low volume (voice/narration should dominate)
- Add sound effects on transitions (subtle whoosh or click)

### Thumbnail
- Split screen: messy Grafana/Prometheus setup (left, red tint) vs clean DockWatch dashboard (right, green tint)
- Large text: "Monitor Docker in 60s"
- DockWatch logo in corner

---

## Key Messages to Emphasize

1. **Simplicity** — One command install, zero config
2. **Lightweight** — 4 dependencies, single container, SQLite
3. **Complete** — Dashboard + anomaly detection + alerts out of the box
4. **Self-hosted** — Your data stays on your server
5. **Open source** — MIT license, free forever
