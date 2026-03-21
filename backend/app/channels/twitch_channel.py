import logging
import os
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseChannel, InboundMessage, OutboundMessage, get_channel_registry

logger = logging.getLogger(__name__)


class TwitchChannel(BaseChannel):
    name = "Twitch"
    platform_name = "twitch"
    webhook_path = "twitch/webhook"

    def __init__(self):
        self.client_id = os.getenv("TWITCH_CLIENT_ID", "")
        self.client_secret = os.getenv("TWITCH_CLIENT_SECRET", "")
        self.bot_nickname = os.getenv("TWITCH_BOT_NICKNAME", "qubot")
        self.channel = os.getenv("TWITCH_CHANNEL", "")
        self.access_token = None
        self._connected = False

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.channel)

    async def handle_webhook(self, request: Request, session: AsyncSession) -> dict:
        payload = await request.json()
        msg = InboundMessage(
            platform=self.platform_name,
            chat_id=self.channel,
            user_id=payload.get("user_id", ""),
            user_name=payload.get("display_name", "Unknown"),
            text=payload.get("message", ""),
            raw=payload,
        )
        reply = await self._process_message(msg, session)
        return {"status": "ok", "reply": reply}

    async def send_message(self, msg: OutboundMessage) -> dict:
        logger.info(f"Twitch message in {msg.chat_id}: {msg.text}")
        return {"status": "sent"}

    async def setup_webhook(self, base_url: str) -> dict:
        return {"status": "ready", "url": self._get_webhooks_full_url(base_url)}

    async def teardown_webhook(self) -> dict:
        return {"status": "removed"}


_instance = TwitchChannel()
if _instance.is_configured():
    get_channel_registry().register(_instance)
