#!/usr/bin/env bash
set -e

# Docker Container Monitoring Dashboard - One-liner Installer
# Usage: curl -sSL https://raw.githubusercontent.com/YOUR_REPO/main/install.sh | bash

REPO="https://github.com/deep-on/dockwatch.git"
DIR="$HOME/dockwatch"
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

banner() {
  echo -e "${CYAN}${BOLD}"
  echo "  ╔═══════════════════════════════════════╗"
  echo "  ║   Docker Container Monitor Installer  ║"
  echo "  ╚═══════════════════════════════════════╝"
  echo -e "${NC}"
}

check_deps() {
  for cmd in docker git openssl; do
    if ! command -v "$cmd" &>/dev/null; then
      echo -e "${RED}Error: $cmd is required but not installed.${NC}" && exit 1
    fi
  done
  if ! docker compose version &>/dev/null; then
    echo -e "${RED}Error: docker compose (v2) is required.${NC}" && exit 1
  fi
}

prompt() {
  local var="$1" msg="$2" default="$3"
  if [ -n "$default" ]; then
    read -rp "$(echo -e "${GREEN}$msg${NC} [$default]: ")" val
    eval "$var=\"${val:-$default}\""
  else
    read -rp "$(echo -e "${GREEN}$msg${NC}: ")" val
    eval "$var=\"$val\""
  fi
}

prompt_secret() {
  local var="$1" msg="$2"
  read -rsp "$(echo -e "${GREEN}$msg${NC}: ")" val
  echo
  eval "$var=\"$val\""
}

# ─── Main ───────────────────────────────────────

banner
check_deps

echo -e "${BOLD}[1/4] Settings${NC}"

prompt AUTH_USER   "Dashboard username" "admin"
prompt_secret AUTH_PASS "Dashboard password"
if [ -z "$AUTH_PASS" ]; then
  AUTH_PASS=$(openssl rand -base64 12)
  echo -e "${YELLOW}  Generated password: ${BOLD}$AUTH_PASS${NC}"
fi

echo ""
prompt TG_TOKEN "Telegram Bot Token (leave empty to skip)" ""
prompt TG_CHAT  "Telegram Chat ID" ""

echo ""
echo -e "${BOLD}[2/4] Access method${NC}"
echo -e "  1) ${CYAN}Local only${NC}      - https://localhost:9090 (self-signed SSL)"
echo -e "  2) ${CYAN}Cloudflare Tunnel${NC} - public HTTPS URL, no port forwarding needed"
read -rp "$(echo -e "${GREEN}Choose [1/2]${NC}: ")" ACCESS_MODE
ACCESS_MODE="${ACCESS_MODE:-1}"

CF_TOKEN=""
if [ "$ACCESS_MODE" = "2" ]; then
  echo ""
  echo -e "${YELLOW}Cloudflare Tunnel setup:${NC}"
  echo "  1. Go to https://one.dash.cloudflare.com → Networks → Tunnels"
  echo "  2. Create a tunnel → copy the tunnel token"
  echo "  3. Set service URL to: http://monitor:9090"
  echo ""
  prompt CF_TOKEN "Cloudflare Tunnel Token" ""
fi

echo ""
echo -e "${BOLD}[3/4] Installing${NC}"

# Clone or update
if [ -d "$DIR" ]; then
  echo "  Updating existing installation..."
  cd "$DIR" && git pull --quiet 2>/dev/null || true
else
  echo "  Downloading..."
  git clone --quiet --depth 1 "$REPO" "$DIR" 2>/dev/null || {
    # If repo doesn't exist yet, create from local files
    mkdir -p "$DIR"
    echo -e "${YELLOW}  Note: Git clone failed. Using local setup mode.${NC}"
  }
fi
cd "$DIR"

# Write .env
cat > .env <<EOF
AUTH_USER=$AUTH_USER
AUTH_PASS=$AUTH_PASS
TELEGRAM_BOT_TOKEN=$TG_TOKEN
TELEGRAM_CHAT_ID=$TG_CHAT
CF_TUNNEL_TOKEN=$CF_TOKEN
EOF

# Generate self-signed cert if local mode
if [ "$ACCESS_MODE" = "1" ]; then
  if [ ! -f certs/cert.pem ]; then
    echo "  Generating SSL certificate..."
    mkdir -p certs
    openssl req -x509 -newkey rsa:2048 -nodes \
      -keyout certs/key.pem -out certs/cert.pem \
      -days 365 -subj "/CN=docker-monitor" \
      -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" 2>/dev/null
  fi
fi

echo ""
echo -e "${BOLD}[4/4] Starting${NC}"

if [ "$ACCESS_MODE" = "2" ] && [ -n "$CF_TOKEN" ]; then
  docker compose --profile tunnel up -d --build 2>&1 | grep -E "Started|Created|Built"
else
  docker compose up -d --build 2>&1 | grep -E "Started|Created|Built"
fi

# Wait for health
echo -n "  Waiting for startup"
for i in $(seq 1 15); do
  sleep 2
  echo -n "."
  SCHEME="https"
  [ ! -f certs/cert.pem ] && SCHEME="http"
  if curl -sk "$SCHEME://localhost:9090/api/health" &>/dev/null; then
    echo -e " ${GREEN}OK${NC}"
    break
  fi
  if [ "$i" = "15" ]; then
    echo -e " ${RED}timeout${NC}"
    echo "  Check: docker logs docker-monitor"
  fi
done

echo ""
echo -e "${CYAN}${BOLD}═══════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Installation complete!${NC}"
echo ""
if [ "$ACCESS_MODE" = "2" ] && [ -n "$CF_TOKEN" ]; then
  echo -e "  Dashboard: ${BOLD}your-tunnel-domain${NC} (check Cloudflare dashboard)"
else
  echo -e "  Dashboard: ${BOLD}https://localhost:9090${NC}"
fi
echo -e "  Username:  ${BOLD}$AUTH_USER${NC}"
echo -e "  Password:  ${BOLD}$AUTH_PASS${NC}"
echo ""
echo -e "  Config:    ${BOLD}$DIR/.env${NC}"
echo -e "  Logs:      docker logs -f docker-monitor"
echo -e "  Stop:      cd $DIR && docker compose down"
echo -e "${CYAN}${BOLD}═══════════════════════════════════════${NC}"
