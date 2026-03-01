<p align="center">
  <img src="app/static/logo.png" width="80" alt="DockWatch">
</p>

<h1 align="center">DockWatch</h1>

<p align="center">
  <b>Leichtgewichtiges Docker-Monitoring-Dashboard mit Anomalieerkennung & Telegram-Benachrichtigungen</b><br>
  Ein Container. Ein Befehl. Volle Übersicht.
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | <b>Deutsch</b> | <a href="README.fr.md">Français</a> | <a href="README.es.md">Español</a> | <a href="README.pt.md">Português</a> | <a href="README.it.md">Italiano</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.12-green" alt="Python">
  <img src="https://img.shields.io/badge/docker-compose-blue" alt="Docker">
  <img src="https://img.shields.io/badge/dependencies-4_only-brightgreen" alt="Deps">
</p>

---

## Was ist DockWatch?

DockWatch ist ein selbst gehostetes Docker-Monitoring-Dashboard, das als einzelner Container läuft. Es sammelt in Echtzeit CPU-, Speicher-, Netzwerk- und Festplattenmetriken von allen Containern und dem Host-System — und zeigt alles in einer übersichtlichen, dunklen Web-Oberfläche an.

Wenn etwas schiefgeht, erkennt DockWatch es automatisch. Sechs integrierte Anomalieerkennungsregeln überwachen CPU-Spitzen, Speicherüberläufe, Temperaturwarnungen, Festplattenengpässe, unerwartete Neustarts und Netzwerkanstiege. Alarme werden sofort per Telegram gesendet, damit Sie reagieren können, bevor Nutzer es bemerken.

Kein Agent muss auf jedem Container installiert werden, keine externe Datenbank, keine komplexe Konfiguration. Einfach den Docker-Socket einbinden, einen Befehl ausführen, und Sie haben unter `https://localhost:9090` volle Übersicht über Ihre Docker-Umgebung.

---

## Schnellstart

```bash
git clone https://github.com/deep-on/dockwatch.git && cd dockwatch && bash install.sh
```

Das war's. Der interaktive Installer konfiguriert Authentifizierung, Telegram-Benachrichtigungen und HTTPS — und öffnet dann `https://localhost:9090`.

> **Voraussetzungen:** Docker (mit Compose v2), Git, OpenSSL

---

## Dashboard-Vorschau

<p align="center">
  <img src="docs/screenshots/dashboard-full.png" alt="DockWatch Dashboard" width="800">
</p>

---

## Funktionen

| Kategorie | Was Sie erhalten |
|-----------|-----------------|
| **Echtzeit-Dashboard** | Dunkles Web-UI, 10s Auto-Aktualisierung, sortierbare Tabellen, Chart.js-Diagramme |
| **Container-Monitoring** | CPU %, Speicher %, Netzwerk-I/O, Block-I/O, Neustart-Zähler |
| **Host-Monitoring** | CPU/GPU-Temperatur, Festplattennutzung, Lastdurchschnitt |
| **Anomalieerkennung** | 6 Regeln — CPU-Spitze, Speicherüberlauf, Hochtemperatur, Festplatte voll, Neustart, Netzwerk-Spitze |
| **Telegram-Benachrichtigungen** | Sofortige Benachrichtigung mit 30-Min-Cooldown pro Alarmtyp |
| **Sicherheit** | Basic Auth, Ratenlimitierung (5 Fehlversuche = 60s Sperre), HTTPS |
| **Sitzungsverwaltung** | Aktive Verbindungsverfolgung, konfigurierbare Max-Verbindungen, Live-IP-Anzeige |
| **Passwortverwaltung** | Benutzername/Passwort über Dashboard-UI ändern |
| **Einstellungs-UI** | Max-Verbindungen zur Laufzeit über das Dashboard anpassen |
| **Zugriffsmodi** | Selbstsigniertes SSL (Standard) oder Cloudflare Tunnel (kein Port-Forwarding) |
| **Leichtgewichtig** | 4 Python-Pakete, einzelne HTML-Datei, SQLite mit 7-Tage-Aufbewahrung |

---

## Dashboard-Aufbau

| Bereich | Details |
|---------|---------|
| Sitzungsleiste | Angemeldeter Benutzer, IP, aktive Verbindungen / Max-Limit |
| Host-Karten | CPU-Temp, GPU-Temp, Festplatte %, Lastdurchschnitt |
| Container-Tabelle | Sortierbar nach CPU/Speicher/Netzwerk, farbcodierte Anomalien |
| Diagramme (4) | Container-CPU- & Speicher-Trends, Host-Temperatur & Last |
| Docker-Festplatte | Images, Build-Cache, Volumes, Container-RW-Schichten |
| Alarm-Verlauf | Letzte 24h mit Zeitstempeln |

---

## Anomalieerkennungsregeln

| Regel | Bedingung | Aktion |
|-------|-----------|--------|
| Container-CPU | >80% für 3 aufeinanderfolgende Prüfungen (30s) | Telegram + rote Hervorhebung |
| Container-Speicher | >90% des Limits | Sofortiger Alarm |
| Host-CPU-Temperatur | >85°C | Sofortiger Alarm |
| Host-Festplatte | >90% Nutzung | Sofortiger Alarm |
| Container-Neustart | restart_count erhöht | Sofortiger Alarm |
| Netzwerk-Spitze | RX 10-facher Anstieg + >100MB | Sofortiger Alarm |

Alle Schwellenwerte sind über Umgebungsvariablen konfigurierbar.

---

## Architektur

```
┌─────────────────────────────────────────┐
│  DockWatch Container                    │
│                                         │
│  FastAPI + uvicorn (Port 9090)          │
│  ├── collectors/                        │
│  │   ├── containers.py  (aiodocker)     │
│  │   ├── host.py        (/proc, /sys)   │
│  │   └── images.py      (system df)     │
│  ├── alerting/                          │
│  │   ├── detector.py    (Zustandsautomat) │
│  │   └── telegram.py    (httpx)         │
│  ├── storage/                           │
│  │   └── db.py          (SQLite WAL)    │
│  └── static/                            │
│      └── index.html     (Chart.js)      │
│                                         │
│  Volumes:                               │
│    docker.sock (ro), /sys (ro),         │
│    /proc (ro), SQLite Named Volume      │
└─────────────────────────────────────────┘
```

**Abhängigkeiten (nur 4 Pakete):**
- `fastapi` — Web-Framework
- `uvicorn` — ASGI-Server
- `aiodocker` — Asynchroner Docker-API-Client
- `httpx` — Asynchroner HTTP-Client (Telegram-API)

---

## Konfiguration

Alle Einstellungen über `.env`-Datei:

```env
# Authentifizierung (erforderlich)
AUTH_USER=admin
AUTH_PASS=your-password

# Telegram-Benachrichtigungen (optional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Schwellenwerte (optional, Standardwerte angezeigt)
CPU_THRESHOLD=80
MEM_THRESHOLD=90

# Verbindungslimit (optional, 0 = unbegrenzt)
MAX_CONNECTIONS=3

# Cloudflare Tunnel (optional)
CF_TUNNEL_TOKEN=your-tunnel-token
```

---

## Zugriffsmodi

### Option 1: Lokal (selbstsigniertes SSL) — Standard

```bash
bash install.sh   # Option 1 wählen
```

Zugriff über `https://localhost:9090` oder `https://<Ihre-IP>:9090`

### Option 2: Cloudflare Tunnel (kein Port-Forwarding nötig)

```bash
bash install.sh   # Option 2 wählen, Tunnel-Token eingeben
```

Öffentlicher HTTPS-Zugang über Ihre Cloudflare-Tunnel-Domain — keine Router-Konfiguration erforderlich.

---

## API-Endpunkte

| Endpunkt | Methode | Beschreibung |
|----------|---------|-------------|
| `/` | GET | Dashboard-HTML |
| `/api/current` | GET | Neuester Snapshot (Container + Host + Images + Anomalien) |
| `/api/history/{name}?hours=1` | GET | Container-Zeitreihen |
| `/api/history/host?hours=1` | GET | Host-Zeitreihen |
| `/api/alerts?hours=24` | GET | Alarm-Verlauf |
| `/api/session` | GET | Aktueller Benutzer, IP, aktive Verbindungen |
| `/api/settings` | GET/POST | Laufzeiteinstellungen (max_connections) |
| `/api/change-password` | POST | Benutzername/Passwort ändern |
| `/api/health` | GET | Gesundheitsprüfung (keine Authentifizierung erforderlich) |

---

## Sicherheit

- **Basic Auth** auf allen Endpunkten (außer `/api/health`)
- **Ratenlimitierung** — 5 fehlgeschlagene Anmeldeversuche → 60s Sperre pro IP
- **HTTPS** — Selbstsigniert oder Cloudflare Tunnel
- **Verbindungslimit** — Konfigurierbare maximale gleichzeitige Benutzer
- **Nur-Lese-Mounts** — Docker-Socket, /sys, /proc alle read-only eingebunden
- **Kein Schreibzugriff** — Nur Monitoring, keine Container-Steuerung

---

## Manuelle Einrichtung

Falls Sie die manuelle Konfiguration bevorzugen:

```bash
git clone https://github.com/deep-on/dockwatch.git
cd dockwatch

# .env erstellen
cp .env.example .env
vi .env

# SSL-Zertifikat generieren (optional)
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -subj "/CN=dockwatch"

# Starten
docker compose up -d --build
```

---

## Lizenz

MIT License — siehe [LICENSE](LICENSE)

**Namensnennung:** Modifizierte oder weiterverteilte Versionen müssen das DeepOn-Logo und den Hinweis „Powered by DeepOn Inc." in der Benutzeroberfläche beibehalten.

---

<p align="center">
  <img src="app/static/logo.png" width="24" alt="DeepOn">
  Entwickelt von <a href="https://deep-on.com">DeepOn Inc.</a>
</p>
