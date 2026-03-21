"""
Qubot Plugin System

Plugins extend Qubot with custom channels, tools, skills, and integrations.

Structure:
    plugins/
    ├── example-plugin/
    │   ├── plugin.json       # Manifest
    │   ├── __init__.py      # Plugin entry point
    │   └── ...

Usage:
    from app.plugins import get_plugin_manager

    manager = get_plugin_manager()
    await manager.initialize()

    plugins = manager.list_plugins()
"""

from .base import (
    BasePlugin,
    ChannelPlugin,
    IntegrationPlugin,
    PluginInfo,
    PluginState,
    PluginType,
    ToolPlugin,
)
from .loader import PluginLoader, get_plugin_loader
from .manager import PluginManager, get_plugin_manager

__all__ = [
    "BasePlugin",
    "ChannelPlugin",
    "IntegrationPlugin",
    "PluginInfo",
    "PluginLoader",
    "PluginManager",
    "PluginState",
    "PluginType",
    "ToolPlugin",
    "get_plugin_loader",
    "get_plugin_manager",
]
