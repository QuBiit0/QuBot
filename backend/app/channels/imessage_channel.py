"""
iMessage Channel - Send and receive messages via iMessage on Mac.

Requires:
- Mac computer with iMessage configured
- BlueBubbles server (recommended) or AppleScript

Usage:
1. Set up BlueBubbles server on Mac
   OR
2. Enable "Remote Apple Events" in System Preferences > Sharing
3. Configure Mac credentials
"""

import os
import subprocess
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


class IMessageChannel(BaseChannel):
    """iMessage channel using BlueBubbles or AppleScript on Mac."""

    def __init__(self):
        self.mac_address = os.getenv("IMESSAGE_MAC_ADDRESS", "")
        self.mac_username = os.getenv("IMESSAGE_MAC_USERNAME", "")
        self.bluebubbles_url = os.getenv("BLUEBUBBLES_URL", "")
        self.bluebubbles_password = os.getenv("BLUEBUBBLES_PASSWORD", "")
        self._use_bluebubbles = bool(self.bluebubbles_url)

    @property
    def name(self) -> str:
        return "imessage"

    @property
    def platform_name(self) -> str:
        return "imessage"

    @property
    def webhook_path(self) -> str:
        return "imessage/webhook"

    def is_configured(self) -> bool:
        return bool(self.bluebubbles_url or (self.mac_address and self.mac_username))

    async def initialize(self) -> None:
        if self._use_bluebubbles:
            await self._test_bluebubbles()
        else:
            await self._test_applescript()

    async def _test_bluebubbles(self) -> None:
        """Test BlueBubbles connection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.bluebubbles_url}/api/v1/status",
                    headers={"Authorization": f"Bearer {self.bluebubbles_password}"},
                    timeout=5,
                )
                if response.status_code != 200:
                    raise RuntimeError("BlueBubbles not available")
                logger.info("BlueBubbles connected")
        except Exception as e:
            raise RuntimeError(f"BlueBubbles connection failed: {e}")

    async def _test_applescript(self) -> None:
        """Test AppleScript availability."""
        if not self.mac_address:
            raise RuntimeError("Mac address required for AppleScript")
        logger.warning("Using AppleScript - less reliable than BlueBubbles")

    async def handle_webhook(self, request: Request, session: AsyncSession) -> dict:
        """Handle incoming iMessage."""
        payload = await request.json()

        sender = payload.get("sender", {}).get("address", "")
        content = payload.get("text", "")
        chat_id = payload.get("chatId", "")

        if not content:
            return {"status": "ignored"}

        msg = InboundMessage(
            platform=self.platform_name,
            chat_id=chat_id or sender,
            user_id=sender,
            user_name=sender,
            text=content,
            message_id=payload.get("guid", ""),
            raw=payload,
        )

        reply = await self._process_message(msg, session)
        return {"status": "processed", "reply": reply}

    async def send_message(self, msg: OutboundMessage) -> dict:
        """Send a message via iMessage."""
        if self._use_bluebubbles:
            return await self._send_bluebubbles(msg.chat_id, msg.text)
        else:
            return await self._send_applescript(msg.chat_id, msg.text)

    async def _send_bluebubbles(self, recipient: str, message: str) -> dict:
        """Send via BlueBubbles API."""
        headers = {
            "Authorization": f"Bearer {self.bluebubbles_password}",
            "Content-Type": "application/json",
        }

        payload = {
            "message": message,
            "recipient": recipient,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.bluebubbles_url}/api/v1/message/{recipient}",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )

                if response.status_code not in (200, 201):
                    return {"success": False, "error": response.text}

                return {
                    "success": True,
                    "recipient": recipient,
                    "message_id": response.json().get("id"),
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _send_applescript(self, recipient: str, message: str) -> dict:
        """Send via AppleScript over SSH."""
        if not self.mac_address or not self.mac_username:
            return {"success": False, "error": "Mac credentials required"}

        script = f'''
        tell application "Messages"
            set targetService to service "iMessage"
            set targetBuddy to buddy "{recipient}" of targetService
            send "{message.replace('"', '\\"')}" to targetBuddy
        end tell
        '''

        cmd = [
            "ssh",
            f"{self.mac_username}@{self.mac_address}",
            f"osascript -e '{script}'",
        ]

        try:
            result = subprocess.run(
                " ".join(cmd),
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr or "AppleScript failed",
                }

            return {"success": True, "recipient": recipient}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout sending message"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def setup_webhook(self, base_url: str) -> dict:
        """Register webhook for incoming messages."""
        if self._use_bluebubbles:
            return {"status": "ready", "url": self._get_webhooks_full_url(base_url)}
        logger.warning("AppleScript mode doesn't support webhooks")
        return {"status": "unsupported"}

    async def teardown_webhook(self) -> dict:
        return {"status": "removed"}


_instance = IMessageChannel()
if _instance.is_configured():
    get_channel_registry().register(_instance)
