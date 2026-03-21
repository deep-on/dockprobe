FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY VERSION .
COPY app/ ./app/
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

RUN adduser --disabled-password --no-create-home --gecos "" appuser \
    && mkdir -p /data && chown appuser:appuser /data
USER appuser

EXPOSE 9090

ENTRYPOINT ["./entrypoint.sh"]
