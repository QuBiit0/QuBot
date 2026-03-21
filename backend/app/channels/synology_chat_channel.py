"""
Synology Chat Channel Plugin

Receives messages from Synology Chat server webhooks.
Sends responses back to Synology Chat rooms.

Env vars required:
    SYNOLOGY_SERVER_URL    — Synology Chat server URL (e.g., https://chat.synology.com)
    SYNOLOGY_PLUGIN_TOKEN  — Plugin token from Synology Chat
    SYNOLOGY_ROOM_ID      — Room ID to post to (optional)
"""

import logging
import os

import httpx
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseChannel, InboundMessage, OutboundMessage, get_channel_registry

logger = logging.getLogger(__name__)


class SynologyChatChannel(BaseChannel):
    """Synology Chat integration via webhooks."""

    @property
    def name(self) -> str:
        return "Synology Chat"

    @property
    def platform_name(self) -> str:
        return "synology_chat"

    @property
    def webhook_path(self) -> str:
        return "synology/webhook"

    def __init__(self):
        self.server_url = os.getenv("SYNOLOGY_SERVER_URL", "").rstrip("/")
        self.plugin_token = os.getenv("SYNOLOGY_PLUGIN_TOKEN", "")
        self.room_id = os.getenv("SYNOLOGY_ROOM_ID", "")
        self._connected = False

    def is_configured(self) -> bool:
        return bool(self.server_url and self.plugin_token)

    async def handle_webhook(self, request: Request, session: AsyncSession) -> dict:
        payload = await request.json()

        user_id = payload.get("user_id", "unknown")
        user_name = payload.get("user_name", payload.get("user", "Unknown User"))
        text = payload.get("text", "").strip()

        if not text:
            return {"status": "ok"}

        room_id = payload.get("room_id", self.room_id)

        msg = InboundMessage(
            platform=self.platform_name,
            chat_id=room_id,
            user_id=str(user_id),
            user_name=str(user_name),
            text=text,
            raw=payload,
        )

        reply_text = await self._process_message(msg, session)

        if reply_text and room_id:
            await self.send_message(OutboundMessage(chat_id=room_id, text=reply_text))

        return {"status": "ok"}

    async def send_message(self, msg: OutboundMessage) -> dict:
        if not msg.chat_id:
            return {"status": "error", "message": "No room_id provided"}

        payload = {
            "room_id": msg.chat_id,
            "text": msg.text[:500],
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.server_url}/api/room/send_message",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.plugin_token}",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )
                result = response.json()
                if result.get("success"):
                    logger.info(f"[synology] Message sent to room {msg.chat_id}")
                return result
        except Exception as e:
            logger.error(f"[synology] Failed to send message: {e}")
            return {"status": "error", "message": str(e)}

    async def setup_webhook(self, base_url: str) -> dict:
        webhook_url = self._get_webhooks_full_url(base_url)
        logger.info(f"[synology] Webhook URL: {webhook_url}")
        return {
            "status": "manual_setup_required",
            "webhook_url": webhook_url,
            "instructions": (
                "1. Go to Synology Chat Server → Settings → Plugins\n"
                "2. Create webhook with the URL above\n"
                "3. Configure which rooms trigger the webhook"
            ),
        }

    async def teardown_webhook(self) -> dict:
        return {"status": "removed"}


_instance = SynologyChatChannel()
if _instance.is_configured():
    get_channel_registry().register(_instance)
