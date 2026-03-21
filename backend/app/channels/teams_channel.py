"""
Microsoft Teams Channel - Send and receive messages via Microsoft Teams.

Requires:
- Azure AD App Registration
- Bot Framework bot
- ngrok for local development

Usage:
1. Create Azure AD App at portal.azure.com
2. Add Microsoft Teams channel
3. Configure ngrok: ngrok http 8000
4. Set webhook URL
"""

import asyncio
import hmac
import hashlib
import time
from typing import Any

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


class MicrosoftTeamsChannel(BaseChannel):
    """Microsoft Teams channel using Bot Framework."""

    def __init__(self):
        self.app_id = os.getenv("TEAMS_APP_ID", "")
        self.app_password = os.getenv("TEAMS_APP_PASSWORD", "")
        self.tenant_id = os.getenv("TEAMS_TENANT_ID", "")
        self.service_url = "https://smba.trafficmanager.net/teams/"
        self._access_token: str | None = None
        self._token_expires: float = 0

    @property
    def name(self) -> str:
        return "microsoft_teams"

    @property
    def platform_name(self) -> str:
        return "microsoft_teams"

    @property
    def webhook_path(self) -> str:
        return "teams/webhook"

    def is_configured(self) -> bool:
        return bool(self.app_id and self.app_password)

    async def initialize(self) -> None:
        await self._get_access_token()

    async def _get_access_token(self) -> str:
        """Get Microsoft Graph access token."""
        if self._access_token and time.time() < self._token_expires - 60:
            return self._access_token

        token_url = (
            f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        )

        data = {
            "grant_type": "client_credentials",
            "client_id": self.app_id,
            "client_secret": self.app_password,
            "scope": "https://api.botframework.com/.default",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)

            if response.status_code != 200:
                raise RuntimeError(f"Failed to get Teams token: {response.text}")

            token_data = response.json()
            self._access_token = token_data["access_token"]
            self._token_expires = time.time() + token_data["expires_in"]

        return self._access_token

    async def handle_webhook(self, request: Request, session: AsyncSession) -> dict:
        """Handle incoming Teams message."""
        payload = await request.json()

        channel_data = payload.get("channelData", {})
        conversation = payload.get("conversation", {})

        sender = payload.get("from", {})
        content = payload.get("text", "")

        if not content:
            return {"status": "ignored"}

        msg = InboundMessage(
            platform=self.platform_name,
            chat_id=conversation.get("id", ""),
            user_id=sender.get("aadObjectId", ""),
            user_name=sender.get("name", "Unknown"),
            text=content,
            message_id=payload.get("id", ""),
            raw=payload,
        )

        reply = await self._process_message(msg, session)
        return {"status": "processed", "reply": reply}

    async def send_message(self, msg: OutboundMessage) -> dict:
        """Send a message via Teams."""
        token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {
            "type": "message",
            "text": msg.text,
        }

        url = f"{self.service_url}v3/conversations/{msg.chat_id}/activities"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code not in (200, 201):
                return {"success": False, "error": response.text}

            return {
                "success": True,
                "recipient": msg.chat_id,
                "activity_id": response.json().get("id"),
            }

    async def setup_webhook(self, base_url: str) -> dict:
        """Register Teams webhook endpoint."""
        full_url = self._get_webhooks_full_url(base_url)
        return {"status": "ready", "url": full_url}

    async def teardown_webhook(self) -> dict:
        return {"status": "removed"}


import os

_instance = MicrosoftTeamsChannel()
if _instance.is_configured():
    get_channel_registry().register(_instance)
