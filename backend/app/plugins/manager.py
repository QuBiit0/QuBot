"""
Plugin Manager Service - Manages plugin lifecycle and integration

Provides high-level plugin management including:
- Plugin discovery and loading
- Configuration management
- Integration with tools and channels
- Hot-reload support
"""

import asyncio
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.config import settings
from .base import BasePlugin, PluginInfo, PluginState, PluginType
from .loader import PluginLoader, get_plugin_loader

logger = get_logger(__name__)


class PluginManager:
    """
    Manages plugin lifecycle and integration with Qubot.

    Handles:
    - Plugin discovery and loading
    - Configuration management
    - Tool and channel registration
    - Hot-reload support
    """

    def __init__(self):
        self._loader = get_plugin_loader()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize plugin system and load all plugins."""
        if self._initialized:
            return

        plugins_path = Path(getattr(settings, "PLUGINS_PATH", "/app/plugins"))

        discovered = self._loader.discover(plugins_path)

        for info in discovered:
            try:
                plugin = self._loader.load_plugin(info)
                await plugin.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize plugin {info.id}: {e}")

        self._initialized = True
        logger.info(f"Plugin system initialized with {len(discovered)} plugins")

    async def shutdown(self) -> None:
        """Shutdown all plugins and cleanup."""
        for plugin_id in list(self._loader._plugins.keys()):
            plugin = self._loader.get_plugin(plugin_id)
            if plugin:
                try:
                    await plugin.shutdown()
                except Exception as e:
                    logger.error(f"Failed to shutdown plugin {plugin_id}: {e}")

        self._loader._plugins.clear()
        self._initialized = False
        logger.info("Plugin system shutdown complete")

    async def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a disabled plugin."""
        plugin = self._loader.get_plugin(plugin_id)
        if not plugin:
            return False

        try:
            await plugin.initialize()
            return True
        except Exception as e:
            logger.error(f"Failed to enable plugin {plugin_id}: {e}")
            return False

    async def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin."""
        plugin = self._loader.get_plugin(plugin_id)
        if not plugin:
            return False

        try:
            await plugin.shutdown()
            return True
        except Exception as e:
            logger.error(f"Failed to disable plugin {plugin_id}: {e}")
            return False

    async def reload_plugin(self, plugin_id: str) -> bool:
        """Hot-reload a plugin."""
        plugin_info = self._loader._plugin_info.get(plugin_id)
        if not plugin_info:
            return False

        try:
            await self.disable_plugin(plugin_id)
            self._loader.unload_plugin(plugin_id)
            plugin = self._loader.load_plugin(plugin_info)
            await plugin.initialize()
            return True
        except Exception as e:
            logger.error(f"Failed to reload plugin {plugin_id}: {e}")
            return False

    def configure_plugin(self, plugin_id: str, config: dict[str, Any]) -> bool:
        """Configure a plugin."""
        plugin = self._loader.get_plugin(plugin_id)
        if not plugin:
            return False

        is_valid, error = plugin.validate_config(config)
        if not is_valid:
            logger.error(f"Invalid config for plugin {plugin_id}: {error}")
            return False

        plugin.set_config(config)
        return True

    def get_plugin(self, plugin_id: str) -> BasePlugin | None:
        """Get a plugin by ID."""
        return self._loader.get_plugin(plugin_id)

    def list_plugins(self, plugin_type: PluginType | None = None) -> list[PluginInfo]:
        """List plugins, optionally filtered by type."""
        plugins = self._loader.list_plugins()
        if plugin_type:
            plugins = [p for p in plugins if p.plugin_type == plugin_type]
        return plugins

    def get_tools_from_plugins(self) -> list[dict[str, Any]]:
        """Get all tool schemas from tool plugins."""
        tools = []
        for plugin in self._loader._plugins.values():
            if hasattr(plugin, "get_schema"):
                try:
                    tools.append(plugin.get_schema())
                except Exception as e:
                    logger.error(
                        f"Failed to get schema from plugin {plugin.info.id}: {e}"
                    )
        return tools

    def get_channel_handlers(self) -> dict[str, BasePlugin]:
        """Get all channel plugins."""
        channels = {}
        for info in self._loader.list_plugins():
            if info.plugin_type == PluginType.CHANNEL:
                plugin = self._loader.get_plugin(info.id)
                if plugin:
                    channels[info.id] = plugin
        return channels


_plugin_manager: PluginManager | None = None


def get_plugin_manager() -> PluginManager:
    """Get or create global plugin manager."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
