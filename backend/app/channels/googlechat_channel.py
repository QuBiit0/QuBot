"""
Google Chat Channel - Send and receive messages via Google Chat.

Requires:
- Google Cloud Project
- Google Chat API enabled
- Service account credentials (JSON)

Usage:
1. Create project at console.cloud.google.com
2. Enable Google Chat API
3. Create service account and download JSON credentials
4. Configure bot in Google Chat
"""

import json
import os
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


class GoogleChatChannel(BaseChannel):
    """Google Chat channel using Google Cloud."""

    def __init__(self):
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "")
        self._access_token: str | None = None
        self._project_id: str | None = None

    @property
    def name(self) -> str:
        return "google_chat"

    @property
    def platform_name(self) -> str:
        return "google_chat"

    @property
    def webhook_path(self) -> str:
        return "googlechat/webhook"

    def is_configured(self) -> bool:
        return bool(self.credentials_path)

    async def initialize(self) -> None:
        await self._load_credentials()

    async def _load_credentials(self) -> None:
        """Load and validate Google credentials."""
        if self.credentials_path:
            try:
                with open(self.credentials_path) as f:
                    creds = json.load(f)
                    self._project_id = creds.get("project_id")
            except FileNotFoundError:
                logger.warning(f"Credentials file not found: {self.credentials_path}")
                self._project_id = None
        else:
            self._project_id = None

    async def _get_access_token(self) -> str:
        """Get Google OAuth access token."""
        if self._access_token:
            return self._access_token

        if not self.credentials_path:
            raise RuntimeError("Google Chat credentials not configured")

        import google.auth
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=["https://www.googleapis.com/auth/chat.bot"],
        )

        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        self._access_token = credentials.token

        return self._access_token

    async def handle_webhook(self, request: Request, session: AsyncSession) -> dict:
        """Handle incoming Google Chat message."""
        payload = await request.json()

        space = payload.get("space", {})
        user = payload.get("user", {})
        message_data = payload.get("message", {})
        content = message_data.get("text", "")

        if not content:
            return {"status": "ignored"}

        msg = InboundMessage(
            platform=self.platform_name,
            chat_id=space.get("name", ""),
            user_id=user.get("name", ""),
            user_name=user.get("displayName", "Unknown"),
            text=content,
            message_id=payload.get("name", ""),
            raw=payload,
        )

        reply = await self._process_message(msg, session)
        return {"status": "processed", "reply": reply}

    async def send_message(self, msg: OutboundMessage) -> dict:
        """Send a message to a Google Chat space."""
        token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {
            "text": msg.text,
        }

        url = f"https://chat.googleapis.com/v1/spaces/{msg.chat_id}/messages"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code not in (200, 201):
                return {"success": False, "error": response.text}

            data = response.json()
            return {
                "success": True,
                "message_id": data.get("name"),
                "thread": data.get("thread", {}).get("name"),
            }

    async def setup_webhook(self, base_url: str) -> dict:
        """Register webhook for Google Chat."""
        full_url = self._get_webhooks_full_url(base_url)
        return {"status": "ready", "url": full_url}

    async def teardown_webhook(self) -> dict:
        return {"status": "removed"}


_instance = GoogleChatChannel()
if _instance.is_configured():
    get_channel_registry().register(_instance)
