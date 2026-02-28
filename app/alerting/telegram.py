from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app import config

logger = logging.getLogger(__name__)

# {alert_key: last_sent_timestamp}
_cooldowns: dict[str, float] = {}


async def send_alert(alert: dict[str, Any]) -> bool:
    """Send a Telegram alert with cooldown."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return False

    key = f"{alert['type']}:{alert['target']}"
    now = time.time()
    last = _cooldowns.get(key, 0)
    if now - last < config.ALERT_COOLDOWN_MINUTES * 60:
        return False

    text = f"🚨 *Docker Monitor Alert*\n\n{alert['msg']}"
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                _cooldowns[key] = now
                logger.info("Telegram alert sent: %s", key)
                return True
            else:
                logger.warning("Telegram API error %s: %s", resp.status_code, resp.text)
    except httpx.HTTPError as e:
        logger.warning("Telegram send failed: %s", e)
    return False
