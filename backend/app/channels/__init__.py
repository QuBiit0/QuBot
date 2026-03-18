"""
Channels package — all messaging platform integrations.

Importing this package registers all configured channels in the global registry.
"""

from .base import (
    BaseChannel,
    ChannelRegistry,
    InboundMessage,
    OutboundMessage,
    get_channel_registry,
)

# Import channels to trigger self-registration
# Each module calls get_channel_registry().register() at module level
# Only channels that pass is_configured() are actually active

try:
    from . import discord_channel  # noqa: F401
except Exception:
    pass

try:
    from . import slack_channel  # noqa: F401
except Exception:
    pass

try:
    from . import whatsapp_channel  # noqa: F401
except Exception:
    pass

# Telegram is managed separately at api/endpoints/telegram.py (legacy)
# It will be refactored to use this plugin system in a future iteration

__all__ = [
    "BaseChannel",
    "ChannelRegistry",
    "InboundMessage",
    "OutboundMessage",
    "get_channel_registry",
]
