<p align="center">
  <img src="app/static/logo.png" width="80" alt="DockProbe">
</p>

<h1 align="center">DockProbe</h1>

<p align="center">
  <b>Tableau de bord léger de surveillance Docker avec détection d'anomalies & alertes Telegram</b><br>
  Un conteneur. Une commande. Visibilité totale.
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | <a href="README.de.md">Deutsch</a> | <b>Français</b> | <a href="README.es.md">Español</a> | <a href="README.pt.md">Português</a> | <a href="README.it.md">Italiano</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-Apache_2.0-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.12-green" alt="Python">
  <img src="https://img.shields.io/badge/docker-compose-blue" alt="Docker">
  <img src="https://img.shields.io/badge/dependencies-4_only-brightgreen" alt="Deps">
</p>

---

## Qu'est-ce que DockProbe ?

DockProbe est un tableau de bord de surveillance Docker auto-hébergé qui s'exécute dans un seul conteneur. Il collecte en temps réel les métriques CPU, mémoire, réseau et disque de tous vos conteneurs et de la machine hôte — puis affiche tout dans une interface web épurée au thème sombre.

Quand quelque chose ne va pas, DockProbe le détecte automatiquement. Six règles de détection d'anomalies intégrées surveillent les pics CPU, les débordements mémoire, les alertes de température, la pression disque, les redémarrages inattendus et les surcharges réseau. Les alertes sont envoyées instantanément sur Telegram pour que vous puissiez réagir avant que les utilisateurs ne s'en aperçoivent. De plus, un scanner de sécurité intégré exécute 16 vérifications automatisées toutes les 5 minutes — couvrant les erreurs de configuration des conteneurs, l'exposition réseau et le durcissement de l'hôte — pour repérer les vulnérabilités avant qu'elles ne deviennent des incidents.

Pas d'agent à installer sur chaque conteneur, pas de base de données externe, pas de configuration complexe. Montez simplement le socket Docker, exécutez une commande, et vous avez une visibilité complète sur votre environnement Docker à `https://localhost:9090`. Besoin d'un accès depuis l'extérieur ? Le support intégré de Cloudflare Tunnel offre un HTTPS public sécurisé sans redirection de ports.

---

## Démarrage rapide

```bash
git clone https://github.com/deep-on/dockprobe.git && cd dockprobe && bash install.sh
```

C'est tout. L'installateur interactif configure l'authentification, les alertes Telegram et HTTPS — puis ouvre `https://localhost:9090`.

> **Prérequis :** Docker (avec Compose v2), Git, OpenSSL

---

## Aperçu du tableau de bord

<p align="center">
  <img src="docs/screenshots/dashboard-full.png" alt="Tableau de bord DockProbe" width="800">
</p>

---

## Fonctionnalités

| Catégorie | Ce que vous obtenez |
|-----------|-------------------|
| **Tableau de bord en temps réel** | Interface web sombre, actualisation auto 10s, tableaux triables, graphiques Chart.js |
| **Surveillance des conteneurs** | CPU %, mémoire %, E/S réseau, E/S bloc, compteur de redémarrages |
| **Surveillance de l'hôte** | Température et utilisation CPU/GPU, mémoire, utilisation disque, charge moyenne |
| **Détection d'anomalies** | 6 règles avec actions recommandées — pic CPU, dépassement mémoire, haute température, disque plein, redémarrage, pic réseau |
| **Alertes Telegram** | Notification instantanée avec cooldown de 30 min par type d'alerte |
| **Sécurité** | Basic Auth, limitation de débit (5 échecs = 60s de blocage), HTTPS |
| **Scanner de sécurité** | 16 vérifications automatisées (conteneur/hôte/réseau), cycle d'analyse de 5 min, badges de sévérité |
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
| Cartes hôte | Temp CPU, temp GPU, CPU/GPU %, mémoire hôte, disque %, charge moyenne |
| Table des conteneurs | Triable par CPU/mémoire/réseau, anomalies colorées |
| Graphiques (5) | Tendances CPU & mémoire des conteneurs, CPU/GPU % de l'hôte, température & charge de l'hôte |
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

## Scanner de sécurité

DockProbe exécute 16 vérifications de sécurité automatisées toutes les 5 minutes et affiche les résultats dans une section dédiée du tableau de bord avec des badges de sévérité.

| Catégorie | Vérifications |
|-----------|--------------|
| **Conteneur** (9) | Mode privilégié, exécution en root, capabilities dangereuses, montage du socket Docker, montage de chemins sensibles, rootfs en lecture seule, AppArmor/Seccomp désactivés, secrets dans les variables d'environnement, pas de limites mémoire/CPU |
| **Réseau** (3) | Mode réseau hôte, exposition excessive de ports, exposition du port SSH (22) |
| **Hôte** (4) | Options de sécurité du daemon Docker, ASLR du noyau, transfert IP, état du Linux Security Module |

**Niveaux de sévérité :**
- 🔴 **Critique** — Action immédiate requise (ex. : mode privilégié, socket Docker accessible en écriture)
- 🟡 **Avertissement** — Amélioration de sécurité recommandée
- 🔵 **Info** — Constatations informatives
- 🟣 **Indisponible** — La vérification ne peut pas s'exécuter en raison de contraintes d'environnement ; indique comment l'activer

> Les vérifications au niveau de l'hôte nécessitent des montages de volumes (`/proc:/host_proc:ro`, `/sys:/host_sys:ro`). Sans ces montages, les vérifications concernées s'affichent comme **Indisponible** avec les instructions de configuration.

---

## Architecture

```
┌─────────────────────────────────────────┐
│  DockProbe Container                    │
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

### Option 1 : Réseau local (SSL auto-signé) — par défaut

```bash
bash install.sh   # choisir l'option 1
```

Accès via `https://localhost:9090` ou `https://<votre-ip>:9090`

Pour accéder depuis d'autres appareils sur le même réseau, utilisez l'IP LAN du serveur (ex : `https://192.168.1.100:9090`). Si nécessaire :
- Autoriser le port dans le pare-feu : `sudo ufw allow 9090/tcp`
- Accepter l'avertissement du certificat auto-signé dans le navigateur

> **Pourquoi cet avertissement du navigateur ?** DockProbe utilise un certificat SSL auto-signé généré lors de l'installation. Comme il n'est pas émis par une Autorité de Certification (CA) de confiance, le navigateur affiche un avertissement "Votre connexion n'est pas privée". C'est normal — cliquez sur "Avancé" → "Continuer vers le site". Pour supprimer cet avertissement, utilisez Cloudflare Tunnel (Option 3) qui fournit automatiquement un certificat TLS de confiance.

### Option 2 : Accès distant par redirection de port

Pour un accès externe sans Cloudflare :

1. Rediriger le port 9090 sur votre routeur vers l'IP LAN du serveur
2. Accéder via `https://<votre-ip-publique>:9090`
3. Utiliser un service DNS dynamique (No-IP, DuckDNS, etc.) si votre IP publique change

> **Note :** Le port est directement exposé. Basic Auth + HTTPS sont activés par défaut, mais Cloudflare Tunnel (Option 3) est recommandé pour une meilleure sécurité.

### Option 3 : Cloudflare Tunnel (recommandé pour l'accès distant)

Pas de redirection de port, pas de modification du pare-feu, certificat TLS valide — la méthode la plus simple et sécurisée pour accéder depuis n'importe où.

```bash
bash install.sh   # choisir l'option 2, coller le token du tunnel
```

**Étapes de configuration :**
1. Créer un compte gratuit sur [Cloudflare Zero Trust](https://one.dash.cloudflare.com)
2. Aller dans **Networks** > **Tunnels** > **Create a tunnel**
3. Nommer le tunnel (ex : `dockprobe`) et copier le token
4. Exécuter `bash install.sh` et choisir l'option Cloudflare Tunnel
5. Coller le token
6. Dans le tableau de bord Cloudflare, ajouter un **Public Hostname** pointant vers `http://localhost:9090`
7. Accéder via `https://your-domain.com` avec un certificat TLS valide

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
git clone https://github.com/deep-on/dockprobe.git
cd dockprobe

# Créer .env
cp .env.example .env
vi .env

# Générer le certificat SSL (optionnel)
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -subj "/CN=dockprobe"

# Démarrer
docker compose up -d --build
```

---

## Licence

Apache License 2.0 — voir [LICENSE](LICENSE)

**Attribution :** Les versions modifiées ou redistribuées doivent conserver le logo DeepOn et la mention « Powered by DeepOn Inc. » dans l'interface.

---

<p align="center">
  <img src="app/static/logo.png" width="24" alt="DeepOn">
  Développé par <a href="https://deep-on.com">DeepOn Inc.</a>
</p>
