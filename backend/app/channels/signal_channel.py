"""
Signal Channel - Send and receive messages via Signal Messenger.

Requires:
- signal-cli installed on the system
- Linked device or registered number

Usage:
1. Install signal-cli: https://github.com/AsamK/signal-cli
2. Link device: signal-cli link -n "Qubot"
3. Configure credentials
"""

import asyncio
import json
import subprocess
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.base import (
    BaseChannel,
    InboundMessage,
    OutboundMessage,
    get_channel_registry,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class SignalChannel(BaseChannel):
    """Signal messenger channel using signal-cli."""

    def __init__(self):
        self.signal_cli_path = os.getenv("SIGNAL_CLI_PATH", "signal-cli")
        self.phone_number = os.getenv("SIGNAL_PHONE_NUMBER", "")

    @property
    def name(self) -> str:
        return "signal"

    @property
    def platform_name(self) -> str:
        return "signal"

    @property
    def webhook_path(self) -> str:
        return "signal/webhook"

    def is_configured(self) -> bool:
        return bool(self.phone_number)

    async def initialize(self) -> None:
        await self._verify_signal_cli()

    async def _verify_signal_cli(self) -> None:
        """Verify signal-cli is installed."""
        try:
            result = subprocess.run(
                [self.signal_cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError("signal-cli not found")
            logger.info(f"Signal CLI version: {result.stdout.strip()}")
        except Exception as e:
            raise RuntimeError(f"signal-cli not available: {e}")

    async def handle_webhook(self, request: Request, session: AsyncSession) -> dict:
        """Handle incoming Signal message via webhook."""
        payload = await request.json()

        envelope = payload.get("envelope", {})
        if not envelope.get("dataMessage"):
            return {"status": "ignored"}

        msg_data = envelope["dataMessage"]
        sender = envelope.get("sourceNumber", envelope.get("source"))
        message_text = msg_data.get("message", "")
        timestamp = msg_data.get("timestamp")

        msg = InboundMessage(
            platform=self.platform_name,
            chat_id=sender or "unknown",
            user_id=sender or "unknown",
            user_name=sender or "Unknown",
            text=message_text,
            message_id=str(timestamp),
            raw=payload,
        )

        reply = await self._process_message(msg, session)
        return {"status": "processed", "reply": reply}

    async def send_message(self, msg: OutboundMessage) -> dict:
        """Send a message via Signal."""
        cmd = [
            self.signal_cli_path,
            "send",
            "-m",
            msg.text,
        ]

        if msg.chat_id.startswith("+"):
            cmd.append(msg.chat_id)
        else:
            cmd.extend(["--group", msg.chat_id])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return {"success": False, "error": result.stderr}

            return {
                "success": True,
                "recipient": msg.chat_id,
                "message": msg.text,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout sending message"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def setup_webhook(self, base_url: str) -> dict:
        """Signal uses subprocess polling mode."""
        logger.info("Signal uses signal-cli daemon mode")
        return {"status": "ready", "url": self._get_webhooks_full_url(base_url)}

    async def teardown_webhook(self) -> dict:
        return {"status": "removed"}


import os

_instance = SignalChannel()
if _instance.is_configured():
    get_channel_registry().register(_instance)
