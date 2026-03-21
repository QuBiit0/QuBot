"""
LINE Channel Plugin — Official LINE Messaging API integration

Supports:
- Reply to user messages
- Push messages to users
- Webhook verification

Env vars required:
    LINE_CHANNEL_ID       — LINE channel ID
    LINE_CHANNEL_SECRET   — LINE channel secret
    LINE_ACCESS_TOKEN     — Long-lived access token
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


class LINEChannel(BaseChannel):
    """LINE bot integration via Messaging API."""

    LINE_API = "https://api.line.me/v2/bot"

    @property
    def name(self) -> str:
        return "LINE"

    @property
    def platform_name(self) -> str:
        return "line"

    @property
    def webhook_path(self) -> str:
        return "line/webhook"

    def __init__(self):
        self.channel_id = os.getenv("LINE_CHANNEL_ID", "")
        self.channel_secret = os.getenv("LINE_CHANNEL_SECRET", "")
        self.access_token = os.getenv("LINE_ACCESS_TOKEN", "")
        self.reply_endpoint = f"{self.LINE_API}/message/reply"
        self.push_endpoint = f"{self.LINE_API}/message/push"
        self.profile_endpoint = f"{self.LINE_API}/profile"
        self._connected = False

    def is_configured(self) -> bool:
        return bool(self.channel_id and self.channel_secret and self.access_token)

    def _verify_webhook(self, request: Request, body: bytes) -> bool:
        """Verify LINE webhook signature."""
        signature = request.headers.get("x-line-signature", "")
        if not signature:
            return False

        hash_value = hmac.new(
            self.channel_secret.encode(), body, hashlib.sha256
        ).digest()
        expected = hash_value.hexdigest()

        return hmac.compare_digest(expected, signature)

    async def handle_webhook(self, request: Request, session: AsyncSession) -> dict:
        """Handle incoming LINE webhook events."""
        body_bytes = await request.body()

        if not self._verify_webhook(request, body_bytes):
            raise HTTPException(status_code=401, detail="Invalid LINE signature")

        payload = await request.json()
        events = payload.get("events", [])

        if not events:
            return {"status": "ok"}

        for event in events:
            event_type = event.get("type")

            if event_type == "follow":
                await self._handle_follow(event, session)
            elif event_type == "unfollow":
                await self._handle_unfollow(event, session)
            elif event_type == "message":
                await self._handle_message(event, session)

        return {"status": "ok"}

    async def _handle_follow(self, event: dict, session: AsyncSession) -> None:
        """Handle follow event (user added bot as friend)."""
        user_id = event.get("source", {}).get("userId", "")
        logger.info(f"[line] User followed: {user_id}")

    async def _handle_unfollow(self, event: dict, session: AsyncSession) -> None:
        """Handle unfollow event (user removed bot)."""
        user_id = event.get("source", {}).get("userId", "")
        logger.info(f"[line] User unfollowed: {user_id}")

    async def _handle_message(self, event: dict, session: AsyncSession) -> None:
        """Handle incoming message."""
        msg_type = event.get("message", {}).get("type", "")
        user_id = event.get("source", {}).get("userId", "")
        reply_token = event.get("replyToken", "")
        text = event.get("message", {}).get("text", "")

        if msg_type != "text" or not text:
            return

        msg = InboundMessage(
            platform=self.platform_name,
            chat_id=reply_token,
            user_id=user_id,
            user_name=await self._get_display_name(user_id) or "LINE User",
            text=text,
            raw=event,
        )

        reply_text = await self._process_message(msg, session)

        if reply_text:
            await self._send_reply(reply_token, reply_text)

    async def _get_display_name(self, user_id: str) -> str | None:
        """Get user display name from LINE API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.profile_endpoint}/{user_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("displayName")
        except Exception as e:
            logger.warning(f"[line] Failed to get user profile: {e}")
        return None

    async def _send_reply(self, reply_token: str, text: str) -> dict:
        """Send reply message using reply token."""
        payload = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "text",
                    "text": text[:500],
                }
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.reply_endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            return response.json()

    async def send_message(self, msg: OutboundMessage) -> dict:
        """Push message to a user (requires user ID as chat_id)."""
        if not msg.chat_id:
            return {"status": "error", "message": "No chat_id provided"}

        payload = {
            "to": msg.chat_id,
            "messages": [
                {
                    "type": "text",
                    "text": msg.text[:500],
                }
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.push_endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            result = response.json()
            if result.get("sent"):
                logger.info(f"[line] Message sent to {msg.chat_id}")
            return result

    async def setup_webhook(self, base_url: str) -> dict:
        """Setup webhook URL in LINE Developer Console."""
        webhook_url = self._get_webhooks_full_url(base_url)
        logger.info(f"[line] Webhook URL configured: {webhook_url}")
        return {
            "status": "manual_setup_required",
            "webhook_url": webhook_url,
            "instructions": (
                "1. Go to https://developers.line.biz/console/\n"
                "2. Select your channel → Messaging API\n"
                "3. Set Webhook URL to the URL above\n"
                "4. Disable auto-reply messages\n"
                "5. Enable webhook"
            ),
        }

    async def teardown_webhook(self) -> dict:
        return {"status": "removed"}


_instance = LINEChannel()
if _instance.is_configured():
    get_channel_registry().register(_instance)
