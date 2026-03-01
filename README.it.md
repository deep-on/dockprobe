<p align="center">
  <img src="app/static/logo.png" width="80" alt="DockWatch">
</p>

<h1 align="center">DockWatch</h1>

<p align="center">
  <b>Dashboard leggera per il monitoraggio Docker con rilevamento anomalie e avvisi Telegram</b><br>
  Un container. Un comando. Visibilità completa.
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | <a href="README.de.md">Deutsch</a> | <a href="README.fr.md">Français</a> | <a href="README.es.md">Español</a> | <a href="README.pt.md">Português</a> | <b>Italiano</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.12-green" alt="Python">
  <img src="https://img.shields.io/badge/docker-compose-blue" alt="Docker">
  <img src="https://img.shields.io/badge/dependencies-4_only-brightgreen" alt="Deps">
</p>

---

## Cos'è DockWatch?

DockWatch è una dashboard di monitoraggio Docker self-hosted che funziona come un singolo container. Raccoglie in tempo reale metriche di CPU, memoria, rete e disco da tutti i container e dalla macchina host — e visualizza tutto in un'interfaccia web pulita con tema scuro.

Quando qualcosa va storto, DockWatch lo rileva automaticamente. Sei regole integrate di rilevamento anomalie monitorano picchi di CPU, overflow di memoria, avvisi di temperatura, pressione disco, riavvii imprevisti e picchi di rete. Gli avvisi vengono inviati istantaneamente tramite Telegram, così puoi intervenire prima che gli utenti se ne accorgano.

Nessun agente da installare su ogni container, nessun database esterno, nessuna configurazione complessa. Basta montare il socket Docker, eseguire un comando, e avrai piena visibilità sul tuo ambiente Docker su `https://localhost:9090`.

---

## Avvio rapido

```bash
git clone https://github.com/deep-on/dockwatch.git && cd dockwatch && bash install.sh
```

Tutto qui. L'installer interattivo configura l'autenticazione, gli avvisi Telegram e HTTPS — poi apre `https://localhost:9090`.

> **Requisiti:** Docker (con Compose v2), Git, OpenSSL

---

## Anteprima della dashboard

<p align="center">
  <img src="docs/screenshots/dashboard-full.png" alt="Dashboard DockWatch" width="800">
</p>

---

## Funzionalità

| Categoria | Cosa ottieni |
|-----------|-------------|
| **Dashboard in tempo reale** | Interfaccia web scura, aggiornamento automatico ogni 10s, tabelle ordinabili, grafici Chart.js |
| **Monitoraggio container** | CPU %, memoria %, I/O di rete, I/O di blocco, contatore riavvii |
| **Monitoraggio host** | Temperatura CPU/GPU, utilizzo disco, media di carico |
| **Rilevamento anomalie** | 6 regole — picco CPU, overflow memoria, alta temperatura, disco pieno, riavvio, picco di rete |
| **Avvisi Telegram** | Notifica istantanea con cooldown di 30 min per tipo di avviso |
| **Sicurezza** | Basic Auth, limitazione di frequenza (5 tentativi falliti = 60s di blocco), HTTPS |
| **Gestione sessioni** | Tracciamento connessioni attive, max connessioni configurabile, visualizzazione IP in tempo reale |
| **Gestione password** | Modifica utente/password dall'interfaccia della dashboard |
| **Interfaccia impostazioni** | Regolare max connessioni a runtime dalla dashboard |
| **Modalità di accesso** | SSL autofirmato (predefinito) o Cloudflare Tunnel (senza port forwarding) |
| **Leggera** | 4 pacchetti Python, singolo file HTML, SQLite con conservazione di 7 giorni |

---

## Composizione della dashboard

| Sezione | Dettagli |
|---------|---------|
| Barra sessione | Utente connesso, IP, connessioni attive / limite massimo |
| Schede host | Temp CPU, temp GPU, disco %, media di carico |
| Tabella container | Ordinabile per CPU/memoria/rete, anomalie con codice colore |
| Grafici (4) | Tendenze CPU e memoria dei container, temperatura e carico dell'host |
| Disco Docker | Immagini, cache di build, volumi, layer RW dei container |
| Storico avvisi | Ultime 24h con timestamp |

---

## Regole di rilevamento anomalie

| Regola | Condizione | Azione |
|--------|-----------|--------|
| CPU container | >80% per 3 controlli consecutivi (30s) | Telegram + evidenziazione rossa |
| Memoria container | >90% del limite | Avviso immediato |
| Temperatura CPU host | >85°C | Avviso immediato |
| Disco host | >90% di utilizzo | Avviso immediato |
| Riavvio container | restart_count incrementato | Avviso immediato |
| Picco di rete | RX aumento 10x + >100MB | Avviso immediato |

Tutte le soglie sono configurabili tramite variabili d'ambiente.

---

## Architettura

```
┌─────────────────────────────────────────┐
│  DockWatch Container                    │
│                                         │
│  FastAPI + uvicorn (porta 9090)         │
│  ├── collectors/                        │
│  │   ├── containers.py  (aiodocker)     │
│  │   ├── host.py        (/proc, /sys)   │
│  │   └── images.py      (system df)     │
│  ├── alerting/                          │
│  │   ├── detector.py    (macchina a stati) │
│  │   └── telegram.py    (httpx)         │
│  ├── storage/                           │
│  │   └── db.py          (SQLite WAL)    │
│  └── static/                            │
│      └── index.html     (Chart.js)      │
│                                         │
│  Volumi:                                │
│    docker.sock (ro), /sys (ro),         │
│    /proc (ro), SQLite named volume      │
└─────────────────────────────────────────┘
```

**Dipendenze (solo 4 pacchetti):**
- `fastapi` — Framework web
- `uvicorn` — Server ASGI
- `aiodocker` — Client Docker API asincrono
- `httpx` — Client HTTP asincrono (API Telegram)

---

## Configurazione

Tutte le impostazioni tramite file `.env`:

```env
# Autenticazione (obbligatorio)
AUTH_USER=admin
AUTH_PASS=your-password

# Avvisi Telegram (opzionale)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Soglie (opzionale, valori predefiniti mostrati)
CPU_THRESHOLD=80
MEM_THRESHOLD=90

# Limite connessioni (opzionale, 0 = illimitato)
MAX_CONNECTIONS=3

# Cloudflare Tunnel (opzionale)
CF_TUNNEL_TOKEN=your-tunnel-token
```

---

## Modalità di accesso

### Opzione 1: Locale (SSL autofirmato) — predefinito

```bash
bash install.sh   # scegliere opzione 1
```

Accesso via `https://localhost:9090` o `https://<tuo-ip>:9090`

### Opzione 2: Cloudflare Tunnel (senza port forwarding)

```bash
bash install.sh   # scegliere opzione 2, incollare token del tunnel
```

HTTPS pubblico tramite il tuo dominio Cloudflare Tunnel — nessuna configurazione del router necessaria.

---

## Endpoint API

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/` | GET | HTML della dashboard |
| `/api/current` | GET | Ultimo snapshot (container + host + immagini + anomalie) |
| `/api/history/{name}?hours=1` | GET | Serie temporali dei container |
| `/api/history/host?hours=1` | GET | Serie temporali dell'host |
| `/api/alerts?hours=24` | GET | Storico avvisi |
| `/api/session` | GET | Utente attuale, IP, connessioni attive |
| `/api/settings` | GET/POST | Impostazioni a runtime (max_connections) |
| `/api/change-password` | POST | Modifica utente/password |
| `/api/health` | GET | Controllo di salute (senza autenticazione) |

---

## Sicurezza

- **Basic Auth** su tutti gli endpoint (eccetto `/api/health`)
- **Limitazione di frequenza** — 5 tentativi falliti → 60s di blocco per IP
- **HTTPS** — Autofirmato o Cloudflare Tunnel
- **Limite connessioni** — Massimo utenti simultanei configurabile
- **Mount in sola lettura** — Docker socket, /sys, /proc tutti montati in read-only
- **Nessun accesso in scrittura** — Solo monitoraggio, nessun controllo dei container

---

## Configurazione manuale

Se preferisci la configurazione manuale:

```bash
git clone https://github.com/deep-on/dockwatch.git
cd dockwatch

# Creare .env
cp .env.example .env
vi .env

# Generare certificato SSL (opzionale)
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -subj "/CN=dockwatch"

# Avviare
docker compose up -d --build
```

---

## Licenza

MIT License — vedi [LICENSE](LICENSE)

**Attribuzione:** Le versioni modificate o ridistribuite devono mantenere il logo DeepOn e l'avviso "Powered by DeepOn Inc." nell'interfaccia.

---

<p align="center">
  <img src="app/static/logo.png" width="24" alt="DeepOn">
  Sviluppato da <a href="https://deep-on.com">DeepOn Inc.</a>
</p>
