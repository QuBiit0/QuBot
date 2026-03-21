"""
Matrix Channel - Send and receive messages via Matrix protocol.
"""

import os
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.channels.base import (
    BaseChannel,
    InboundMessage,
    OutboundMessage,
    get_channel_registry,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class MatrixChannel(BaseChannel):
    """Matrix.org protocol channel."""

    def __init__(self):
        self.homeserver = os.getenv("MATRIX_HOMESERVER", "https://matrix.org")
        self.user_id = os.getenv("MATRIX_USER_ID", "")
        self.access_token = os.getenv("MATRIX_ACCESS_TOKEN", "")
        self.device_id = os.getenv("MATRIX_DEVICE_ID", "Qubot")
        self.password = os.getenv("MATRIX_PASSWORD", "")

    @property
    def name(self) -> str:
        return "matrix"

    @property
    def platform_name(self) -> str:
        return "matrix"

    @property
    def webhook_path(self) -> str:
        return "matrix/webhook"

    def is_configured(self) -> bool:
        return bool(self.user_id and (self.access_token or self.password))

    async def initialize(self) -> None:
        if not self.access_token:
            await self._login()

    async def _login(self) -> None:
        url = f"{self.homeserver}/_matrix/client/r0/login"
        data = {
            "type": "m.login.password",
            "identifier": {"type": "m.id.user", "user": self.user_id},
            "password": self.password,
            "device_id": self.device_id,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, timeout=30)
            if response.status_code == 200:
                self.access_token = response.json()["access_token"]

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def handle_webhook(self, request: Request, session: AsyncSession) -> dict:
        """Handle incoming Matrix message."""
        payload = await request.json()

        event = payload.get("event", {})
        if event.get("type") != "m.room.message":
            return {"status": "ignored"}

        content = event.get("content", {})
        sender = event.get("sender", "")
        room_id = event.get("room_id", "")
        content_body = content.get("body", "")

        msg = InboundMessage(
            platform=self.platform_name,
            chat_id=room_id,
            user_id=sender,
            user_name=sender.split(":")[0].replace("@", "")
            if ":" in sender
            else sender,
            text=content_body,
            message_id=event.get("event_id", ""),
            raw=payload,
        )

        reply = await self._process_message(msg, session)
        return {"status": "processed", "reply": reply}

    async def send_message(self, msg: OutboundMessage) -> dict:
        """Send a message to Matrix room."""
        room_id = msg.chat_id
        if not room_id:
            return {"success": False, "error": "No room_id provided"}

        url = f"{self.homeserver}/_matrix/client/r0/rooms/{room_id}/send/m.room.message"
        payload = {"msgtype": "m.text", "body": msg.text}

        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                headers=self._headers(),
                json=payload,
                params={"txnId": str(UUID())},
                timeout=30,
            )
            if response.status_code in (200, 201):
                return {"success": True, "room_id": room_id}
            return {"success": False, "error": response.text}

    async def setup_webhook(self, base_url: str) -> dict:
        """Register webhook for Matrix."""
        return {"status": "ready", "url": self._get_webhooks_full_url(base_url)}

    async def teardown_webhook(self) -> dict:
        return {"status": "removed"}


_instance = MatrixChannel()
if _instance.is_configured():
    get_channel_registry().register(_instance)
