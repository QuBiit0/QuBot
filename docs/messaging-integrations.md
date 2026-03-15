# Qubot — Messaging Integrations

> **Module**: `backend/app/messaging/`
> **Supported platforms**: Telegram, WhatsApp (Meta Cloud API), Discord, Slack
> **Pattern**: All inbound messages route to the same Orchestrator used by the web UI chat.

---

## 1. Overview

Users can interact with Qubot — and their entire agent team — directly from their preferred messaging app. A message sent on Telegram or WhatsApp is treated identically to a message sent through the web chat UI: it reaches the Orchestrator, which can create tasks, assign agents, and reply with results.

```
User (Telegram/WhatsApp/Discord/Slack)
    │
    │  inbound message (webhook POST)
    ▼
┌─────────────────────────────────────────────────┐
│  Messaging Ingress Layer (backend/app/messaging) │
│  - Verify platform signature                     │
│  - Parse platform-specific payload               │
│  - Resolve or create Conversation record         │
│  - Normalize to standard ChatMessage             │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
        OrchestratorService.handle_chat()
                     │
                     ▼
        Platform-specific sender
        (reply back to user)
```

**Key principle**: The messaging layer is a thin adapter. It converts platform-specific formats into the same `ChatRequest` the web UI uses, then converts `ChatResponse` back into the platform's send format.

---

## 2. Database Schema

### 2.1 `MessagingChannel` — configured platform connections

```python
class MessagingChannel(SQLModel, table=True):
    __tablename__ = "messaging_channel"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    platform: MessagingPlatformEnum   # TELEGRAM | WHATSAPP | DISCORD | SLACK
    name: str                         # Human label, e.g. "Main Telegram Bot"
    is_active: bool = True

    # Credentials — stored as env var references (never plaintext secrets)
    # e.g. {"bot_token_ref": "TELEGRAM_BOT_TOKEN", "secret_ref": "TELEGRAM_SECRET"}
    config: dict = Field(sa_column=Column(JSONB), default={})

    # Optional: restrict this channel to a specific agent as responder
    # If None, uses the global orchestrator
    assigned_agent_id: Optional[UUID] = Field(default=None, foreign_key="agent.id")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2.2 `Conversation` — one per (channel × external_user)

```python
class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    channel_id: UUID = Field(foreign_key="messaging_channel.id")

    # Platform-native identifiers
    external_user_id: str    # Telegram user_id, WhatsApp phone number, Discord user ID
    external_chat_id: str    # Telegram chat_id, WhatsApp phone, Discord channel ID

    # Optional: map to an internal Qubot user
    qubot_user_id: Optional[str] = None

    # Rolling history for context (last N messages, stored as JSON array)
    history: list[dict] = Field(sa_column=Column(JSONB), default=[])

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2.3 `ConversationMessage` — immutable message log

```python
class ConversationMessage(SQLModel, table=True):
    __tablename__ = "conversation_message"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversation.id")
    direction: MessageDirectionEnum  # INBOUND | OUTBOUND
    content: str                     # Plain text content
    platform_message_id: str         # Native message ID from the platform
    metadata: dict = Field(sa_column=Column(JSONB), default={})
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 2.4 New Enums

```python
class MessagingPlatformEnum(str, Enum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    DISCORD = "discord"
    SLACK = "slack"

class MessageDirectionEnum(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
```

---

## 3. Architecture — Messaging Module

```
backend/app/messaging/
├── __init__.py
├── router.py              # All webhook + management endpoints
├── base.py                # BasePlatformAdapter ABC
├── dispatcher.py          # Inbound message → OrchestratorService → send reply
├── adapters/
│   ├── telegram.py        # TelegramAdapter
│   ├── whatsapp.py        # WhatsAppAdapter (Meta Cloud API)
│   ├── discord.py         # DiscordAdapter
│   └── slack.py           # SlackAdapter
└── senders/
    ├── telegram_sender.py
    ├── whatsapp_sender.py
    ├── discord_sender.py
    └── slack_sender.py
```

### `base.py` — Platform Adapter Interface

```python
from abc import ABC, abstractmethod
from fastapi import Request
from pydantic import BaseModel


class InboundMessage(BaseModel):
    """Normalized inbound message from any platform."""
    platform: MessagingPlatformEnum
    channel_id: UUID
    external_user_id: str
    external_chat_id: str
    text: str
    platform_message_id: str
    raw_payload: dict  # Original platform payload for debugging


class BasePlatformAdapter(ABC):
    """Convert platform-specific webhook payload → InboundMessage."""

    @abstractmethod
    async def verify_signature(self, request: Request, channel: MessagingChannel) -> bool:
        """Verify the request is authentically from the platform."""
        ...

    @abstractmethod
    async def parse_inbound(self, request: Request, channel: MessagingChannel) -> InboundMessage | None:
        """Parse the raw webhook payload. Returns None if not a text message (e.g. media, system events)."""
        ...

    @abstractmethod
    async def send_message(self, channel: MessagingChannel, chat_id: str, text: str) -> bool:
        """Send a reply to the user. Returns True on success."""
        ...
```

### `dispatcher.py` — Core Routing Logic

```python
import structlog
from app.services.orchestrator_service import OrchestratorService
from app.services.messaging_service import MessagingService
from app.schemas.chat import ChatRequest

logger = structlog.get_logger()


class MessageDispatcher:

    def __init__(self, orchestrator: OrchestratorService, messaging_svc: MessagingService):
        self.orchestrator = orchestrator
        self.messaging = messaging_svc

    async def handle(self, msg: InboundMessage, channel: MessagingChannel):
        """Process one inbound message end-to-end."""

        # 1. Resolve or create Conversation
        conversation = await self.messaging.get_or_create_conversation(
            channel_id=msg.channel_id,
            external_user_id=msg.external_user_id,
            external_chat_id=msg.external_chat_id,
        )

        # 2. Persist inbound message
        await self.messaging.save_message(
            conversation_id=conversation.id,
            direction=MessageDirectionEnum.INBOUND,
            content=msg.text,
            platform_message_id=msg.platform_message_id,
        )

        # 3. Build chat request (same as web UI)
        chat_req = ChatRequest(
            message=msg.text,
            conversation_history=conversation.history[-10:],  # last 10 messages as context
        )

        # 4. Call orchestrator
        try:
            chat_response = await self.orchestrator.handle_chat(chat_req)
            reply_text = chat_response.response or _format_actions(chat_response.actions)
        except Exception as e:
            logger.error("orchestrator_error", error=str(e), platform=msg.platform)
            reply_text = "Sorry, I encountered an error. Please try again."

        # 5. Send reply
        adapter = get_adapter(channel.platform)
        await adapter.send_message(channel, msg.external_chat_id, reply_text)

        # 6. Persist outbound message + update conversation history
        await self.messaging.save_message(
            conversation_id=conversation.id,
            direction=MessageDirectionEnum.OUTBOUND,
            content=reply_text,
            platform_message_id="",
        )
        await self.messaging.update_history(conversation.id, msg.text, reply_text)

        logger.info(
            "message_handled",
            platform=msg.platform,
            conversation_id=str(conversation.id),
        )


def _format_actions(actions: list) -> str:
    """Convert orchestrator actions into readable text for messaging platforms."""
    lines = []
    for action in actions:
        if action.type == "CREATE_TASK":
            lines.append(f"✅ Task created: *{action.payload.get('title')}*")
        elif action.type == "ASSIGN_TASK":
            lines.append(f"👤 Task assigned to agent")
        elif action.type == "UPDATE_TASK":
            lines.append(f"🔄 Task updated")
    return "\n".join(lines) if lines else "Done."
```

---

## 4. Platform-Specific Implementation

### 4.1 Telegram

**Setup:**
1. Create bot via [@BotFather](https://t.me/BotFather) → get `BOT_TOKEN`
2. Set webhook: `POST https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://yourdomain.com/webhooks/telegram/{channel_id}`
3. Optionally set `secret_token` for signature verification

**Config JSON stored in `MessagingChannel.config`:**
```json
{
  "bot_token_ref": "TELEGRAM_BOT_TOKEN",
  "secret_token_ref": "TELEGRAM_SECRET_TOKEN"
}
```

**`adapters/telegram.py`:**
```python
import hashlib, hmac, os
from fastapi import Request
from app.messaging.base import BasePlatformAdapter, InboundMessage


class TelegramAdapter(BasePlatformAdapter):

    async def verify_signature(self, request: Request, channel: MessagingChannel) -> bool:
        secret_ref = channel.config.get("secret_token_ref")
        if not secret_ref:
            return True  # No secret configured — skip verification (dev only)
        expected = os.getenv(secret_ref, "")
        received = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        return hmac.compare_digest(expected, received)

    async def parse_inbound(self, request: Request, channel: MessagingChannel) -> InboundMessage | None:
        payload = await request.json()
        message = payload.get("message") or payload.get("edited_message")
        if not message or "text" not in message:
            return None  # Ignore non-text updates (photos, stickers, etc.)

        return InboundMessage(
            platform=MessagingPlatformEnum.TELEGRAM,
            channel_id=channel.id,
            external_user_id=str(message["from"]["id"]),
            external_chat_id=str(message["chat"]["id"]),
            text=message["text"],
            platform_message_id=str(message["message_id"]),
            raw_payload=payload,
        )

    async def send_message(self, channel: MessagingChannel, chat_id: str, text: str) -> bool:
        import httpx
        token = os.getenv(channel.config["bot_token_ref"], "")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            })
        return resp.is_success
```

### 4.2 WhatsApp (Meta Cloud API)

**Setup:**
1. Create Meta App → add WhatsApp product → get `PHONE_NUMBER_ID` + `ACCESS_TOKEN`
2. Set webhook URL in Meta dashboard: `https://yourdomain.com/webhooks/whatsapp/{channel_id}`
3. Set `VERIFY_TOKEN` (a string you choose) for the verification challenge
4. Subscribe to `messages` webhook field

**Config JSON:**
```json
{
  "phone_number_id_ref": "WHATSAPP_PHONE_NUMBER_ID",
  "access_token_ref": "WHATSAPP_ACCESS_TOKEN",
  "verify_token_ref": "WHATSAPP_VERIFY_TOKEN",
  "app_secret_ref": "WHATSAPP_APP_SECRET"
}
```

**`adapters/whatsapp.py`:**
```python
import hashlib, hmac, os
from fastapi import Request
from app.messaging.base import BasePlatformAdapter, InboundMessage


class WhatsAppAdapter(BasePlatformAdapter):

    async def verify_signature(self, request: Request, channel: MessagingChannel) -> bool:
        """Meta signs requests with HMAC-SHA256 of the raw body using the App Secret."""
        app_secret = os.getenv(channel.config.get("app_secret_ref", ""), "")
        if not app_secret:
            return True
        signature_header = request.headers.get("X-Hub-Signature-256", "")
        if not signature_header.startswith("sha256="):
            return False
        body = await request.body()
        expected = "sha256=" + hmac.new(
            app_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header)

    async def parse_inbound(self, request: Request, channel: MessagingChannel) -> InboundMessage | None:
        payload = await request.json()
        try:
            entry = payload["entry"][0]
            change = entry["changes"][0]
            value = change["value"]
            msg = value["messages"][0]
            if msg.get("type") != "text":
                return None  # Ignore media messages
            contact = value["contacts"][0]
            return InboundMessage(
                platform=MessagingPlatformEnum.WHATSAPP,
                channel_id=channel.id,
                external_user_id=contact["wa_id"],
                external_chat_id=contact["wa_id"],  # For WhatsApp, chat = user phone
                text=msg["text"]["body"],
                platform_message_id=msg["id"],
                raw_payload=payload,
            )
        except (KeyError, IndexError):
            return None

    async def send_message(self, channel: MessagingChannel, chat_id: str, text: str) -> bool:
        import httpx
        phone_id = os.getenv(channel.config["phone_number_id_ref"], "")
        token = os.getenv(channel.config["access_token_ref"], "")
        url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": chat_id,
                    "type": "text",
                    "text": {"body": text},
                },
            )
        return resp.is_success
```

### 4.3 Discord

**Setup:**
1. Create application at [discord.com/developers](https://discord.com/developers)
2. Add Bot, get `BOT_TOKEN`
3. Set Interactions Endpoint URL in app settings (for slash commands) OR use Gateway WebSocket (for message events)
4. Recommended for Qubot: use the Bot Gateway to listen to `MESSAGE_CREATE` events

**Config JSON:**
```json
{
  "bot_token_ref": "DISCORD_BOT_TOKEN",
  "application_id_ref": "DISCORD_APPLICATION_ID",
  "public_key_ref": "DISCORD_PUBLIC_KEY"
}
```

**`adapters/discord.py`:**
```python
import os
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.exceptions import InvalidSignature
from fastapi import Request
from app.messaging.base import BasePlatformAdapter, InboundMessage


class DiscordAdapter(BasePlatformAdapter):

    async def verify_signature(self, request: Request, channel: MessagingChannel) -> bool:
        """Discord uses Ed25519 signature verification."""
        public_key_hex = os.getenv(channel.config.get("public_key_ref", ""), "")
        signature = request.headers.get("X-Signature-Ed25519", "")
        timestamp = request.headers.get("X-Signature-Timestamp", "")
        body = await request.body()
        try:
            public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
            public_key.verify(bytes.fromhex(signature), timestamp.encode() + body)
            return True
        except (InvalidSignature, Exception):
            return False

    async def parse_inbound(self, request: Request, channel: MessagingChannel) -> InboundMessage | None:
        payload = await request.json()
        # Handle Discord PING (verification)
        if payload.get("type") == 1:
            return None  # Handled separately in router (must return {"type": 1})
        # Handle MESSAGE_CREATE (type 0 = normal message)
        if payload.get("type") == 0 and payload.get("content"):
            return InboundMessage(
                platform=MessagingPlatformEnum.DISCORD,
                channel_id=channel.id,
                external_user_id=payload["author"]["id"],
                external_chat_id=payload["channel_id"],
                text=payload["content"],
                platform_message_id=payload["id"],
                raw_payload=payload,
            )
        return None

    async def send_message(self, channel: MessagingChannel, chat_id: str, text: str) -> bool:
        import httpx
        token = os.getenv(channel.config["bot_token_ref"], "")
        url = f"https://discord.com/api/v10/channels/{chat_id}/messages"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bot {token}"},
                json={"content": text},
            )
        return resp.is_success
```

### 4.4 Slack

**Setup:**
1. Create Slack App at [api.slack.com](https://api.slack.com)
2. Enable Event Subscriptions → subscribe to `message.channels`, `message.im`
3. Set Request URL: `https://yourdomain.com/webhooks/slack/{channel_id}`
4. Get `Signing Secret` + `Bot Token` (starts with `xoxb-`)

**Config JSON:**
```json
{
  "bot_token_ref": "SLACK_BOT_TOKEN",
  "signing_secret_ref": "SLACK_SIGNING_SECRET"
}
```

**`adapters/slack.py`:**
```python
import hashlib, hmac, os, time
from fastapi import Request
from app.messaging.base import BasePlatformAdapter, InboundMessage


class SlackAdapter(BasePlatformAdapter):

    async def verify_signature(self, request: Request, channel: MessagingChannel) -> bool:
        """Slack HMAC-SHA256 with timestamp replay protection."""
        signing_secret = os.getenv(channel.config.get("signing_secret_ref", ""), "")
        timestamp = request.headers.get("X-Slack-Request-Timestamp", "0")
        if abs(time.time() - int(timestamp)) > 60 * 5:
            return False  # Replay attack protection — reject if older than 5 minutes
        body = await request.body()
        sig_basestring = f"v0:{timestamp}:{body.decode()}"
        computed = "v0=" + hmac.new(
            signing_secret.encode(), sig_basestring.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(computed, request.headers.get("X-Slack-Signature", ""))

    async def parse_inbound(self, request: Request, channel: MessagingChannel) -> InboundMessage | None:
        payload = await request.json()
        # URL verification challenge
        if payload.get("type") == "url_verification":
            return None  # Handled in router (return challenge)
        event = payload.get("event", {})
        if event.get("type") == "message" and not event.get("bot_id"):
            return InboundMessage(
                platform=MessagingPlatformEnum.SLACK,
                channel_id=channel.id,
                external_user_id=event["user"],
                external_chat_id=event["channel"],
                text=event["text"],
                platform_message_id=event["ts"],
                raw_payload=payload,
            )
        return None

    async def send_message(self, channel: MessagingChannel, chat_id: str, text: str) -> bool:
        import httpx
        token = os.getenv(channel.config["bot_token_ref"], "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {token}"},
                json={"channel": chat_id, "text": text},
            )
        return resp.json().get("ok", False)
```

---

## 5. Webhook Router

```python
# backend/app/messaging/router.py
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlmodel import select
from app.core.deps import get_session
from app.messaging.adapters.telegram import TelegramAdapter
from app.messaging.adapters.whatsapp import WhatsAppAdapter
from app.messaging.adapters.discord import DiscordAdapter
from app.messaging.adapters.slack import SlackAdapter
from app.messaging.dispatcher import MessageDispatcher

router = APIRouter(tags=["messaging"])

ADAPTERS = {
    MessagingPlatformEnum.TELEGRAM: TelegramAdapter(),
    MessagingPlatformEnum.WHATSAPP: WhatsAppAdapter(),
    MessagingPlatformEnum.DISCORD: DiscordAdapter(),
    MessagingPlatformEnum.SLACK: SlackAdapter(),
}


async def get_active_channel(channel_id: UUID, session) -> MessagingChannel:
    channel = await session.get(MessagingChannel, channel_id)
    if not channel or not channel.is_active:
        raise HTTPException(status_code=404, detail="Channel not found or inactive")
    return channel


# ── Telegram ──────────────────────────────────────────────────────────────
@router.post("/webhooks/telegram/{channel_id}")
async def telegram_webhook(channel_id: UUID, request: Request, session=Depends(get_session)):
    channel = await get_active_channel(channel_id, session)
    adapter = ADAPTERS[MessagingPlatformEnum.TELEGRAM]

    if not await adapter.verify_signature(request, channel):
        raise HTTPException(status_code=401, detail="Invalid signature")

    msg = await adapter.parse_inbound(request, channel)
    if msg:
        dispatcher = MessageDispatcher(...)
        await dispatcher.handle(msg, channel)

    return {"ok": True}


# ── WhatsApp ──────────────────────────────────────────────────────────────
@router.get("/webhooks/whatsapp/{channel_id}")
async def whatsapp_verify(channel_id: UUID, request: Request, session=Depends(get_session)):
    """Meta webhook verification challenge."""
    channel = await get_active_channel(channel_id, session)
    verify_token = os.getenv(channel.config.get("verify_token_ref", ""), "")
    params = request.query_params
    if (params.get("hub.mode") == "subscribe"
            and params.get("hub.verify_token") == verify_token):
        return Response(content=params.get("hub.challenge"), media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhooks/whatsapp/{channel_id}")
async def whatsapp_webhook(channel_id: UUID, request: Request, session=Depends(get_session)):
    channel = await get_active_channel(channel_id, session)
    adapter = ADAPTERS[MessagingPlatformEnum.WHATSAPP]

    if not await adapter.verify_signature(request, channel):
        raise HTTPException(status_code=401, detail="Invalid signature")

    msg = await adapter.parse_inbound(request, channel)
    if msg:
        dispatcher = MessageDispatcher(...)
        await dispatcher.handle(msg, channel)

    return {"status": "ok"}


# ── Discord ───────────────────────────────────────────────────────────────
@router.post("/webhooks/discord/{channel_id}")
async def discord_webhook(channel_id: UUID, request: Request, session=Depends(get_session)):
    channel = await get_active_channel(channel_id, session)
    adapter = ADAPTERS[MessagingPlatformEnum.DISCORD]

    if not await adapter.verify_signature(request, channel):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    if payload.get("type") == 1:
        return {"type": 1}  # Discord PING — must reply immediately

    msg = await adapter.parse_inbound(request, channel)
    if msg:
        dispatcher = MessageDispatcher(...)
        await dispatcher.handle(msg, channel)

    return {"type": 4, "data": {"content": ""}}


# ── Slack ─────────────────────────────────────────────────────────────────
@router.post("/webhooks/slack/{channel_id}")
async def slack_webhook(channel_id: UUID, request: Request, session=Depends(get_session)):
    channel = await get_active_channel(channel_id, session)
    adapter = ADAPTERS[MessagingPlatformEnum.SLACK]

    if not await adapter.verify_signature(request, channel):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    if payload.get("type") == "url_verification":
        return {"challenge": payload["challenge"]}  # Slack URL verification

    msg = await adapter.parse_inbound(request, channel)
    if msg:
        dispatcher = MessageDispatcher(...)
        await dispatcher.handle(msg, channel)

    return {"ok": True}


# ── Channel Management ────────────────────────────────────────────────────
@router.get("/messaging/channels")
async def list_channels(session=Depends(get_session)):
    channels = (await session.exec(select(MessagingChannel))).all()
    return {"data": channels}


@router.post("/messaging/channels", status_code=201)
async def create_channel(data: MessagingChannelCreate, session=Depends(get_session)):
    channel = MessagingChannel(**data.model_dump())
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    return {"data": channel}


@router.put("/messaging/channels/{channel_id}")
async def update_channel(channel_id: UUID, data: MessagingChannelUpdate, session=Depends(get_session)):
    channel = await session.get(MessagingChannel, channel_id)
    if not channel:
        raise HTTPException(404)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(channel, k, v)
    await session.commit()
    return {"data": channel}


@router.delete("/messaging/channels/{channel_id}", status_code=204)
async def delete_channel(channel_id: UUID, session=Depends(get_session)):
    channel = await session.get(MessagingChannel, channel_id)
    if not channel:
        raise HTTPException(404)
    await session.delete(channel)
    await session.commit()


@router.get("/messaging/channels/{channel_id}/conversations")
async def list_conversations(channel_id: UUID, session=Depends(get_session)):
    convs = (await session.exec(
        select(Conversation).where(Conversation.channel_id == channel_id)
    )).all()
    return {"data": convs}
```

---

## 6. Messaging Service

```python
# backend/app/services/messaging_service.py

class MessagingService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_conversation(
        self,
        channel_id: UUID,
        external_user_id: str,
        external_chat_id: str,
    ) -> Conversation:
        existing = await self.session.exec(
            select(Conversation)
            .where(Conversation.channel_id == channel_id)
            .where(Conversation.external_user_id == external_user_id)
        ).first()

        if existing:
            return existing

        conv = Conversation(
            channel_id=channel_id,
            external_user_id=external_user_id,
            external_chat_id=external_chat_id,
            history=[],
        )
        self.session.add(conv)
        await self.session.commit()
        await self.session.refresh(conv)
        return conv

    async def save_message(
        self,
        conversation_id: UUID,
        direction: MessageDirectionEnum,
        content: str,
        platform_message_id: str,
    ) -> ConversationMessage:
        msg = ConversationMessage(
            conversation_id=conversation_id,
            direction=direction,
            content=content,
            platform_message_id=platform_message_id,
        )
        self.session.add(msg)
        await self.session.commit()
        return msg

    async def update_history(
        self,
        conversation_id: UUID,
        user_text: str,
        assistant_text: str,
        max_history: int = 20,
    ):
        conv = await self.session.get(Conversation, conversation_id)
        history = conv.history or []
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": assistant_text})
        conv.history = history[-max_history:]  # Keep last 20 messages
        conv.updated_at = datetime.utcnow()
        await self.session.commit()
```

---

## 7. Frontend — Messaging Settings Page

### `app/settings/messaging/page.tsx`

A management page to configure channels without touching the server:

**UI Sections:**

1. **Active Channels list** — shows platform icon, name, status badge (active/inactive), webhook URL to copy, edit/delete buttons
2. **Add Channel button** — opens `ChannelFormModal`
3. **Conversations view** — click a channel → see all conversations with last message preview

### `ChannelFormModal` fields:

| Platform | Required fields |
|----------|----------------|
| Telegram | Bot Token env var ref, Secret Token env var ref (optional) |
| WhatsApp | Phone Number ID env var ref, Access Token env var ref, Verify Token env var ref, App Secret env var ref |
| Discord | Bot Token env var ref, Public Key env var ref |
| Slack | Bot Token env var ref, Signing Secret env var ref |

All fields accept **env var names** (e.g. `TELEGRAM_BOT_TOKEN`), never actual tokens.

**After saving**, the UI displays the webhook URL to configure in each platform:
```
Telegram webhook: https://yourdomain.com/webhooks/telegram/{channel_id}
WhatsApp webhook: https://yourdomain.com/webhooks/whatsapp/{channel_id}
Discord interactions: https://yourdomain.com/webhooks/discord/{channel_id}
Slack events URL: https://yourdomain.com/webhooks/slack/{channel_id}
```

---

## 8. Environment Variables (Messaging)

Add to `.env.example`:

```bash
# ── Telegram ──────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN=123456789:AAF...
TELEGRAM_SECRET_TOKEN=any_random_string_you_set_in_botfather

# ── WhatsApp (Meta Cloud API) ─────────────────────────────────────
WHATSAPP_PHONE_NUMBER_ID=1234567890
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxx
WHATSAPP_VERIFY_TOKEN=any_random_string_you_choose
WHATSAPP_APP_SECRET=abc123def456...

# ── Discord ───────────────────────────────────────────────────────
DISCORD_BOT_TOKEN=MTxxxxxxx.Gxxxxx.xxxxxxxxx
DISCORD_APPLICATION_ID=123456789012345678
DISCORD_PUBLIC_KEY=abc123...

# ── Slack ─────────────────────────────────────────────────────────
SLACK_BOT_TOKEN=xoxb-1234-5678-abcdef
SLACK_SIGNING_SECRET=abc123def456...
```

---

## 9. Platform Setup Guides (Quick Reference)

### Telegram
1. Message `@BotFather` → `/newbot` → get token
2. Add token to `.env` as `TELEGRAM_BOT_TOKEN`
3. Create channel in Qubot UI → copy webhook URL
4. Register: `curl -X POST "https://api.telegram.org/bot{TOKEN}/setWebhook" -d '{"url":"https://yourdomain.com/webhooks/telegram/{channel_id}", "secret_token":"your_secret"}'`

### WhatsApp
1. [developers.facebook.com](https://developers.facebook.com) → Create App → Add WhatsApp product
2. Generate permanent System User token with `whatsapp_business_messaging` permission
3. Add all 4 env vars to `.env`
4. Create channel in Qubot UI → copy webhook URL → paste in Meta dashboard
5. Subscribe to `messages` webhook field in Meta dashboard

### Discord
1. [discord.com/developers](https://discord.com/developers) → New Application → Bot → Reset Token
2. Enable `MESSAGE CONTENT INTENT` in Bot settings
3. Add bot to server via OAuth2 URL with `bot` + `Send Messages` scopes
4. Add env vars to `.env`
5. Create channel in Qubot UI → copy webhook URL → paste in App → Interactions Endpoint URL

### Slack
1. [api.slack.com](https://api.slack.com) → Create New App → From scratch
2. OAuth & Permissions → Add `chat:write`, `channels:history`, `im:history` scopes
3. Install to workspace → copy Bot Token
4. Event Subscriptions → Enable → set Request URL → Subscribe to `message.channels`, `message.im`
5. Add env vars to `.env`

---

## 10. Message Formatting per Platform

Qubot sends plain text by default. Platform-specific formatting:

| Feature | Telegram | WhatsApp | Discord | Slack |
|---------|----------|----------|---------|-------|
| Bold | `*text*` | `*text*` | `**text**` | `*text*` |
| Code | `` `code` `` | `` `code` `` | `` `code` `` | `` `code` `` |
| Link | `[text](url)` | URL only | `[text](url)` | `<url\|text>` |
| Max length | 4096 chars | 4096 chars | 2000 chars | 40000 chars |

The `_format_actions()` function in `dispatcher.py` uses Telegram/Markdown syntax by default. To support all platforms, pass `platform` to a `format_reply(text, platform)` helper that applies platform-specific escaping.

---

## 11. Project Structure Addition

```
backend/app/messaging/
├── __init__.py
├── router.py              # Webhook endpoints + channel management endpoints
├── base.py                # BasePlatformAdapter ABC + InboundMessage model
├── dispatcher.py          # MessageDispatcher: inbound → orchestrator → send reply
├── service.py             # MessagingService: conversation/message DB operations
└── adapters/
    ├── __init__.py        # ADAPTERS dict + get_adapter() factory
    ├── telegram.py
    ├── whatsapp.py
    ├── discord.py
    └── slack.py

frontend/app/settings/messaging/
└── page.tsx               # Channel management UI (list, create, delete, show webhook URL)

frontend/components/messaging/
├── ChannelCard.tsx         # Platform icon + name + status + webhook URL copy button
└── ChannelFormModal.tsx    # Create/edit channel form with dynamic fields per platform
```

Register the messaging router in `app/main.py`:
```python
from app.messaging.router import router as messaging_router
app.include_router(messaging_router, prefix=API_PREFIX)
```
