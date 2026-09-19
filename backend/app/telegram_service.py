"""
Telegram notification service to send snapshot photos and match details to a Telegram bot.
"""
import logging
import httpx
from datetime import datetime, timezone
from typing import List, Optional
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED
from .schemas import CelebrityMatch

logger = logging.getLogger(__name__)

async def send_snapshot_to_telegram(image_bytes: bytes) -> bool:
    """
    Sends solely the user's captured snapshot to the configured Telegram bot.
    Executed as an asynchronous background task.
    """
    if not TELEGRAM_ENABLED:
        logger.debug("Telegram notifications are disabled (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set).")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

    files = {
        "photo": ("snapshot.jpg", image_bytes, "image/jpeg"),
    }
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, data=data, files=files)
            if resp.status_code == 200:
                logger.info("Successfully sent user snapshot to Telegram bot.")
                return True
            else:
                logger.error("Failed to send snapshot to Telegram: status=%d, response=%s", resp.status_code, resp.text)
                return False
    except Exception as exc:
        logger.error("Telegram error sending snapshot: %s", exc)
        return False
