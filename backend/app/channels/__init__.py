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

try:
    from . import signal_channel  # noqa: F401
except Exception:
    pass

try:
    from . import teams_channel  # noqa: F401
except Exception:
    pass

try:
    from . import googlechat_channel  # noqa: F401
except Exception:
    pass

try:
    from . import imessage_channel  # noqa: F401
except Exception:
    pass

try:
    from . import matrix_channel  # noqa: F401
except Exception:
    pass

try:
    from . import mattermost_channel  # noqa: F401
except Exception:
    pass

try:
    from . import irc_channel  # noqa: F401
except Exception:
    pass

try:
    from . import line_channel  # noqa: F401
except Exception:
    pass

try:
    from . import feishu_channel  # noqa: F401
except Exception:
    pass

try:
    from . import twitch_channel  # noqa: F401
except Exception:
    pass

try:
    from . import nostr_channel  # noqa: F401
except Exception:
    pass

try:
    from . import synology_chat_channel  # noqa: F401
except Exception:
    pass

try:
    from . import zalo_channel  # noqa: F401
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
