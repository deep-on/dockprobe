<p align="center">
  <img src="app/static/logo.png" width="80" alt="DockWatch">
</p>

<h1 align="center">DockWatch</h1>

<p align="center">
  <b>Painel leve de monitoramento Docker com detecção de anomalias e alertas Telegram</b><br>
  Um contêiner. Um comando. Visibilidade total.
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | <a href="README.de.md">Deutsch</a> | <a href="README.fr.md">Français</a> | <a href="README.es.md">Español</a> | <b>Português</b> | <a href="README.it.md">Italiano</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.12-green" alt="Python">
  <img src="https://img.shields.io/badge/docker-compose-blue" alt="Docker">
  <img src="https://img.shields.io/badge/dependencies-4_only-brightgreen" alt="Deps">
</p>

---

## O que é o DockWatch?

DockWatch é um painel de monitoramento Docker auto-hospedado que roda como um único contêiner. Ele coleta em tempo real métricas de CPU, memória, rede e disco de todos os seus contêineres e da máquina host — e exibe tudo em uma interface web limpa com tema escuro.

Quando algo dá errado, o DockWatch detecta automaticamente. Seis regras integradas de detecção de anomalias monitoram picos de CPU, estouro de memória, alertas de temperatura, pressão de disco, reinicializações inesperadas e surtos de rede. Os alertas são enviados instantaneamente via Telegram para que você possa reagir antes que os usuários percebam.

Não há agente para instalar em cada contêiner, nem banco de dados externo, nem configuração complexa. Basta montar o socket do Docker, executar um comando, e você terá visibilidade completa do seu ambiente Docker em `https://localhost:9090`. Precisa acessar de fora da sua rede? O suporte integrado ao Cloudflare Tunnel oferece HTTPS público seguro sem redirecionamento de portas.

---

## Início rápido

```bash
git clone https://github.com/deep-on/dockwatch.git && cd dockwatch && bash install.sh
```

É só isso. O instalador interativo configura a autenticação, alertas Telegram e HTTPS — depois abre `https://localhost:9090`.

> **Requisitos:** Docker (com Compose v2), Git, OpenSSL

---

## Pré-visualização do painel

<p align="center">
  <img src="docs/screenshots/dashboard-full.png" alt="Painel DockWatch" width="800">
</p>

---

## Funcionalidades

| Categoria | O que você obtém |
|-----------|-----------------|
| **Painel em tempo real** | Interface web escura, atualização automática a cada 10s, tabelas ordenáveis, gráficos Chart.js |
| **Monitoramento de contêineres** | CPU %, memória %, E/S de rede, E/S de bloco, contador de reinícios |
| **Monitoramento do host** | Temperatura CPU/GPU, uso de disco, média de carga |
| **Detecção de anomalias** | 6 regras — pico de CPU, estouro de memória, alta temperatura, disco cheio, reinício, pico de rede |
| **Alertas Telegram** | Notificação instantânea com cooldown de 30 min por tipo de alerta |
| **Segurança** | Basic Auth, limitação de taxa (5 falhas = 60s de bloqueio), HTTPS |
| **Gestão de sessões** | Rastreamento de conexões ativas, máx. conexões configurável, exibição de IP ao vivo |
| **Gestão de senhas** | Alterar usuário/senha pela interface do painel |
| **Interface de configurações** | Ajustar máx. conexões em tempo de execução pelo painel |
| **Modos de acesso** | SSL autoassinado (padrão) ou Cloudflare Tunnel (sem redirecionamento de portas) |
| **Leve** | 4 pacotes Python, arquivo HTML único, SQLite com retenção de 7 dias |

---

## Composição do painel

| Seção | Detalhes |
|-------|---------|
| Barra de sessão | Usuário conectado, IP, conexões ativas / limite máximo |
| Cartões do host | Temp CPU, temp GPU, disco %, média de carga |
| Tabela de contêineres | Ordenável por CPU/memória/rede, anomalias com código de cores |
| Gráficos (4) | Tendências de CPU e memória dos contêineres, temperatura e carga do host |
| Disco Docker | Imagens, cache de build, volumes, camadas RW dos contêineres |
| Histórico de alertas | Últimas 24h com timestamps |

---

## Regras de detecção de anomalias

| Regra | Condição | Ação |
|-------|----------|------|
| CPU do contêiner | >80% por 3 verificações consecutivas (30s) | Telegram + destaque vermelho |
| Memória do contêiner | >90% do limite | Alerta imediato |
| Temperatura CPU do host | >85°C | Alerta imediato |
| Disco do host | >90% de uso | Alerta imediato |
| Reinício do contêiner | restart_count incrementado | Alerta imediato |
| Pico de rede | RX aumento de 10x + >100MB | Alerta imediato |

Todos os limites são configuráveis via variáveis de ambiente.

---

## Arquitetura

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
│  │   ├── detector.py    (máquina de estados) │
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

**Dependências (apenas 4 pacotes):**
- `fastapi` — Framework web
- `uvicorn` — Servidor ASGI
- `aiodocker` — Cliente Docker API assíncrono
- `httpx` — Cliente HTTP assíncrono (API Telegram)

---

## Configuração

Todas as configurações via arquivo `.env`:

```env
# Autenticação (obrigatório)
AUTH_USER=admin
AUTH_PASS=your-password

# Alertas Telegram (opcional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Limites (opcional, valores padrão exibidos)
CPU_THRESHOLD=80
MEM_THRESHOLD=90

# Limite de conexões (opcional, 0 = ilimitado)
MAX_CONNECTIONS=3

# Cloudflare Tunnel (opcional)
CF_TUNNEL_TOKEN=your-tunnel-token
```

---

## Modos de acesso

### Opção 1: Rede local (SSL autoassinado) — padrão

```bash
bash install.sh   # escolher opção 1
```

Acesso via `https://localhost:9090` ou `https://<seu-ip>:9090`

Para acessar de outros dispositivos na mesma rede, use o IP LAN do servidor (ex: `https://192.168.1.100:9090`). Se necessário:
- Liberar a porta no firewall: `sudo ufw allow 9090/tcp`
- Aceitar o aviso de certificado autoassinado no navegador

> **Por que o aviso do navegador?** O DockWatch usa um certificado SSL autoassinado gerado durante a instalação. Como não foi emitido por uma Autoridade Certificadora (CA) confiável, o navegador exibe um aviso "Sua conexão não é particular". Isso é normal — clique em "Avançado" → "Prosseguir para o site". Para eliminar este aviso, use o Cloudflare Tunnel (Opção 3) que fornece automaticamente um certificado TLS confiável.

### Opção 2: Acesso remoto por redirecionamento de portas

Para acesso externo sem Cloudflare:

1. Redirecionar a porta 9090 no roteador para o IP LAN do servidor
2. Acessar via `https://<seu-ip-público>:9090`
3. Usar um serviço DDNS (No-IP, DuckDNS, etc.) se seu IP público mudar

> **Nota:** A porta fica diretamente exposta. Basic Auth + HTTPS estão ativados por padrão, mas recomenda-se o Cloudflare Tunnel (Opção 3) para maior segurança.

### Opção 3: Cloudflare Tunnel (recomendado para acesso remoto)

Sem redirecionamento de portas, sem alterações no firewall, certificado TLS válido — a forma mais fácil e segura de acessar de qualquer lugar.

```bash
bash install.sh   # escolher opção 2, colar token do túnel
```

**Passos de configuração:**
1. Criar uma conta gratuita no [Cloudflare Zero Trust](https://one.dash.cloudflare.com)
2. Ir em **Networks** > **Tunnels** > **Create a tunnel**
3. Nomear o túnel (ex: `dockwatch`) e copiar o token
4. Executar `bash install.sh` e escolher a opção Cloudflare Tunnel
5. Colar o token
6. No painel do Cloudflare, adicionar um **Public Hostname** apontando para `http://localhost:9090`
7. Acessar via `https://your-domain.com` com certificado TLS válido

---

## Endpoints da API

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | HTML do painel |
| `/api/current` | GET | Último snapshot (contêineres + host + imagens + anomalias) |
| `/api/history/{name}?hours=1` | GET | Séries temporais dos contêineres |
| `/api/history/host?hours=1` | GET | Séries temporais do host |
| `/api/alerts?hours=24` | GET | Histórico de alertas |
| `/api/session` | GET | Usuário atual, IP, conexões ativas |
| `/api/settings` | GET/POST | Configurações em tempo de execução (max_connections) |
| `/api/change-password` | POST | Alterar usuário/senha |
| `/api/health` | GET | Verificação de saúde (sem autenticação) |

---

## Segurança

- **Basic Auth** em todos os endpoints (exceto `/api/health`)
- **Limitação de taxa** — 5 tentativas falhas → 60s de bloqueio por IP
- **HTTPS** — Autoassinado ou Cloudflare Tunnel
- **Limite de conexões** — Máximo de usuários simultâneos configurável
- **Montagens somente leitura** — Docker socket, /sys, /proc todos montados em read-only
- **Sem acesso de escrita** — Apenas monitoramento, sem controle de contêineres

---

## Configuração manual

Se preferir a configuração manual:

```bash
git clone https://github.com/deep-on/dockwatch.git
cd dockwatch

# Criar .env
cp .env.example .env
vi .env

# Gerar certificado SSL (opcional)
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -subj "/CN=dockwatch"

# Iniciar
docker compose up -d --build
```

---

## Licença

MIT License — ver [LICENSE](LICENSE)

**Atribuição:** Versões modificadas ou redistribuídas devem manter o logo DeepOn e o aviso "Powered by DeepOn Inc." na interface.

---

<p align="center">
  <img src="app/static/logo.png" width="24" alt="DeepOn">
  Desenvolvido por <a href="https://deep-on.com">DeepOn Inc.</a>
</p>
