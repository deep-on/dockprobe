#!/bin/sh
# Match docker socket GID so appuser can read it
if [ -S /var/run/docker.sock ]; then
  SOCK_GID=$(stat -c '%g' /var/run/docker.sock)
  if ! getent group "$SOCK_GID" > /dev/null 2>&1; then
    addgroup --gid "$SOCK_GID" dockerhost 2>/dev/null
  fi
  SOCK_GROUP=$(getent group "$SOCK_GID" | cut -d: -f1)
  adduser appuser "$SOCK_GROUP" 2>/dev/null
fi

# Fix /data ownership (may be owned by root from previous runs)
chown -R appuser:appuser /data 2>/dev/null

# Start uvicorn as appuser
CMD="uvicorn app.main:app --host 0.0.0.0 --port 9090"
if [ -f /certs/cert.pem ] && [ -f /certs/key.pem ]; then
  exec su -s /bin/sh appuser -c "$CMD --ssl-keyfile /certs/key.pem --ssl-certfile /certs/cert.pem"
else
  echo "WARNING: No SSL certs found. Running in plain HTTP mode."
  echo "         Credentials will be transmitted in cleartext."
  echo "         This is only safe behind a reverse proxy (e.g. Cloudflare Tunnel)."
  exec su -s /bin/sh appuser -c "$CMD"
fi
