<p align="center">
  <img src="app/static/logo.png" width="80" alt="DockWatch">
</p>

<h1 align="center">DockWatch</h1>

<p align="center">
  <b>Tableau de bord léger de surveillance Docker avec détection d'anomalies & alertes Telegram</b><br>
  Un conteneur. Une commande. Visibilité totale.
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | <a href="README.de.md">Deutsch</a> | <b>Français</b> | <a href="README.es.md">Español</a> | <a href="README.pt.md">Português</a> | <a href="README.it.md">Italiano</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.12-green" alt="Python">
  <img src="https://img.shields.io/badge/docker-compose-blue" alt="Docker">
  <img src="https://img.shields.io/badge/dependencies-4_only-brightgreen" alt="Deps">
</p>

---

## Démarrage rapide

```bash
git clone https://github.com/deep-on/dockwatch.git && cd dockwatch && bash install.sh
```

C'est tout. L'installateur interactif configure l'authentification, les alertes Telegram et HTTPS — puis ouvre `https://localhost:9090`.

> **Prérequis :** Docker (avec Compose v2), Git, OpenSSL

---

## Aperçu du tableau de bord

<p align="center">
  <img src="docs/screenshots/dashboard-full.png" alt="Tableau de bord DockWatch" width="800">
</p>

---

## Fonctionnalités

| Catégorie | Ce que vous obtenez |
|-----------|-------------------|
| **Tableau de bord en temps réel** | Interface web sombre, actualisation auto 10s, tableaux triables, graphiques Chart.js |
| **Surveillance des conteneurs** | CPU %, mémoire %, E/S réseau, E/S bloc, compteur de redémarrages |
| **Surveillance de l'hôte** | Température CPU/GPU, utilisation disque, charge moyenne |
| **Détection d'anomalies** | 6 règles — pic CPU, dépassement mémoire, haute température, disque plein, redémarrage, pic réseau |
| **Alertes Telegram** | Notification instantanée avec cooldown de 30 min par type d'alerte |
| **Sécurité** | Basic Auth, limitation de débit (5 échecs = 60s de blocage), HTTPS |
| **Gestion des sessions** | Suivi des connexions actives, max connexions configurable, affichage IP en direct |
| **Gestion des mots de passe** | Changement nom d'utilisateur/mot de passe via l'interface |
| **Interface de réglages** | Ajuster le max de connexions à la volée depuis le tableau de bord |
| **Modes d'accès** | SSL auto-signé (par défaut) ou Cloudflare Tunnel (sans redirection de port) |
| **Léger** | 4 paquets Python, fichier HTML unique, SQLite avec rétention de 7 jours |

---

## Composition du tableau de bord

| Section | Détails |
|---------|---------|
| Barre de session | Utilisateur connecté, IP, connexions actives / limite max |
| Cartes hôte | Temp CPU, temp GPU, disque %, charge moyenne |
| Table des conteneurs | Triable par CPU/mémoire/réseau, anomalies colorées |
| Graphiques (4) | Tendances CPU & mémoire des conteneurs, température & charge de l'hôte |
| Disque Docker | Images, cache de build, volumes, couches RW des conteneurs |
| Historique des alertes | Dernières 24h avec horodatages |

---

## Règles de détection d'anomalies

| Règle | Condition | Action |
|-------|-----------|--------|
| CPU conteneur | >80% pendant 3 vérifications consécutives (30s) | Telegram + surbrillance rouge |
| Mémoire conteneur | >90% de la limite | Alerte immédiate |
| Température CPU hôte | >85°C | Alerte immédiate |
| Disque hôte | >90% d'utilisation | Alerte immédiate |
| Redémarrage conteneur | restart_count augmenté | Alerte immédiate |
| Pic réseau | RX augmentation 10x + >100Mo | Alerte immédiate |

Tous les seuils sont configurables via les variables d'environnement.

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
│  │   ├── detector.py    (machine à états) │
│  │   └── telegram.py    (httpx)         │
│  ├── storage/                           │
│  │   └── db.py          (SQLite WAL)    │
│  └── static/                            │
│      └── index.html     (Chart.js)      │
│                                         │
│  Volumes montés :                       │
│    docker.sock (ro), /sys (ro),         │
│    /proc (ro), SQLite named volume      │
└─────────────────────────────────────────┘
```

**Dépendances (4 paquets uniquement) :**
- `fastapi` — Framework web
- `uvicorn` — Serveur ASGI
- `aiodocker` — Client Docker API asynchrone
- `httpx` — Client HTTP asynchrone (API Telegram)

---

## Configuration

Tous les paramètres via le fichier `.env` :

```env
# Authentification (requis)
AUTH_USER=admin
AUTH_PASS=your-password

# Alertes Telegram (optionnel)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Seuils (optionnel, valeurs par défaut affichées)
CPU_THRESHOLD=80
MEM_THRESHOLD=90

# Limite de connexions (optionnel, 0 = illimité)
MAX_CONNECTIONS=3

# Cloudflare Tunnel (optionnel)
CF_TUNNEL_TOKEN=your-tunnel-token
```

---

## Modes d'accès

### Option 1 : Local (SSL auto-signé) — par défaut

```bash
bash install.sh   # choisir l'option 1
```

Accès via `https://localhost:9090` ou `https://<votre-ip>:9090`

### Option 2 : Cloudflare Tunnel (pas de redirection de port nécessaire)

```bash
bash install.sh   # choisir l'option 2, coller le token du tunnel
```

HTTPS public via votre domaine Cloudflare Tunnel — aucune configuration routeur requise.

---

## Points de terminaison API

| Point de terminaison | Méthode | Description |
|---------------------|---------|-------------|
| `/` | GET | HTML du tableau de bord |
| `/api/current` | GET | Dernier instantané (conteneurs + hôte + images + anomalies) |
| `/api/history/{name}?hours=1` | GET | Séries temporelles des conteneurs |
| `/api/history/host?hours=1` | GET | Séries temporelles de l'hôte |
| `/api/alerts?hours=24` | GET | Historique des alertes |
| `/api/session` | GET | Utilisateur actuel, IP, connexions actives |
| `/api/settings` | GET/POST | Paramètres d'exécution (max_connections) |
| `/api/change-password` | POST | Changer nom d'utilisateur/mot de passe |
| `/api/health` | GET | Vérification de santé (sans authentification) |

---

## Sécurité

- **Basic Auth** sur tous les points de terminaison (sauf `/api/health`)
- **Limitation de débit** — 5 tentatives échouées → 60s de blocage par IP
- **HTTPS** — Auto-signé ou Cloudflare Tunnel
- **Limite de connexions** — Maximum d'utilisateurs simultanés configurable
- **Montages en lecture seule** — Docker socket, /sys, /proc tous montés en read-only
- **Aucun accès en écriture** — Surveillance uniquement, pas de contrôle des conteneurs

---

## Installation manuelle

Si vous préférez la configuration manuelle :

```bash
git clone https://github.com/deep-on/dockwatch.git
cd dockwatch

# Créer .env
cp .env.example .env
vi .env

# Générer le certificat SSL (optionnel)
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -subj "/CN=dockwatch"

# Démarrer
docker compose up -d --build
```

---

## Licence

MIT License — voir [LICENSE](LICENSE)

**Attribution :** Les versions modifiées ou redistribuées doivent conserver le logo DeepOn et la mention « Powered by DeepOn Inc. » dans l'interface.

---

<p align="center">
  <img src="app/static/logo.png" width="24" alt="DeepOn">
  Développé par <a href="https://deep-on.com">DeepOn Inc.</a>
</p>
