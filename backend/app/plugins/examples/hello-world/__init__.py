"""
Hello World Plugin for Qubot

Example plugin demonstrating the Qubot Plugin SDK.
This plugin provides a simple greeting tool.

Usage:
    from app.plugins import get_plugin_manager

    manager = get_plugin_manager()
    plugin = manager.get_plugin("hello-world")

    result = await plugin.execute({"name": "User"})
"""

from typing import Any

from app.plugins.base import BasePlugin, PluginInfo, PluginType


class HelloWorldPlugin(BasePlugin):
    """Example plugin that provides greeting functionality."""

    async def initialize(self) -> None:
        """Initialize the plugin."""
        await super().initialize()

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the greeting tool.

        Args:
            params: Dictionary with 'name' key for the person to greet

        Returns:
            Dictionary with greeting message
        """
        name = params.get("name", "World")
        greeting = self.config.get("greeting", "Hello")
        use_emoji = self.config.get("use_emoji", True)

        emoji = "👋 " if use_emoji else ""
        message = f"{emoji}{greeting}, {name}! Welcome to Qubot."

        return {
            "success": True,
            "message": message,
            "params": params,
        }

    def get_schema(self) -> dict[str, Any]:
        """Return the tool schema for LLM function calling."""
        return {
            "type": "function",
            "function": {
                "name": "hello_world",
                "description": "Send a friendly greeting to someone",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the person to greet",
                        },
                    },
                    "required": ["name"],
                },
            },
        }


def get_plugin() -> BasePlugin:
    """Entry point for the plugin loader."""
    return HelloWorldPlugin()
