"""
WhatsApp Channel Plugin — WhatsApp Business API via Meta Webhooks.

Protocol: Meta sends HTTP POST events to a verified webhook.
  - GET  /webhook  → verification challenge (hub.verify_token)
  - POST /webhook  → inbound messages / status updates

Env vars required:
    WHATSAPP_API_TOKEN            — Permanent access token or System User token
    WHATSAPP_PHONE_NUMBER_ID      — Numeric ID of the WhatsApp Business phone
    WHATSAPP_WEBHOOK_VERIFY_TOKEN — Any string you define; must match Meta dashboard
    WHATSAPP_BUSINESS_ACCOUNT_ID  — (optional) WABA ID for account-level ops
"""

from __future__ import annotations

import logging
import os

import httpx
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseChannel, InboundMessage, OutboundMessage, get_channel_registry

logger = logging.getLogger(__name__)


class WhatsAppChannel(BaseChannel):
    """
    WhatsApp Business Cloud API integration.

    Supports:
    - Webhook verification (GET challenge)
    - Inbound text messages
    - Auto-read receipts
    - Reply via Cloud API (text messages)
    - Typing indicator
    """

    META_API = "https://graph.facebook.com/v21.0"

    def __init__(self):
        self._api_token = os.getenv("WHATSAPP_API_TOKEN", "")
        self._phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self._verify_token = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")

    @property
    def name(self) -> str:
        return "WhatsApp"

    @property
    def platform_name(self) -> str:
        return "whatsapp"

    @property
    def webhook_path(self) -> str:
        return "whatsapp/webhook"

    def is_configured(self) -> bool:
        return bool(self._api_token and self._phone_number_id and self._verify_token)

    # ── Webhook handler ───────────────────────────────────────────────────────

    async def handle_webhook(
        self,
        request: Request,
        session: AsyncSession,
    ) -> dict:
        """
        Handles both GET (verification) and POST (events) requests.
        FastAPI routing sends both to this method; we distinguish via request.method.
        """
        if request.method == "GET":
            return await self._handle_verification(request)
        return await self._handle_event(request, session)

    async def _handle_verification(self, request: Request) -> dict:
        """Handle Meta webhook verification challenge (GET)."""
        params = dict(request.query_params)
        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")

        if mode == "subscribe" and token == self._verify_token:
            logger.info("[whatsapp] Webhook verified ✅")
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(challenge)

        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Verification failed")

    async def _handle_event(self, request: Request, session: AsyncSession) -> dict:
        """Process inbound WhatsApp message events."""
        body = await request.json()

        try:
            entry = body.get("entry", [{}])[0]
            change = entry.get("changes", [{}])[0]
            value = change.get("value", {})

            # Process only message events
            messages = value.get("messages", [])
            contacts = {c["wa_id"]: c for c in value.get("contacts", [])}

            for wamsg in messages:
                msg_type = wamsg.get("type", "")
                from_id = wamsg.get("from", "")
                msg_id = wamsg.get("id", "")

                # Only handle text messages for now
                if msg_type != "text":
                    logger.debug(f"[whatsapp] Ignoring non-text message type: {msg_type}")
                    continue

                text = wamsg.get("text", {}).get("body", "").strip()
                if not text:
                    continue

                contact = contacts.get(from_id, {})
                profile = contact.get("profile", {})
                user_name = profile.get("name", from_id)

                # Mark as read
                await self._mark_as_read(msg_id)

                msg = InboundMessage(
                    platform=self.platform_name,
                    chat_id=from_id,  # WhatsApp uses phone as chat ID
                    user_id=from_id,
                    user_name=user_name,
                    text=text,
                    message_id=msg_id,
                    raw=wamsg,
                )

                reply = await self._process_message(msg, session)

                await self.send_message(
                    OutboundMessage(
                        chat_id=from_id,
                        text=reply,
                        reply_to_id=msg_id,
                    )
                )

        except Exception:
            logger.exception("[whatsapp] Error handling event")

        return {"status": "ok"}

    # ── Utility API calls ─────────────────────────────────────────────────────

    async def _mark_as_read(self, message_id: str) -> None:
        """Mark a message as read (shows blue checkmarks on sender's side)."""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.META_API}/{self._phone_number_id}/messages",
                    json={
                        "messaging_product": "whatsapp",
                        "status": "read",
                        "message_id": message_id,
                    },
                    headers=self._auth_headers(),
                    timeout=5.0,
                )
        except Exception:
            pass  # Non-critical

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json",
        }

    # ── Send message ──────────────────────────────────────────────────────────

    async def send_message(self, msg: OutboundMessage) -> dict:
        """Send a text message via WhatsApp Cloud API."""
        payload: dict = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": msg.chat_id,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": msg.text[:4096],
            },
        }

        if msg.reply_to_id:
            payload["context"] = {"message_id": msg.reply_to_id}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.META_API}/{self._phone_number_id}/messages",
                json=payload,
                headers=self._auth_headers(),
                timeout=10.0,
            )
            data = response.json()
            if response.status_code != 200:
                logger.warning(f"[whatsapp] send failed: {data}")
            return data

    # ── Webhook management ────────────────────────────────────────────────────

    async def setup_webhook(self, base_url: str) -> dict:
        full_url = self._get_webhooks_full_url(base_url)
        logger.info(f"[whatsapp] Webhook URL: {full_url}")
        return {
            "status": "manual_setup_required",
            "url": full_url,
            "verify_token": self._verify_token,
            "instructions": (
                "1. Go to Meta Developer Console → Your App\n"
                "2. WhatsApp → Configuration → Webhook\n"
                "3. Set Callback URL to the URL above\n"
                "4. Set Verify Token to your WHATSAPP_WEBHOOK_VERIFY_TOKEN\n"
                "5. Subscribe to 'messages' field"
            ),
        }

    async def teardown_webhook(self) -> dict:
        return {"status": "manual_removal_required"}


# Self-register
_instance = WhatsAppChannel()
get_channel_registry().register(_instance)
