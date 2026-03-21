"""
Mattermost Channel - Send and receive messages via Mattermost.
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


class MattermostChannel(BaseChannel):
    """Mattermost team communication platform."""

    def __init__(self):
        self.server_url = os.getenv("MATTERMOST_SERVER_URL", "")
        self.token = os.getenv("MATTERMOST_TOKEN", "")
        self.team = os.getenv("MATTERMOST_TEAM", "")

    @property
    def name(self) -> str:
        return "mattermost"

    @property
    def platform_name(self) -> str:
        return "mattermost"

    @property
    def webhook_path(self) -> str:
        return "mattermost/webhook"

    def is_configured(self) -> bool:
        return bool(self.server_url and self.token and self.team)

    async def initialize(self) -> None:
        pass

    async def handle_webhook(self, request: Request, session: AsyncSession) -> dict:
        """Handle incoming Mattermost message."""
        payload = await request.json()

        post = payload.get("post", {})
        content = post.get("message", "")
        channel_id = post.get("channel_id", "")
        user_id = post.get("user_id", "")

        if not content:
            return {"status": "ignored"}

        msg = InboundMessage(
            platform=self.platform_name,
            chat_id=channel_id,
            user_id=user_id,
            user_name=user_id,
            text=content,
            message_id=post.get("id", ""),
            raw=payload,
        )

        reply = await self._process_message(msg, session)
        return {"status": "processed", "reply": reply}

    async def send_message(self, msg: OutboundMessage) -> dict:
        """Send a message to Mattermost channel."""
        channel_id = msg.chat_id
        if not channel_id:
            return {"success": False, "error": "No channel_id provided"}

        url = f"{self.server_url}/api/v4/posts"
        payload = {"channel_id": channel_id, "message": msg.text}

        headers = {"Authorization": f"Bearer {self.token}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code in (200, 201):
                return {"success": True, "post_id": response.json()["id"]}
            return {"success": False, "error": response.text}

    async def _get_channel_id(self, channel_name: str) -> str:
        """Get channel ID by name."""
        url = f"{self.server_url}/api/v4/teams/name/{self.team}/channels/name/{channel_name}"
        headers = {"Authorization": f"Bearer {self.token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()["id"]
        raise ValueError(f"Channel not found: {channel_name}")

    async def setup_webhook(self, base_url: str) -> dict:
        """Register webhook for Mattermost."""
        return {"status": "ready", "url": self._get_webhooks_full_url(base_url)}

    async def teardown_webhook(self) -> dict:
        return {"status": "removed"}


_instance = MattermostChannel()
if _instance.is_configured():
    get_channel_registry().register(_instance)
