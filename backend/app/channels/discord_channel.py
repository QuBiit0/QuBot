"""
Discord Channel Plugin — Slash-command & regular message support via the Discord Gateway.

Uses discord-py-interactions (nextcord/py-cord) in gateway mode for development
and discord.py webhooks for simplified webhook-only deployments.

For production: use the Discord Interactions Endpoint (HTTP-based, no persistent connection).

Env vars required:
    DISCORD_BOT_TOKEN        — Bot token from Discord Dev Portal
    DISCORD_APPLICATION_ID   — Application ID
    DISCORD_PUBLIC_KEY       — Ed25519 public key for request verification
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time

import httpx
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseChannel, InboundMessage, OutboundMessage, get_channel_registry

logger = logging.getLogger(__name__)


class DiscordChannel(BaseChannel):
    """
    Discord bot integration.

    Supports:
    - Slash commands via Interactions Endpoint (HTTP webhook mode)
    - Regular DM and guild message events via MESSAGE_CREATE (optional Gateway)
    - Ed25519 signature verification for security
    """

    DISCORD_API = "https://discord.com/api/v10"

    def __init__(self):
        self._bot_token = os.getenv("DISCORD_BOT_TOKEN", "")
        self._app_id = os.getenv("DISCORD_APPLICATION_ID", "")
        self._public_key = os.getenv("DISCORD_PUBLIC_KEY", "")

    @property
    def name(self) -> str:
        return "Discord"

    @property
    def platform_name(self) -> str:
        return "discord"

    @property
    def webhook_path(self) -> str:
        return "discord/webhook"

    def is_configured(self) -> bool:
        return bool(self._bot_token and self._app_id and self._public_key)

    # ── Security ─────────────────────────────────────────────────────────────

    def _verify_signature(self, signature: str, timestamp: str, body: bytes) -> bool:
        """Verify Discord Ed25519 request signature."""
        try:
            from nacl.signing import VerifyKey
            from nacl.exceptions import BadSignatureError

            verify_key = VerifyKey(bytes.fromhex(self._public_key))
            verify_key.verify(
                (timestamp + body.decode()).encode(),
                bytes.fromhex(signature),
            )
            return True
        except Exception as e:
            logger.warning(f"[discord] Signature verification failed: {e}")
            return False

    # ── Webhook handler ───────────────────────────────────────────────────────

    async def handle_webhook(
        self,
        request: Request,
        session: AsyncSession,
    ) -> dict:
        """Handle Discord Interactions Endpoint POST."""
        body = await request.body()

        # Verify signature
        signature = request.headers.get("X-Signature-Ed25519", "")
        timestamp = request.headers.get("X-Signature-Timestamp", "")

        if not self._verify_signature(signature, timestamp, body):
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Invalid request signature")

        payload = await request.json()
        interaction_type = payload.get("type")

        # Type 1 = PING (Discord verification)
        if interaction_type == 1:
            return {"type": 1}

        # Type 2 = APPLICATION_COMMAND (slash command)
        if interaction_type == 2:
            return await self._handle_slash_command(payload, session)

        # Type 3 = MESSAGE_COMPONENT
        if interaction_type == 3:
            return {"type": 6}  # Deferred update

        return {"type": 6}

    async def _handle_slash_command(self, payload: dict, session: AsyncSession) -> dict:
        """Handle /ask or /qubot slash command."""
        data = payload.get("data", {})
        command_name = data.get("name", "")
        options = {o["name"]: o["value"] for o in data.get("options", [])}

        user = payload.get("member", {}).get("user") or payload.get("user", {})
        chat_id = payload.get("channel_id", "")
        guild_id = payload.get("guild_id", "")

        user_text = options.get("message", options.get("text", command_name))
        user_id = user.get("id", "unknown")
        user_name = user.get("username", "User")

        msg = InboundMessage(
            platform=self.platform_name,
            chat_id=chat_id or guild_id,
            user_id=user_id,
            user_name=user_name,
            text=user_text,
            is_command=True,
            command=command_name,
            command_args=user_text,
            raw=payload,
        )

        # Return deferred response (we'll send a followup)
        reply = await self._process_message(msg, session)

        return {
            "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
            "data": {
                "content": reply[:2000],  # Discord limit
            },
        }

    # ── Send message ──────────────────────────────────────────────────────────

    async def send_message(self, msg: OutboundMessage) -> dict:
        """Send a message to a Discord channel."""
        url = f"{self.DISCORD_API}/channels/{msg.chat_id}/messages"

        payload = {
            "content": msg.text[:2000],
        }
        if msg.reply_to_id:
            payload["message_reference"] = {"message_id": msg.reply_to_id}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bot {self._bot_token}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            return response.json()

    # ── Webhook management ────────────────────────────────────────────────────

    async def setup_webhook(self, base_url: str) -> dict:
        """Register the interactions endpoint with Discord."""
        full_url = self._get_webhooks_full_url(base_url)
        logger.info(f"[discord] Interactions endpoint: {full_url}")

        # Discord doesn't have a REST API to set the interactions endpoint.
        # It must be set manually in the Developer Portal.
        return {
            "status": "manual_setup_required",
            "url": full_url,
            "instructions": (
                "1. Go to https://discord.com/developers/applications\n"
                "2. Select your application\n"
                "3. Set 'Interactions Endpoint URL' to the URL above\n"
                "4. Invite the bot with /invite link"
            ),
        }

    async def teardown_webhook(self) -> dict:
        return {"status": "manual_removal_required"}

    # ── Bot registration helper ───────────────────────────────────────────────

    async def register_slash_commands(self) -> dict:
        """Register /ask and /help slash commands globally."""
        commands = [
            {
                "name": "ask",
                "description": "Ask Qubot to complete a task",
                "options": [
                    {
                        "name": "message",
                        "description": "What do you need help with?",
                        "type": 3,  # STRING
                        "required": True,
                    }
                ],
            },
            {
                "name": "status",
                "description": "Check the status of your tasks",
            },
        ]

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.DISCORD_API}/applications/{self._app_id}/commands",
                json=commands,
                headers={
                    "Authorization": f"Bot {self._bot_token}",
                    "Content-Type": "application/json",
                },
                timeout=15.0,
            )
            return response.json()


# Self-register on module import
_instance = DiscordChannel()
get_channel_registry().register(_instance)
