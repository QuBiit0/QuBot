"""
Notification Tool - Send proactive notifications to Slack, Discord, or any webhook.
Agents can report progress, alert on errors, and push updates without being asked.
"""

import json
import time

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


class NotificationTool(BaseTool):
    """
    Send notifications to Slack, Discord, Microsoft Teams, or any custom webhook.
    Agents use this to proactively report results, errors, or status updates.

    Configure via environment variables:
      SLACK_WEBHOOK_URL    - Slack Incoming Webhook URL
      DISCORD_WEBHOOK_URL  - Discord Webhook URL
      TEAMS_WEBHOOK_URL    - Microsoft Teams Connector URL

    Operations: slack, discord, teams, webhook (generic HTTP POST)
    """

    name = "notification"
    description = (
        "Send notifications to Slack, Discord, Teams, or custom webhooks. "
        "Use to proactively report task results, errors, progress updates, or alerts. "
        "Supports rich formatting: message blocks, embeds, markdown, @mentions."
    )
    category = ToolCategory.COMMUNICATION
    risk_level = ToolRiskLevel.NORMAL

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "channel": ToolParameter(
                name="channel",
                type="string",
                description="Target channel: 'slack', 'discord', 'teams', or 'webhook'",
                required=True,
                enum=["slack", "discord", "teams", "webhook"],
            ),
            "message": ToolParameter(
                name="message",
                type="string",
                description="Main message text (supports markdown for Slack/Discord)",
                required=True,
            ),
            "title": ToolParameter(
                name="title",
                type="string",
                description="Optional title/heading for the notification",
                required=False,
                default=None,
            ),
            "color": ToolParameter(
                name="color",
                type="string",
                description="Accent color: 'green' (success), 'red' (error), 'yellow' (warning), 'blue' (info), or hex '#ff0000'",
                required=False,
                default="blue",
            ),
            "fields": ToolParameter(
                name="fields",
                type="array",
                description="Additional fields as [{'title': 'Key', 'value': 'Val', 'short': true}]",
                required=False,
                default=None,
            ),
            "webhook_url": ToolParameter(
                name="webhook_url",
                type="string",
                description="Override webhook URL (optional, uses env var default)",
                required=False,
                default=None,
            ),
            "webhook_payload": ToolParameter(
                name="webhook_payload",
                type="object",
                description="Custom JSON payload for 'webhook' channel (replaces default format)",
                required=False,
                default=None,
            ),
            "mention": ToolParameter(
                name="mention",
                type="string",
                description="User/role to mention: '@here', '@channel', user ID, etc.",
                required=False,
                default=None,
            ),
        }

    def _validate_config(self) -> None:
        import os
        self.slack_webhook = self.config.get("slack_webhook") or os.getenv("SLACK_WEBHOOK_URL", "")
        self.discord_webhook = self.config.get("discord_webhook") or os.getenv("DISCORD_WEBHOOK_URL", "")
        self.teams_webhook = self.config.get("teams_webhook") or os.getenv("TEAMS_WEBHOOK_URL", "")

    def _resolve_color(self, color: str) -> str:
        """Resolve color name to hex."""
        colors = {
            "green": "#2eb886", "red": "#e01e5a", "yellow": "#ecb22e",
            "blue": "#36c5f0", "purple": "#9c3ac7", "orange": "#f59e0b",
        }
        return colors.get(color.lower(), color if color.startswith("#") else "#36c5f0")

    def _build_slack_payload(self, message: str, title: str | None, color: str,
                             fields: list | None, mention: str | None) -> dict:
        hex_color = self._resolve_color(color)
        text = f"{mention} " if mention else ""
        text += message

        attachment: dict = {"color": hex_color, "text": message, "fallback": message}
        if title:
            attachment["title"] = title
        if fields:
            attachment["fields"] = fields

        return {"text": text if mention else None, "attachments": [attachment]}

    def _build_discord_payload(self, message: str, title: str | None, color: str,
                                fields: list | None, mention: str | None) -> dict:
        hex_color = self._resolve_color(color).lstrip("#")
        color_int = int(hex_color, 16)

        embed: dict = {"description": message, "color": color_int}
        if title:
            embed["title"] = title
        if fields:
            embed["fields"] = [
                {"name": f.get("title", ""), "value": f.get("value", ""), "inline": f.get("short", False)}
                for f in fields
            ]

        content = mention or ""
        return {"content": content or None, "embeds": [embed]}

    def _build_teams_payload(self, message: str, title: str | None, color: str,
                              fields: list | None) -> dict:
        hex_color = self._resolve_color(color).lstrip("#")
        payload: dict = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "themeColor": hex_color,
            "summary": title or message[:50],
            "sections": [{"activityText": message}],
        }
        if title:
            payload["title"] = title
        if fields:
            payload["sections"][0]["facts"] = [
                {"name": f.get("title", ""), "value": f.get("value", "")} for f in fields
            ]
        return payload

    async def _post(self, url: str, payload: dict) -> tuple[int, str]:
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx not installed")

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            try:
                return resp.status_code, resp.text
            except Exception:
                return resp.status_code, ""

    async def execute(
        self,
        channel: str,
        message: str,
        title: str | None = None,
        color: str = "blue",
        fields: list | None = None,
        webhook_url: str | None = None,
        webhook_payload: dict | None = None,
        mention: str | None = None,
    ) -> ToolResult:
        start_time = time.time()

        try:
            if channel == "slack":
                url = webhook_url or self.slack_webhook
                if not url:
                    return ToolResult(success=False, error="SLACK_WEBHOOK_URL not configured")
                payload = self._build_slack_payload(message, title, color, fields, mention)

            elif channel == "discord":
                url = webhook_url or self.discord_webhook
                if not url:
                    return ToolResult(success=False, error="DISCORD_WEBHOOK_URL not configured")
                payload = self._build_discord_payload(message, title, color, fields, mention)

            elif channel == "teams":
                url = webhook_url or self.teams_webhook
                if not url:
                    return ToolResult(success=False, error="TEAMS_WEBHOOK_URL not configured")
                payload = self._build_teams_payload(message, title, color, fields)

            elif channel == "webhook":
                if not webhook_url:
                    return ToolResult(success=False, error="webhook_url is required for 'webhook' channel")
                url = webhook_url
                payload = webhook_payload or {"text": message, "title": title}

            else:
                return ToolResult(success=False, error=f"Unknown channel: {channel}")

            status, response = await self._post(url, payload)
            success = 200 <= status < 300

            return ToolResult(
                success=success,
                data={"channel": channel, "status": status, "response": response[:200]},
                stdout=f"Notification sent to {channel}: {title or message[:50]}",
                error=f"HTTP {status}: {response[:200]}" if not success else None,
                execution_time_ms=int((time.time() - start_time) * 1000),
                metadata={"channel": channel, "status_code": status},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Notification failed: {e}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
