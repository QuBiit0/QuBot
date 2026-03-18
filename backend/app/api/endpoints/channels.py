"""
Channels API — REST endpoints for managing messaging channel integrations.

Routes:
  GET    /channels/          — List all registered channels and their status
  POST   /channels/{platform}/setup-webhook  — Register webhook with the platform
  DELETE /channels/{platform}/webhook        — Remove webhook from the platform
  GET    /channels/{platform}/status         — Test channel connectivity
  POST   /channels/discord/register-commands — Register Discord slash commands
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...channels import get_channel_registry
from ...core.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/channels", tags=["channels"])


# ── Response schemas ─────────────────────────────────────────────────────────

class ChannelInfo(BaseModel):
    platform: str
    name: str
    active: bool
    webhook_path: str


class WebhookSetupResponse(BaseModel):
    platform: str
    result: dict[str, Any]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[ChannelInfo])
async def list_channels():
    """List all registered (active + configured) channels."""
    registry = get_channel_registry()
    return [
        ChannelInfo(
            platform=ch.platform_name,
            name=ch.name,
            active=True,
            webhook_path=ch.webhook_path,
        )
        for ch in registry.list_channels()
    ]


@router.post("/{platform}/setup-webhook", response_model=WebhookSetupResponse)
async def setup_webhook(
    platform: str,
    base_url: str,
):
    """
    Register the webhook URL for a channel with the external platform.

    Args:
        platform: Channel slug (discord, slack, whatsapp)
        base_url: Your public base URL (e.g. https://api.qubot.io)
    """
    registry = get_channel_registry()
    channel = registry.get(platform)
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel '{platform}' not found or not configured")

    result = await channel.setup_webhook(base_url)
    return WebhookSetupResponse(platform=platform, result=result)


@router.delete("/{platform}/webhook", response_model=WebhookSetupResponse)
async def teardown_webhook(platform: str):
    """Remove the webhook registration for a channel."""
    registry = get_channel_registry()
    channel = registry.get(platform)
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel '{platform}' not found")

    result = await channel.teardown_webhook()
    return WebhookSetupResponse(platform=platform, result=result)


@router.get("/{platform}/status")
async def channel_status(platform: str):
    """Check if a channel is configured and ready."""
    registry = get_channel_registry()
    channel = registry.get(platform)
    if not channel:
        return {"platform": platform, "active": False, "error": "Not configured"}

    return {
        "platform": platform,
        "name": channel.name,
        "active": True,
        "configured": channel.is_configured(),
    }


@router.post("/discord/register-commands")
async def register_discord_commands():
    """Register /ask and /status slash commands with Discord (global)."""
    registry = get_channel_registry()
    channel = registry.get("discord")
    if not channel:
        raise HTTPException(status_code=404, detail="Discord not configured")

    from ...channels.discord_channel import DiscordChannel
    if not isinstance(channel, DiscordChannel):
        raise HTTPException(status_code=500, detail="Unexpected channel type")

    result = await channel.register_slash_commands()
    return {"result": result}


# ── Dynamic webhook receivers ──────────────────────────────────────────────────
# These routes receive inbound webhooks FROM the external platforms

@router.post("/discord/webhook")
@router.get("/discord/webhook")
async def discord_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    registry = get_channel_registry()
    channel = registry.get("discord")
    if not channel:
        raise HTTPException(status_code=503, detail="Discord not configured")
    return await channel.handle_webhook(request, session)


@router.post("/slack/webhook")
async def slack_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    registry = get_channel_registry()
    channel = registry.get("slack")
    if not channel:
        raise HTTPException(status_code=503, detail="Slack not configured")
    return await channel.handle_webhook(request, session)


@router.post("/whatsapp/webhook")
@router.get("/whatsapp/webhook")  # GET for Meta verification challenge
async def whatsapp_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    registry = get_channel_registry()
    channel = registry.get("whatsapp")
    if not channel:
        raise HTTPException(status_code=503, detail="WhatsApp not configured")
    return await channel.handle_webhook(request, session)
