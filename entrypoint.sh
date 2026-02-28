#!/bin/sh
# Start uvicorn with SSL if certs exist, otherwise plain HTTP (for tunnel mode)
if [ -f /certs/cert.pem ] && [ -f /certs/key.pem ]; then
  exec uvicorn app.main:app --host 0.0.0.0 --port 9090 \
    --ssl-keyfile /certs/key.pem --ssl-certfile /certs/cert.pem
else
  exec uvicorn app.main:app --host 0.0.0.0 --port 9090
fi
