FROM python:3.12-slim

LABEL org.opencontainers.image.title="DockProbe" \
      org.opencontainers.image.description="Lightweight Docker monitoring dashboard with anomaly detection & Telegram alerts" \
      org.opencontainers.image.url="https://github.com/deep-on/dockprobe" \
      org.opencontainers.image.source="https://github.com/deep-on/dockprobe" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.vendor="DeepOn Inc."

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY VERSION .
COPY LICENSE NOTICE ./
COPY app/ ./app/
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh && chmod -R a+r app/

RUN adduser --disabled-password --no-create-home --gecos "" appuser \
    && mkdir -p /data && chown appuser:appuser /data

EXPOSE 9090

ENTRYPOINT ["./entrypoint.sh"]
