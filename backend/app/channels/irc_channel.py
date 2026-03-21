import logging
import os
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseChannel, InboundMessage, OutboundMessage, get_channel_registry

logger = logging.getLogger(__name__)


class IRCChannel(BaseChannel):
    name = "IRC"
    platform_name = "irc"
    webhook_path = "irc/webhook"

    def __init__(self):
        self.server = os.getenv("IRC_SERVER", "")
        self.port = int(os.getenv("IRC_PORT", "6667"))
        self.channel = os.getenv("IRC_CHANNEL", "")
        self.nickname = os.getenv("IRC_NICKNAME", "qubot")
        self.use_ssl = os.getenv("IRC_USE_SSL", "false").lower() == "true"
        self._connected = False

    def is_configured(self) -> bool:
        return bool(self.server and self.channel and self.nickname)

    async def handle_webhook(self, request: Request, session: AsyncSession) -> dict:
        payload = await request.json()
        msg = InboundMessage(
            platform=self.platform_name,
            chat_id=payload.get("channel", self.channel),
            user_id=payload.get("user_id", "unknown"),
            user_name=payload.get("user", "Unknown"),
            text=payload.get("message", ""),
            raw=payload,
        )
        reply = await self._process_message(msg, session)
        return {"status": "processed", "reply": reply}

    async def send_message(self, msg: OutboundMessage) -> dict:
        logger.info(f"IRC message to {msg.chat_id}: {msg.text}")
        return {"status": "sent"}

    async def setup_webhook(self, base_url: str) -> dict:
        return {"status": "ready", "url": self._get_webhooks_full_url(base_url)}

    async def teardown_webhook(self) -> dict:
        return {"status": "removed"}


_instance = IRCChannel()
if _instance.is_configured():
    get_channel_registry().register(_instance)
