<p align="center">
  <img src="app/static/logo.png" width="80" alt="DockWatch">
</p>

<h1 align="center">DockWatch</h1>

<p align="center">
  <b>Panel de monitoreo Docker ligero con detección de anomalías y alertas de Telegram</b><br>
  Un contenedor. Un comando. Visibilidad total.
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | <a href="README.de.md">Deutsch</a> | <a href="README.fr.md">Français</a> | <b>Español</b> | <a href="README.pt.md">Português</a> | <a href="README.it.md">Italiano</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.12-green" alt="Python">
  <img src="https://img.shields.io/badge/docker-compose-blue" alt="Docker">
  <img src="https://img.shields.io/badge/dependencies-4_only-brightgreen" alt="Deps">
</p>

---

## Inicio rápido

```bash
git clone https://github.com/deep-on/dockwatch.git && cd dockwatch && bash install.sh
```

Eso es todo. El instalador interactivo configura la autenticación, alertas de Telegram y HTTPS — luego abre `https://localhost:9090`.

> **Requisitos:** Docker (con Compose v2), Git, OpenSSL

---

## Vista previa del panel

<p align="center">
  <img src="docs/screenshots/dashboard-full.png" alt="Panel DockWatch" width="800">
</p>

---

## Características

| Categoría | Qué obtienes |
|-----------|-------------|
| **Panel en tiempo real** | Interfaz web oscura, actualización automática cada 10s, tablas ordenables, gráficos Chart.js |
| **Monitoreo de contenedores** | CPU %, memoria %, E/S de red, E/S de bloque, contador de reinicios |
| **Monitoreo del host** | Temperatura CPU/GPU, uso de disco, carga promedio |
| **Detección de anomalías** | 6 reglas — pico de CPU, desbordamiento de memoria, alta temperatura, disco lleno, reinicio, pico de red |
| **Alertas de Telegram** | Notificación instantánea con cooldown de 30 min por tipo de alerta |
| **Seguridad** | Basic Auth, limitación de tasa (5 fallos = 60s de bloqueo), HTTPS |
| **Gestión de sesiones** | Seguimiento de conexiones activas, máx. conexiones configurable, visualización de IP en vivo |
| **Gestión de contraseñas** | Cambiar usuario/contraseña desde la interfaz del panel |
| **Interfaz de configuración** | Ajustar máx. conexiones en tiempo de ejecución desde el panel |
| **Modos de acceso** | SSL autofirmado (por defecto) o Cloudflare Tunnel (sin redirección de puertos) |
| **Ligero** | 4 paquetes Python, un solo archivo HTML, SQLite con retención de 7 días |

---

## Composición del panel

| Sección | Detalles |
|---------|---------|
| Barra de sesión | Usuario conectado, IP, conexiones activas / límite máximo |
| Tarjetas del host | Temp CPU, temp GPU, disco %, carga promedio |
| Tabla de contenedores | Ordenable por CPU/memoria/red, anomalías con código de color |
| Gráficos (4) | Tendencias de CPU y memoria de contenedores, temperatura y carga del host |
| Disco Docker | Imágenes, caché de construcción, volúmenes, capas RW de contenedores |
| Historial de alertas | Últimas 24h con marcas de tiempo |

---

## Reglas de detección de anomalías

| Regla | Condición | Acción |
|-------|-----------|--------|
| CPU del contenedor | >80% durante 3 verificaciones consecutivas (30s) | Telegram + resaltado rojo |
| Memoria del contenedor | >90% del límite | Alerta inmediata |
| Temperatura CPU del host | >85°C | Alerta inmediata |
| Disco del host | >90% de uso | Alerta inmediata |
| Reinicio del contenedor | restart_count incrementado | Alerta inmediata |
| Pico de red | RX aumento 10x + >100MB | Alerta inmediata |

Todos los umbrales son configurables mediante variables de entorno.

---

## Arquitectura

```
┌─────────────────────────────────────────┐
│  DockWatch Container                    │
│                                         │
│  FastAPI + uvicorn (puerto 9090)        │
│  ├── collectors/                        │
│  │   ├── containers.py  (aiodocker)     │
│  │   ├── host.py        (/proc, /sys)   │
│  │   └── images.py      (system df)     │
│  ├── alerting/                          │
│  │   ├── detector.py    (máquina de estados) │
│  │   └── telegram.py    (httpx)         │
│  ├── storage/                           │
│  │   └── db.py          (SQLite WAL)    │
│  └── static/                            │
│      └── index.html     (Chart.js)      │
│                                         │
│  Volúmenes:                             │
│    docker.sock (ro), /sys (ro),         │
│    /proc (ro), SQLite named volume      │
└─────────────────────────────────────────┘
```

**Dependencias (solo 4 paquetes):**
- `fastapi` — Framework web
- `uvicorn` — Servidor ASGI
- `aiodocker` — Cliente Docker API asíncrono
- `httpx` — Cliente HTTP asíncrono (API de Telegram)

---

## Configuración

Todos los ajustes mediante el archivo `.env`:

```env
# Autenticación (requerido)
AUTH_USER=admin
AUTH_PASS=your-password

# Alertas de Telegram (opcional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Umbrales (opcional, se muestran valores por defecto)
CPU_THRESHOLD=80
MEM_THRESHOLD=90

# Límite de conexiones (opcional, 0 = ilimitado)
MAX_CONNECTIONS=3

# Cloudflare Tunnel (opcional)
CF_TUNNEL_TOKEN=your-tunnel-token
```

---

## Modos de acceso

### Opción 1: Local (SSL autofirmado) — por defecto

```bash
bash install.sh   # elegir opción 1
```

Acceso vía `https://localhost:9090` o `https://<tu-ip>:9090`

### Opción 2: Cloudflare Tunnel (sin redirección de puertos)

```bash
bash install.sh   # elegir opción 2, pegar token del túnel
```

HTTPS público mediante tu dominio de Cloudflare Tunnel — sin configuración de router necesaria.

---

## Endpoints de la API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | HTML del panel |
| `/api/current` | GET | Último snapshot (contenedores + host + imágenes + anomalías) |
| `/api/history/{name}?hours=1` | GET | Series temporales de contenedores |
| `/api/history/host?hours=1` | GET | Series temporales del host |
| `/api/alerts?hours=24` | GET | Historial de alertas |
| `/api/session` | GET | Usuario actual, IP, conexiones activas |
| `/api/settings` | GET/POST | Configuración en tiempo de ejecución (max_connections) |
| `/api/change-password` | POST | Cambiar usuario/contraseña |
| `/api/health` | GET | Verificación de salud (sin autenticación) |

---

## Seguridad

- **Basic Auth** en todos los endpoints (excepto `/api/health`)
- **Limitación de tasa** — 5 intentos fallidos → 60s de bloqueo por IP
- **HTTPS** — Autofirmado o Cloudflare Tunnel
- **Límite de conexiones** — Máximo de usuarios simultáneos configurable
- **Montajes de solo lectura** — Docker socket, /sys, /proc todos montados en read-only
- **Sin acceso de escritura** — Solo monitoreo, sin control de contenedores

---

## Configuración manual

Si prefieres la configuración manual:

```bash
git clone https://github.com/deep-on/dockwatch.git
cd dockwatch

# Crear .env
cp .env.example .env
vi .env

# Generar certificado SSL (opcional)
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -subj "/CN=dockwatch"

# Iniciar
docker compose up -d --build
```

---

## Licencia

MIT License — ver [LICENSE](LICENSE)

**Atribución:** Las versiones modificadas o redistribuidas deben mantener el logo de DeepOn y el aviso "Powered by DeepOn Inc." en la interfaz.

---

<p align="center">
  <img src="app/static/logo.png" width="24" alt="DeepOn">
  Desarrollado por <a href="https://deep-on.com">DeepOn Inc.</a>
</p>
