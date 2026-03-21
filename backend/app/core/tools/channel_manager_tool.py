"""
Channel Manager Tool - Configure and manage communication channels.

Allows agents to set up, configure, and manage channels like:
- Telegram, Discord, Slack, WhatsApp
- Microsoft Teams, Signal, Google Chat
- iMessage (via Mac)

Each channel requires different credentials and setup steps.
"""

import json
from pathlib import Path

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


class ChannelManagerTool(BaseTool):
    """
    Manage communication channels for the agent.
    Set up webhooks, configure credentials, and enable/disable channels.
    """

    name = "channel_manager"
    description = (
        "Configure and manage communication channels (Telegram, Discord, Slack, WhatsApp, "
        "Teams, Signal, Google Chat, iMessage). Use to set up bot tokens, webhooks, "
        "and channel-specific settings. Each channel has different requirements."
    )

    category = ToolCategory.SYSTEM
    risk_level = ToolRiskLevel.DANGEROUS

    CHANNELS_CONFIG_PATH = Path("/app/config/channels.json")

    SUPPORTED_CHANNELS = {
        "telegram": {
            "name": "Telegram",
            "icon": "📱",
            "requires": ["bot_token"],
            "setup_type": "webhook",
            "description": "Requires @BotFather bot token",
            "docs_url": "https://core.telegram.org/bots/tutorial",
        },
        "discord": {
            "name": "Discord",
            "icon": "🎮",
            "requires": ["bot_token"],
            "setup_type": "websocket",
            "description": "Requires Discord bot token with MESSAGE CONTENT intent",
            "docs_url": "https://discord.com/developers/docs/getting-started",
        },
        "slack": {
            "name": "Slack",
            "icon": "💬",
            "requires": ["bot_token", "signing_secret"],
            "setup_type": "webhook",
            "description": "Requires Slack bot token (xoxb) and signing secret",
            "docs_url": "https://api.slack.com/start/building",
        },
        "whatsapp": {
            "name": "WhatsApp",
            "icon": "💬",
            "requires": ["phone_number_id", "access_token", "verify_token"],
            "setup_type": "webhook",
            "description": "Requires WhatsApp Business API credentials",
            "docs_url": "https://developers.facebook.com/docs/whatsapp",
        },
        "microsoft_teams": {
            "name": "Microsoft Teams",
            "icon": "👥",
            "requires": ["app_id", "app_password"],
            "setup_type": "webhook",
            "description": "Requires Azure AD app registration",
            "docs_url": "https://docs.microsoft.com/en-us/microsoftteams/platform/",
        },
        "signal": {
            "name": "Signal",
            "icon": "🔔",
            "requires": ["phone_number", "sgnal_cli_path"],
            "setup_type": "cli",
            "description": "Requires signal-cli installation",
            "docs_url": "https://github.com/AsamK/signal-cli",
        },
        "google_chat": {
            "name": "Google Chat",
            "icon": "💬",
            "requires": ["credentials_json"],
            "setup_type": "webhook",
            "description": "Requires Google Cloud service account",
            "docs_url": "https://developers.google.com/chat/how-to",
        },
        "imessage": {
            "name": "iMessage",
            "icon": "🍎",
            "requires": ["mac_address"],
            "setup_type": "mac",
            "description": "Requires Mac with AppleScript enabled",
            "docs_url": "https://support.apple.com/guide/mac-help/",
        },
    }

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "operation": ToolParameter(
                name="operation",
                type="string",
                description="Operation: 'list', 'status', 'configure', 'enable', 'disable', 'setup'",
                required=True,
                enum=[
                    "list",
                    "status",
                    "configure",
                    "enable",
                    "disable",
                    "setup",
                    "test",
                ],
            ),
            "channel": ToolParameter(
                name="channel",
                type="string",
                description=f"Channel name: {', '.join(self.SUPPORTED_CHANNELS.keys())}",
                required=False,
                enum=list(self.SUPPORTED_CHANNELS.keys()),
            ),
            "credentials": ToolParameter(
                name="credentials",
                type="string",
                description='JSON credentials for the channel (e.g., \'{"bot_token": "xxx"}\')',
                required=False,
                default="{}",
            ),
            "settings": ToolParameter(
                name="settings",
                type="string",
                description='JSON settings for the channel (e.g., \'{"prefix": "!", "channels": ["general"]}\')',
                required=False,
                default="{}",
            ),
        }

    def _load_config(self) -> dict:
        """Load channel configuration from file."""
        if self.CHANNELS_CONFIG_PATH.exists():
            return json.loads(self.CHANNELS_CONFIG_PATH.read_text())
        return {"channels": {}}

    def _save_config(self, config: dict) -> None:
        """Save channel configuration to file."""
        self.CHANNELS_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.CHANNELS_CONFIG_PATH.write_text(json.dumps(config, indent=2))

    async def execute(
        self,
        operation: str,
        channel: str | None = None,
        credentials: str = "{}",
        settings: str = "{}",
    ) -> ToolResult:
        """Execute channel management operation."""
        start_time = __import__("time").time()

        try:
            config = self._load_config()
            credentials = json.loads(credentials) if credentials else {}
            settings = json.loads(settings) if settings else {}

            if operation == "list":
                return await self._list_channels(config)

            elif operation == "status":
                if not channel:
                    return ToolResult(
                        success=False,
                        error="'channel' is required for status operation",
                    )
                return await self._get_channel_status(channel, config)

            elif operation == "configure":
                if not channel:
                    return ToolResult(
                        success=False,
                        error="'channel' is required for configure operation",
                    )
                return await self._configure_channel(
                    channel, credentials, settings, config
                )

            elif operation == "enable":
                if not channel:
                    return ToolResult(
                        success=False,
                        error="'channel' is required for enable operation",
                    )
                return await self._enable_channel(channel, config)

            elif operation == "disable":
                if not channel:
                    return ToolResult(
                        success=False,
                        error="'channel' is required for disable operation",
                    )
                return await self._disable_channel(channel, config)

            elif operation == "setup":
                if not channel:
                    return ToolResult(
                        success=False, error="'channel' is required for setup operation"
                    )
                return await self._get_setup_instructions(channel)

            elif operation == "test":
                if not channel:
                    return ToolResult(
                        success=False, error="'channel' is required for test operation"
                    )
                return await self._test_channel(channel, config)

            else:
                return ToolResult(
                    success=False, error=f"Unknown operation: {operation}"
                )

        except json.JSONDecodeError as e:
            return ToolResult(
                success=False,
                error=f"Invalid JSON: {str(e)}",
                execution_time_ms=int((__import__("time").time() - start_time) * 1000),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Channel operation failed: {str(e)}",
                execution_time_ms=int((__import__("time").time() - start_time) * 1000),
            )

    async def _list_channels(self, config: dict) -> ToolResult:
        """List all supported channels and their status."""
        lines = ["# Available Channels\n"]

        for channel_id, channel_info in self.SUPPORTED_CHANNELS.items():
            status = (
                config.get("channels", {}).get(channel_id, {}).get("enabled", False)
            )
            status_icon = "✅" if status else "❌"
            lines.append(
                f"{status_icon} **{channel_info['icon']} {channel_info['name']}** (`{channel_id}`)"
            )
            lines.append(f"   {channel_info['description']}")

        lines.append("\n# Configured Channels")
        configured = [
            c for c, cfg in config.get("channels", {}).items() if cfg.get("enabled")
        ]
        if configured:
            for c in configured:
                lines.append(f"  - `{c}`")
        else:
            lines.append("  None configured")

        lines.append("\n# Quick Setup Examples:")
        lines.append("```")
        lines.append('channel_manager(operation="setup", channel="telegram")')
        lines.append(
            'channel_manager(operation="configure", channel="discord", credentials=\'{"bot_token": "xxx"}\')'
        )
        lines.append('channel_manager(operation="enable", channel="telegram")')
        lines.append("```")

        return ToolResult(
            success=True,
            data={
                "channels": self.SUPPORTED_CHANNELS,
                "configured": list(config.get("channels", {}).keys()),
            },
            stdout="\n".join(lines),
            execution_time_ms=0,
        )

    async def _get_channel_status(self, channel: str, config: dict) -> ToolResult:
        """Get status of a specific channel."""
        if channel not in self.SUPPORTED_CHANNELS:
            return ToolResult(
                success=False,
                error=f"Unknown channel: {channel}. Supported: {', '.join(self.SUPPORTED_CHANNELS.keys())}",
            )

        channel_info = self.SUPPORTED_CHANNELS[channel]
        channel_config = config.get("channels", {}).get(channel, {})
        is_configured = bool(channel_config.get("credentials"))
        is_enabled = channel_config.get("enabled", False)

        lines = [
            f"# {channel_info['icon']} {channel_info['name']}",
            f"**Status:** {'✅ Enabled' if is_enabled else '❌ Disabled'}",
            f"**Configured:** {'Yes' if is_configured else 'No'}",
            "",
            f"**Requirements:** {', '.join(channel_info['requires'])}",
            f"**Setup Type:** {channel_info['setup_type']}",
            "",
            f"**Documentation:** {channel_info['docs_url']}",
        ]

        if channel_config:
            lines.append("\n**Current Config:**")
            safe_config = {
                k: "***" if "token" in k or "secret" in k else v
                for k, v in channel_config.items()
            }
            for key, value in safe_config.items():
                lines.append(f"  - {key}: {value}")

        return ToolResult(
            success=True,
            data={
                "channel": channel,
                "configured": is_configured,
                "enabled": is_enabled,
                "requirements": channel_info["requires"],
            },
            stdout="\n".join(lines),
            execution_time_ms=0,
        )

    async def _configure_channel(
        self, channel: str, credentials: dict, settings: dict, config: dict
    ) -> ToolResult:
        """Configure a channel with credentials."""
        if channel not in self.SUPPORTED_CHANNELS:
            return ToolResult(success=False, error=f"Unknown channel: {channel}")

        channel_info = self.SUPPORTED_CHANNELS[channel]
        missing = [req for req in channel_info["requires"] if req not in credentials]

        if missing:
            return ToolResult(
                success=False,
                error=f"Missing required credentials for {channel}: {', '.join(missing)}",
            )

        if "channels" not in config:
            config["channels"] = {}

        config["channels"][channel] = {
            "enabled": False,
            "credentials": credentials,
            "settings": settings,
            "configured_at": __import__("datetime").datetime.utcnow().isoformat(),
        }

        self._save_config(config)

        lines = [
            f"✅ **Channel `{channel}` configured successfully!**",
            "",
            "**Next steps:**",
            f"1. Run: `channel_manager(operation='enable', channel='{channel}')`",
            f"2. Set up webhook in {channel}: `POST https://your-domain.com/api/v1/channels/{channel}/webhook`",
        ]

        return ToolResult(
            success=True,
            data={"channel": channel, "configured": True},
            stdout="\n".join(lines),
            execution_time_ms=0,
        )

    async def _enable_channel(self, channel: str, config: dict) -> ToolResult:
        """Enable a configured channel."""
        if channel not in config.get("channels", {}):
            return ToolResult(
                success=False,
                error=f"Channel `{channel}` not configured. Run configure first.",
            )

        config["channels"][channel]["enabled"] = True
        self._save_config(config)

        return ToolResult(
            success=True,
            data={"channel": channel, "enabled": True},
            stdout=f"✅ **Channel `{channel}` enabled!**",
            execution_time_ms=0,
        )

    async def _disable_channel(self, channel: str, config: dict) -> ToolResult:
        """Disable a channel."""
        if channel not in config.get("channels", {}):
            config["channels"][channel] = {"enabled": False}

        config["channels"][channel]["enabled"] = False
        self._save_config(config)

        return ToolResult(
            success=True,
            data={"channel": channel, "enabled": False},
            stdout=f"✅ **Channel `{channel}` disabled!**",
            execution_time_ms=0,
        )

    async def _get_setup_instructions(self, channel: str) -> ToolResult:
        """Get detailed setup instructions for a channel."""
        if channel not in self.SUPPORTED_CHANNELS:
            return ToolResult(success=False, error=f"Unknown channel: {channel}")

        channel_info = self.SUPPORTED_CHANNELS[channel]

        instructions = {
            "telegram": """## Telegram Setup

1. **Create a bot:**
   - Open Telegram and chat with @BotFather
   - Send `/newbot` and follow the prompts
   - Copy the bot token (looks like: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`)

2. **Configure:**
   ```python
   channel_manager(operation="configure", channel="telegram", credentials='{
     "bot_token": "YOUR_BOT_TOKEN"
   }')
   ```

3. **Set webhook URL:**
   ```
   https://your-domain.com/api/v1/channels/telegram/webhook
   ```
   """,
            "discord": """## Discord Setup

1. **Create application:**
   - Go to https://discord.com/developers/applications
   - Create New Application

2. **Add Bot:**
   - Go to Bot tab
   - Click "Add Bot"
   - Copy the bot token

3. **Enable Intents:**
   - In Bot settings, enable:
     - SERVER MEMBERS INTENT
     - MESSAGE CONTENT INTENT

4. **Invite Link:**
   ```
   https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&scope=bot
   ```

5. **Configure:**
   ```python
   channel_manager(operation="configure", channel="discord", credentials='{
     "bot_token": "YOUR_BOT_TOKEN"
   }')
   ```
   """,
            "slack": """## Slack Setup

1. **Create app:**
   - Go to https://api.slack.com/apps
   - Create New App > From scratch

2. **Add permissions:**
   - Go to OAuth & Permissions
   - Add Scopes: `chat:write`, `channels:read`, `channels:history`, `im:read`, `im:history`

3. **Install to workspace:**
   - Click "Install to Workspace"
   - Copy Bot User OAuth Token (starts with `xoxb-`)

4. **Get Signing Secret:**
   - Basic Information > App Credentials > Signing Secret

5. **Configure:**
   ```python
   channel_manager(operation="configure", channel="slack", credentials='{
     "bot_token": "xoxb-xxx",
     "signing_secret": "xxx"
   }')
   ```
   """,
            "whatsapp": """## WhatsApp Setup (Meta Business API)

1. **Create Meta Business Account:**
   - Go to business.facebook.com
   - Create account

2. **Set up WhatsApp Business:**
   - Add phone number (can't be used on regular WhatsApp)
   - Get Phone Number ID

3. **Create App:**
   - Go to developers.facebook.com
   - Create App > Business

4. **Add WhatsApp Product:**
   - Add WhatsApp to your app
   - Configure webhooks

5. **Get Credentials:**
   - Permanent Token from Meta Business
   - Phone Number ID
   - Verify Token (random string you choose)

6. **Configure:**
   ```python
   channel_manager(operation="configure", channel="whatsapp", credentials='{
     "phone_number_id": "xxx",
     "access_token": "xxx",
     "verify_token": "your_verify_token"
   }')
   ```
   """,
            "microsoft_teams": """## Microsoft Teams Setup

1. **Create Azure AD App:**
   - Go to portal.azure.com > Azure Active Directory
   - App registrations > New registration

2. **Configure:**
   - Set Redirect URI: `https://your-domain.com/api/v1/channels/microsoft_teams/callback`
   - Add Client Secret in Certificates & secrets

3. **Enable Permissions:**
   - API permissions > Add Microsoft Graph:
     - `Channel.ReadBasic.All`
     - `ChannelMessage.Read.All`
     - `Chat.Read`
     - `Chat.ReadWrite`

4. **Configure ngrok for local dev:**
   ```
   ngrok http 8000
   ```

5. **Configure:**
   ```python
   channel_manager(operation="configure", channel="microsoft_teams", credentials='{
     "app_id": "xxx",
     "app_password": "xxx",
     "tenant_id": "xxx"
   }')
   ```
   """,
            "signal": """## Signal Setup

1. **Install signal-cli:**
   ```bash
   # Ubuntu/Debian
   sudo apt install signal-cli
   
   # macOS
   brew install signal-cli
   ```

2. **Link your number:**
   ```bash
   signal-cli link -n "Qubot"
   # Scan QR code with Signal app
   ```

3. **Get config path:**
   ```bash
   signal-cli config
   ```

4. **Configure:**
   ```python
   channel_manager(operation="configure", channel="signal", credentials='{
     "phone_number": "+1234567890",
     "signal_cli_path": "/usr/local/bin/signal-cli"
   }')
   ```
   """,
            "google_chat": """## Google Chat Setup

1. **Create Google Cloud Project:**
   - Go to console.cloud.google.com
   - Create new project

2. **Enable Chat API:**
   - APIs & Services > Enable API
   - Search "Google Chat API" and enable

3. **Configure Chat API:**
   - Google Chat API > Configuration
   - Set App name, avatar
   - Enable "Bot works in direct messages"

4. **Create Service Account:**
   - IAM & Admin > Service Accounts
   - Create key in JSON format

5. **Download credentials JSON** and configure:
   ```python
   channel_manager(operation="configure", channel="google_chat", credentials='{
     "credentials_json": "path/to/credentials.json"
   }')
   ```
   """,
            "imessage": """## iMessage Setup (Mac only)

1. **Enable AppleScript:**
   - System Preferences > Security & Privacy > Privacy > Automation
   - Allow Terminal/Apps to control iMessage

2. **Enable Remote Apple Events:**
   - System Preferences > Sharing > Enable Remote Apple Events

3. **Note Mac's IP address:**
   ```bash
   ipconfig getifaddr en0
   ```

4. **Configure:**
   ```python
   channel_manager(operation="configure", channel="imessage", credentials='{
     "mac_address": "192.168.1.100",
     "mac_username": "your-mac-username"
   }')
   ```
   """,
        }

        content = instructions.get(
            channel, f"# {channel_info['name']}\n\nSetup instructions not available."
        )

        return ToolResult(
            success=True,
            data={
                "channel": channel,
                "name": channel_info["name"],
                "requires": channel_info["requires"],
                "docs_url": channel_info["docs_url"],
            },
            stdout=content,
            execution_time_ms=0,
        )

    async def _test_channel(self, channel: str, config: dict) -> ToolResult:
        """Test a channel connection."""
        channel_config = config.get("channels", {}).get(channel)

        if not channel_config:
            return ToolResult(
                success=False, error=f"Channel `{channel}` not configured"
            )

        if not channel_config.get("enabled"):
            return ToolResult(
                success=False,
                error=f"Channel `{channel}` is disabled. Enable it first.",
            )

        return ToolResult(
            success=True,
            data={"channel": channel, "test": "pending"},
            stdout=f"🔄 Testing `{channel}` connection...\n\nThis will send a test message to verify the setup. Check your {self.SUPPORTED_CHANNELS.get(channel, {}).get('name', channel)} bot/app.",
            execution_time_ms=0,
        )
