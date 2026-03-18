"""
Channel Plugin Base — Abstract interface for all messaging platform integrations.

Every channel (Telegram, Discord, Slack, WhatsApp, etc.) implements this ABC.
The system supports dynamic registration of new channel plugins at startup.

Inspired by:
- OpenClaw's modular channel system (22+ channels)
- NanoBot's Channel Plugin Guide (low-code extension model)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from fastapi import Request

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Standardized Message contract
# ---------------------------------------------------------------------------

@dataclass
class InboundMessage:
    """
    Normalized message received from any messaging platform.
    Channel implementations parse the raw webhook payload into this struct.
    """

    platform: str                       # "telegram" | "discord" | "slack" | "whatsapp"
    chat_id: str                        # Platform-specific chat/channel ID
    user_id: str                        # Platform-specific user ID
    user_name: str                      # Human-readable display name
    text: str                           # Cleaned message text (no bot mention prefix)
    message_id: str = ""               # Native platform message ID
    is_command: bool = False           # Starts with / or bot command
    command: str = ""                  # Command name, e.g. "start" (no slash)
    command_args: str = ""             # Everything after the command
    raw: dict[str, Any] = field(default_factory=dict)  # Original payload
    media_url: str | None = None       # Optional media attachment URL
    reply_to_id: str | None = None     # ID of message being replied to
    thread_id: str | None = None       # Thread / reply-chain ID (Slack etc.)


@dataclass
class OutboundMessage:
    """Response to send back to the user on the platform."""

    chat_id: str
    text: str
    parse_mode: str = "markdown"       # markdown | html | plain
    reply_to_id: str | None = None
    thread_id: str | None = None


# ---------------------------------------------------------------------------
# Base Channel plugin
# ---------------------------------------------------------------------------

class BaseChannel(ABC):
    """
    Abstract base class for all messaging channel integrations.

    Subclasses MUST implement:
        - name / platform_name
        - is_configured()
        - handle_webhook(request, session)  →  processes inbound updates
        - send_message(msg)                 →  sends text to the platform
        - setup_webhook(base_url)           →  registers webhook with the platform
        - teardown_webhook()               →  removes webhook registration

    Optional hooks:
        - on_startup(app)     — called when the FastAPI app starts
        - on_shutdown(app)    — called when the FastAPI app stops
    """

    # ---- Subclass metadata ------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable channel name, e.g. 'Telegram'"""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Slug used as enum / route key: 'telegram' | 'discord' | 'slack' | 'whatsapp'"""

    @property
    @abstractmethod
    def webhook_path(self) -> str:
        """FastAPI route suffix, e.g. '/telegram/webhook'"""

    # ---- Configuration ----------------------------------------------------

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Return True if all required env vars / tokens are present.
        The system disables the channel silently if this returns False.
        """

    # ---- Core interface ---------------------------------------------------

    @abstractmethod
    async def handle_webhook(
        self,
        request: "Request",
        session: AsyncSession,
    ) -> dict[str, Any]:
        """
        Parse a raw webhook POST payload and process the inbound event.
        Must return a dict that will be JSON-serialised as the HTTP response.
        """

    @abstractmethod
    async def send_message(self, msg: OutboundMessage) -> dict[str, Any]:
        """
        Send a text reply back to the user on the platform.
        Returns the platform's send-message response payload.
        """

    @abstractmethod
    async def setup_webhook(self, base_url: str) -> dict[str, Any]:
        """
        Register this bot's webhook URL with the external platform.
        base_url: e.g. "https://api.qubot.io"
        """

    @abstractmethod
    async def teardown_webhook(self) -> dict[str, Any]:
        """Unregister / delete the webhook from the external platform."""

    # ---- Optional lifecycle hooks -----------------------------------------

    async def on_startup(self, app: Any) -> None:
        """Called once when the FastAPI application starts."""

    async def on_shutdown(self, app: Any) -> None:
        """Called once when the FastAPI application stops."""

    # ---- Shared helpers ---------------------------------------------------

    def _get_webhooks_full_url(self, base_url: str) -> str:
        """Build the full public webhook URL for this channel."""
        base = base_url.rstrip("/")
        path = self.webhook_path.lstrip("/")
        return f"{base}/api/v1/{path}"

    async def _process_message(
        self,
        msg: InboundMessage,
        session: AsyncSession,
        assigned_agent_id: UUID | None = None,
    ) -> str:
        """
        Shared pipeline: route InboundMessage → OrchestratorService → text reply.

        This default implementation handles the full orchestration call so that
        individual channel plugins only need to parse/send and not deal with
        business logic.
        """
        from app.services.llm_service import LLMService
        from app.services.orchestrator_service import OrchestratorService
        from app.models.enums import DomainEnum, PriorityEnum

        try:
            # Get default LLM config
            llm_service = LLMService(session)
            configs = await llm_service.get_default_configs()

            if not configs:
                return "⚠️ No LLM configuration found. Please set up a provider in Settings."

            llm_config_id = configs[0].id

            # Detect domain (basic keyword matching)
            domain = self._detect_domain(msg.text)

            # Process through orchestrator
            orchestrator = OrchestratorService(session)
            result = await orchestrator.process_task(
                title=msg.text[:200],
                description=msg.text,
                llm_config_id=llm_config_id,
                priority=PriorityEnum.MEDIUM,
                requested_domain=domain,
                input_data={
                    "source": self.platform_name,
                    "user_id": msg.user_id,
                    "user_name": msg.user_name,
                    "chat_id": msg.chat_id,
                    "channel": self.platform_name,
                },
                created_by=msg.user_id,
            )

            if result.get("success"):
                task_id = result.get("parent_task_id", "?")
                subtasks = result.get("subtasks", [])
                agent = result.get("assigned_agent", "an agent")

                if subtasks:
                    return (
                        f"✅ Task created! Broken into *{len(subtasks)} steps*.\n"
                        f"Task ID: `{task_id}` — Coordinator: {agent}"
                    )
                return (
                    f"✅ Task assigned to **{agent}**\n"
                    f"Task ID: `{task_id}` — I'll notify you when done."
                )
            else:
                error = result.get("error", "Unknown error")
                return f"❌ Error processing your request: {error}"

        except Exception:
            logger.exception(f"[{self.platform_name}] Error processing message")
            return "⚠️ Something went wrong. Please try again later."

    _DOMAIN_KEYWORDS: dict = {
        "TECH": ["code","develop","build","fix","bug","api","backend","frontend","deploy","database","script"],
        "BUSINESS": ["business","strategy","revenue","sales","client","market","product"],
        "FINANCE": ["finance","budget","cost","expense","invoice","payment","accounting"],
        "HR": ["hire","recruit","employee","team","salary","onboarding","training"],
        "MARKETING": ["marketing","campaign","seo","content","social","brand","audience"],
        "LEGAL": ["legal","contract","compliance","regulation","law","policy","gdpr"],
        "PERSONAL": ["personal","reminder","todo","schedule","appointment","meeting"],
    }

    def _detect_domain(self, text: str):
        from app.models.enums import DomainEnum
        lower = text.lower()
        scores = {d: 0 for d in DomainEnum}
        for domain_str, keywords in self._DOMAIN_KEYWORDS.items():
            try:
                domain = DomainEnum[domain_str]
                for kw in keywords:
                    if kw in lower:
                        scores[domain] += 1
            except KeyError:
                pass
        best = max(scores, key=lambda d: scores[d])
        return best if scores[best] > 0 else DomainEnum.OTHER


# ---------------------------------------------------------------------------
# Channel Registry
# ---------------------------------------------------------------------------

class ChannelRegistry:
    """
    Global registry of all active channel plugins.
    Channels self-register on import. Only configured channels are active.
    """

    def __init__(self):
        self._channels: dict[str, BaseChannel] = {}

    def register(self, channel: BaseChannel) -> None:
        """Register a channel instance. Skips if not configured."""
        if not channel.is_configured():
            logger.info(f"[channels] {channel.name} skipped (not configured)")
            return
        self._channels[channel.platform_name] = channel
        logger.info(f"[channels] {channel.name} registered ✅")

    def get(self, platform_name: str) -> BaseChannel | None:
        return self._channels.get(platform_name)

    def list_channels(self) -> list[BaseChannel]:
        return list(self._channels.values())

    def list_names(self) -> list[str]:
        return list(self._channels.keys())


# Singleton registry
_registry: ChannelRegistry | None = None


def get_channel_registry() -> ChannelRegistry:
    global _registry
    if _registry is None:
        _registry = ChannelRegistry()
    return _registry
