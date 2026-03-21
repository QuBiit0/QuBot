"""
Feishu (Lark) Channel Plugin

Official Feishu/Lark Open Platform integration.

Env vars required:
    FEISHU_APP_ID      — Feishu App ID
    FEISHU_APP_SECRET  — Feishu App Secret
    FEISHU_BOT_NAME   — Bot display name
"""

import hashlib
import hmac
import logging
import os
import time
from typing import Any

import httpx
from fastapi import Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseChannel, InboundMessage, OutboundMessage, get_channel_registry

logger = logging.getLogger(__name__)


class FeishuChannel(BaseChannel):
    """Feishu/Lark Open Platform bot integration."""

    FEISHU_API = "https://open.feishu.cn/open-apis"

    @property
    def name(self) -> str:
        return "Feishu"

    @property
    def platform_name(self) -> str:
        return "feishu"

    @property
    def webhook_path(self) -> str:
        return "feishu/webhook"

    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID", "")
        self.app_secret = os.getenv("FEISHU_APP_SECRET", "")
        self.bot_name = os.getenv("FEISHU_BOT_NAME", "Qubot")
        self._access_token = ""
        self._token_expires = 0
        self._connected = False

    def is_configured(self) -> bool:
        return bool(self.app_id and self.app_secret)

    def _verify_signature(self, timestamp: str, sign: str, body: bytes) -> bool:
        """Verify Feishu request signature."""
        if not sign:
            return False
        try:
            ts = int(timestamp)
            if abs(time.time() - ts) > 300:
                return False
            sign_str = f"{timestamp}{body.decode()}"
            my_sign = base64.b64encode(
                hmac.new(
                    self.app_secret.encode(), sign_str.encode(), hashlib.sha256
                ).digest()
            ).decode()
            return hmac.compare_digest(my_sign, sign)
        except Exception:
            return False

    async def _get_access_token(self) -> str:
        """Get or refresh Feishu access token."""
        if time.time() < self._token_expires - 60:
            return self._access_token

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.FEISHU_API}/auth/v3/tenant_access_token/internal",
                    json={"app_id": self.app_id, "app_secret": self.app_secret},
                    timeout=10.0,
                )
                data = response.json()
                if data.get("code") == 0:
                    self._access_token = data["tenant_access_token"]
                    self._token_expires = time.time() + data.get("expire", 7200)
                    return self._access_token
        except Exception as e:
            logger.error(f"[feishu] Failed to get access token: {e}")
        return ""

    async def handle_webhook(self, request: Request, session: AsyncSession) -> dict:
        body_bytes = await request.body()

        timestamp = request.headers.get("X-Lark-Timestamp", "")
        sign = request.headers.get("X-Lark-Signature", "")
        if not self._verify_signature(timestamp, sign, body_bytes):
            raise HTTPException(status_code=401, detail="Invalid Feishu signature")

        payload = await request.json()
        event = payload.get("event", {})

        if event.get("message_type") == "text":
            sender = event.get("sender", {})
            text = event.get("message", {}).get("text", "").strip()

            if text:
                msg = InboundMessage(
                    platform=self.platform_name,
                    chat_id=event.get("chat_id", ""),
                    user_id=sender.get("sender_id", {}).get("open_id", ""),
                    user_name="Feishu User",
                    text=text,
                    raw=payload,
                )
                reply = await self._process_message(msg, session)
                if reply:
                    await self.send_message(
                        OutboundMessage(chat_id=event.get("chat_id", ""), text=reply)
                    )

        return {"status": "ok"}

    async def send_message(self, msg: OutboundMessage) -> dict:
        if not msg.chat_id:
            return {"status": "error", "message": "No chat_id provided"}

        token = await self._get_access_token()
        if not token:
            return {"status": "error", "message": "Failed to get access token"}

        payload = {
            "receive_id": msg.chat_id,
            "msg_type": "text",
            "content": {"text": msg.text[:500]},
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.FEISHU_API}/im/v1/messages?receive_id_type=chat_id",
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                )
                result = response.json()
                if result.get("code") == 0:
                    logger.info(f"[feishu] Message sent to {msg.chat_id}")
                return result
        except Exception as e:
            logger.error(f"[feishu] Failed to send: {e}")
            return {"status": "error", "message": str(e)}

    async def setup_webhook(self, base_url: str) -> dict:
        webhook_url = self._get_webhooks_full_url(base_url)
        logger.info(f"[feishu] Webhook URL: {webhook_url}")
        return {
            "status": "manual_setup_required",
            "webhook_url": webhook_url,
            "instructions": (
                "1. Go to https://open.feishu.cn/app\n"
                "2. Select your app → Event Subscriptions\n"
                "3. Set Request URL to the URL above\n"
                "4. Enable 'receive messages' permission"
            ),
        }

    async def teardown_webhook(self) -> dict:
        return {"status": "removed"}


import base64

_instance = FeishuChannel()
if _instance.is_configured():
    get_channel_registry().register(_instance)
