"""
Slack Channel Plugin — Events API + slash commands via signed requests.

Protocol: Slack sends HTTP POST events to a webhook. We verify with HMAC-SHA256.
Bot can also send messages via the Web API (chat.postMessage).

Env vars required:
    SLACK_BOT_TOKEN        — xoxb-... (Bot User OAuth Token)
    SLACK_SIGNING_SECRET   — For request verification
    SLACK_APP_TOKEN        — xapp-... (Socket Mode, optional)
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


class SlackChannel(BaseChannel):
    """
    Slack bot integration via Events API.

    Supports:
    - HMAC-SHA256 request signature verification
    - message.im (DMs), app_mention events
    - Slash commands (/ask, /qubot)
    - URL verification challenge
    """

    SLACK_API = "https://slack.com/api"

    def __init__(self):
        self._bot_token = os.getenv("SLACK_BOT_TOKEN", "")
        self._signing_secret = os.getenv("SLACK_SIGNING_SECRET", "")

    @property
    def name(self) -> str:
        return "Slack"

    @property
    def platform_name(self) -> str:
        return "slack"

    @property
    def webhook_path(self) -> str:
        return "slack/webhook"

    def is_configured(self) -> bool:
        return bool(self._bot_token and self._signing_secret)

    # ── Security ─────────────────────────────────────────────────────────────

    def _verify_signature(self, request_ts: str, body: bytes, signature: str) -> bool:
        """Verify Slack HMAC-SHA256 signature."""
        try:
            ts = int(request_ts)
            if abs(time.time() - ts) > 300:  # Replay attack window: 5 min
                return False

            sig_base = f"v0:{request_ts}:{body.decode()}"
            expected = "v0=" + hmac.new(
                self._signing_secret.encode(),
                sig_base.encode(),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.warning(f"[slack] Signature verification failed: {e}")
            return False

    # ── Webhook handler ───────────────────────────────────────────────────────

    async def handle_webhook(
        self,
        request: Request,
        session: AsyncSession,
    ) -> dict:
        body_bytes = await request.body()

        # Verify signature
        ts = request.headers.get("X-Slack-Request-Timestamp", "")
        sig = request.headers.get("X-Slack-Signature", "")
        if not self._verify_signature(ts, body_bytes, sig):
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Invalid Slack signature")

        content_type = request.headers.get("content-type", "")

        # Handle slash commands (form-encoded)
        if "application/x-www-form-urlencoded" in content_type:
            from urllib.parse import parse_qs
            params = parse_qs(body_bytes.decode())
            return await self._handle_slash_command(params, session)

        # Handle Events API (JSON)
        payload = await request.json()
        event_type = payload.get("type")

        # URL verification challenge
        if event_type == "url_verification":
            return {"challenge": payload.get("challenge")}

        # Event callback
        if event_type == "event_callback":
            event = payload.get("event", {})
            return await self._handle_event(event, session)

        return {"ok": True}

    async def _handle_slash_command(self, params: dict, session: AsyncSession) -> dict:
        """Handle /ask or /qubot slash commands."""
        text = params.get("text", [""])[0].strip()
        user_id = params.get("user_id", ["unknown"])[0]
        user_name = params.get("user_name", ["user"])[0]
        channel_id = params.get("channel_id", [""])[0]
        command = params.get("command", ["/ask"])[0].lstrip("/")

        msg = InboundMessage(
            platform=self.platform_name,
            chat_id=channel_id,
            user_id=user_id,
            user_name=user_name,
            text=text,
            is_command=True,
            command=command,
            command_args=text,
            raw=dict(params),
        )

        reply = await self._process_message(msg, session)
        return {"text": reply, "response_type": "in_channel"}

    async def _handle_event(self, event: dict, session: AsyncSession) -> dict:
        """
        Handle message events:
          - message.im   → Direct Message with bot
          - app_mention  → Bot @mentioned in a channel
        """
        event_type = event.get("type", "")
        subtype = event.get("subtype")

        # Ignore bot's own messages & system subtypes
        if subtype or event.get("bot_id"):
            return {"ok": True}

        if event_type in ("message", "app_mention"):
            text = event.get("text", "").strip()
            # Strip bot mention prefix <@U123>
            import re
            text = re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()

            if not text:
                return {"ok": True}

            user_id = event.get("user", "unknown")
            channel_id = event.get("channel", "")
            thread_ts = event.get("thread_ts")

            msg = InboundMessage(
                platform=self.platform_name,
                chat_id=channel_id,
                user_id=user_id,
                user_name=user_id,  # Slack user IDs; resolve to name via API if needed
                text=text,
                thread_id=thread_ts,
                raw=event,
            )

            reply = await self._process_message(msg, session)

            await self.send_message(
                OutboundMessage(
                    chat_id=channel_id,
                    text=reply,
                    thread_id=thread_ts,
                )
            )

        return {"ok": True}

    # ── Send message ──────────────────────────────────────────────────────────

    async def send_message(self, msg: OutboundMessage) -> dict:
        """Send a message via Slack Web API chat.postMessage."""
        payload: dict = {
            "channel": msg.chat_id,
            "text": msg.text[:3000],
            "mrkdwn": True,  # Slack markdown
        }
        if msg.thread_id:
            payload["thread_ts"] = msg.thread_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.SLACK_API}/chat.postMessage",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._bot_token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
                timeout=10.0,
            )
            return response.json()

    # ── Webhook management ────────────────────────────────────────────────────

    async def setup_webhook(self, base_url: str) -> dict:
        full_url = self._get_webhooks_full_url(base_url)
        logger.info(f"[slack] Events API URL: {full_url}")
        return {
            "status": "manual_setup_required",
            "url": full_url,
            "instructions": (
                "1. Go to https://api.slack.com/apps\n"
                "2. Select your app → Event Subscriptions\n"
                "3. Toggle 'Enable Events' ON\n"
                "4. Set Request URL to the URL above\n"
                "5. Subscribe to: message.im, app_mention\n"
                "6. Also add /ask to Slash Commands → Request URL"
            ),
        }

    async def teardown_webhook(self) -> dict:
        return {"status": "manual_removal_required"}


# Self-register
_instance = SlackChannel()
get_channel_registry().register(_instance)
