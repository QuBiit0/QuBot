import logging
import os
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseChannel, InboundMessage, OutboundMessage, get_channel_registry

logger = logging.getLogger(__name__)


class NostrChannel(BaseChannel):
    name = "Nostr"
    platform_name = "nostr"
    webhook_path = "nostr/webhook"

    def __init__(self):
        self.relays = os.getenv("NOSTR_RELAYS", "wss://relay.damus.io").split(",")
        self.private_key = os.getenv("NOSTR_PRIVATE_KEY", "")
        self.public_key = os.getenv("NOSTR_PUBLIC_KEY", "")
        self._connected = False

    def is_configured(self) -> bool:
        return bool(self.private_key and self.public_key)

    async def handle_webhook(self, request: Request, session: AsyncSession) -> dict:
        payload = await request.json()
        msg = InboundMessage(
            platform=self.platform_name,
            chat_id="nostr-dm",
            user_id=payload.get("pubkey", ""),
            user_name=payload.get("pubkey", "Unknown")[:8],
            text=payload.get("content", ""),
            raw=payload,
        )
        reply = await self._process_message(msg, session)
        return {"status": "ok", "reply": reply}

    async def send_message(self, msg: OutboundMessage) -> dict:
        logger.info(f"Nostr message: {msg.text}")
        return {"status": "sent"}

    async def setup_webhook(self, base_url: str) -> dict:
        return {"status": "ready", "relays": self.relays}

    async def teardown_webhook(self) -> dict:
        return {"status": "removed"}


_instance = NostrChannel()
if _instance.is_configured():
    get_channel_registry().register(_instance)
