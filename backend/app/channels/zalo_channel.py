"""
Zalo Channel Plugin — Official Zalo OA API integration

Supports:
- Reply to user messages
- Send messages to users
- Webhook verification

Env vars required:
    ZALO_APP_ID          — Zalo App ID
    ZALO_APP_SECRET     — Zalo App Secret
    ZALO_ACCESS_TOKEN    — Long-lived access token
    ZALO_OA_ID          — Official Account ID
"""

import hashlib
import hmac
import logging
import os
from typing import Any

import httpx
from fastapi import Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseChannel, InboundMessage, OutboundMessage, get_channel_registry

logger = logging.getLogger(__name__)


class ZaloChannel(BaseChannel):
    """Zalo Official Account bot integration."""

    ZALO_API = "https://graph.zalo.me/v2.0"
    ZALO_OA_API = "https://openapi.zalo.me/v2.0"

    @property
    def name(self) -> str:
        return "Zalo"

    @property
    def platform_name(self) -> str:
        return "zalo"

    @property
    def webhook_path(self) -> str:
        return "zalo/webhook"

    def __init__(self):
        self.app_id = os.getenv("ZALO_APP_ID", "")
        self.app_secret = os.getenv("ZALO_APP_SECRET", "")
        self.access_token = os.getenv("ZALO_ACCESS_TOKEN", "")
        self.oa_id = os.getenv("ZALO_OA_ID", "")
        self.api_endpoint = f"{self.ZALO_API}"
        self.oa_endpoint = f"{self.ZALO_OA_API}"
        self._connected = False

    def is_configured(self) -> bool:
        return bool(self.app_id and self.app_secret and self.access_token)

    def _verify_webhook(self, request: Request, body: bytes) -> bool:
        """Verify Zalo webhook signature."""
        secret_key = self.app_secret.encode()
        signature = request.headers.get("x-zalo-signature", "")
        if not signature:
            return False

        expected = hmac.new(secret_key, body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def handle_webhook(self, request: Request, session: AsyncSession) -> dict:
        """Handle incoming Zalo webhook events."""
        body_bytes = await request.body()

        if not self._verify_webhook(request, body_bytes):
            raise HTTPException(status_code=401, detail="Invalid Zalo signature")

        payload = await request.json()
        event = payload.get("event_name")

        if event == "send message":
            await self._handle_message(payload.get("message", {}), session)
        elif event == "follow":
            await self._handle_follow(payload.get("follower"), session)
        elif event == "unfollow":
            await self._handle_unfollow(payload.get("follower"), session)

        return {"status": "ok"}

    async def _handle_follow(self, follower: dict, session: AsyncSession) -> None:
        """Handle follow event."""
        user_id = follower.get("openid", "")
        logger.info(f"[zalo] User followed: {user_id}")

    async def _handle_unfollow(self, follower: dict, session: AsyncSession) -> None:
        """Handle unfollow event."""
        user_id = follower.get("openid", "")
        logger.info(f"[zalo] User unfollowed: {user_id}")

    async def _handle_message(self, message: dict, session: AsyncSession) -> None:
        """Handle incoming message."""
        msg_type = message.get("type", "")
        user_id = message.get("sender", {}).get("id", "")
        text = message.get("text", "")

        if msg_type != "text" or not text:
            return

        msg = InboundMessage(
            platform=self.platform_name,
            chat_id=user_id,
            user_id=user_id,
            user_name="Zalo User",
            text=text,
            raw=message,
        )

        reply_text = await self._process_message(msg, session)

        if reply_text:
            await self.send_message(OutboundMessage(chat_id=user_id, text=reply_text))

    async def send_message(self, msg: OutboundMessage) -> dict:
        """Send message to Zalo user."""
        if not msg.chat_id:
            return {"status": "error", "message": "No chat_id provided"}

        payload = {
            "recipient": {"user_id": msg.chat_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "text",
                        "text": msg.text[:500],
                    },
                }
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.oa_endpoint}/oa/message/send",
                    json=payload,
                    headers={
                        "access_token": self.access_token,
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )
                result = response.json()
                if result.get("success"):
                    logger.info(f"[zalo] Message sent to {msg.chat_id}")
                return result
        except Exception as e:
            logger.error(f"[zalo] Failed to send message: {e}")
            return {"status": "error", "message": str(e)}

    async def setup_webhook(self, base_url: str) -> dict:
        """Setup webhook URL in Zalo Developer Console."""
        webhook_url = self._get_webhooks_full_url(base_url)
        logger.info(f"[zalo] Webhook URL: {webhook_url}")
        return {
            "status": "manual_setup_required",
            "webhook_url": webhook_url,
            "instructions": (
                "1. Go to https://developers.zalo.me/\n"
                "2. Select your app → Webhooks\n"
                "3. Set Webhook URL to the URL above\n"
                "4. Verify webhook with the verification token"
            ),
        }

    async def teardown_webhook(self) -> dict:
        return {"status": "removed"}


_instance = ZaloChannel()
if _instance.is_configured():
    get_channel_registry().register(_instance)
