"""
Plugin Loader - Discovers and loads Qubot plugins

Handles plugin discovery from filesystem, validation, and loading.
"""

import importlib
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.config import settings
from .base import BasePlugin, PluginInfo, PluginState, PluginType

logger = get_logger(__name__)


def get_plugins_base_path() -> Path:
    """Get plugins base path from settings."""
    return Path(settings.PLUGINS_PATH)


class PluginLoadError(Exception):
    """Error loading a plugin."""


class PluginLoader:
    """
    Discovers and loads plugins from the filesystem.

    Expected structure:
    plugins/
    ├── my-plugin/
    │   ├── plugin.json       # Plugin manifest
    │   ├── __init__.py      # Main plugin module
    │   └── ...              # Supporting files
    """

    def __init__(self):
        self._plugins: dict[str, BasePlugin] = {}
        self._plugin_info: dict[str, PluginInfo] = {}

    def discover(self, path: Path | None = None) -> list[PluginInfo]:
        """Discover all plugins in the plugins directory."""
        plugins_path = path or get_plugins_base_path()
        discovered = []

        if not plugins_path.exists():
            logger.info(f"Plugins directory does not exist: {plugins_path}")
            return []

        for plugin_dir in plugins_path.iterdir():
            if not plugin_dir.is_dir():
                continue

            manifest_file = plugin_dir / "plugin.json"
            if not manifest_file.exists():
                continue

            try:
                manifest = json.loads(manifest_file.read_text())
                info = PluginInfo(
                    id=manifest.get("id", plugin_dir.name),
                    name=manifest.get("name", plugin_dir.name),
                    version=manifest.get("version", "1.0.0"),
                    description=manifest.get("description", ""),
                    author=manifest.get("author", "unknown"),
                    plugin_type=PluginType(manifest.get("type", "tool")),
                    dependencies=manifest.get("dependencies", []),
                    config_schema=manifest.get("config_schema", {}),
                    file_path=plugin_dir,
                )
                discovered.append(info)
                logger.info(f"Discovered plugin: {info.name} v{info.version}")
            except Exception as e:
                logger.warning(f"Failed to parse plugin manifest {manifest_file}: {e}")

        return discovered

    def load_plugin(self, info: PluginInfo) -> BasePlugin:
        """
        Load a plugin from its directory.

        Expects:
        - plugin.json: manifest file
        - __init__.py or main.py: plugin entry point with `get_plugin()` function
        """
        if not info.file_path:
            raise PluginLoadError(f"No file path for plugin {info.id}")

        plugin_dir = info.file_path

        init_file = plugin_dir / "__init__.py"
        main_file = plugin_dir / "main.py"

        entry_file = None
        if init_file.exists():
            entry_file = init_file
        elif main_file.exists():
            entry_file = main_file

        if not entry_file:
            raise PluginLoadError(f"Plugin {info.id} has no __init__.py or main.py")

        try:
            spec = importlib.util.spec_from_file_location(
                f"qubot.plugins.{info.id}", entry_file
            )
            if not spec or not spec.loader:
                raise PluginLoadError(f"Failed to load spec for {info.id}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, "get_plugin"):
                raise PluginLoadError(
                    f"Plugin {info.id} does not define get_plugin() function"
                )

            plugin = module.get_plugin()
            if not isinstance(plugin, BasePlugin):
                raise PluginLoadError(
                    f"Plugin {info.id}.get_plugin() does not return BasePlugin"
                )

            plugin._info = info
            plugin._state = PluginState.LOADED

            self._plugins[info.id] = plugin
            self._plugin_info[info.id] = info

            logger.info(f"Loaded plugin: {info.name} v{info.version}")
            return plugin

        except Exception as e:
            logger.error(f"Failed to load plugin {info.id}: {e}")
            raise PluginLoadError(f"Failed to load plugin {info.id}: {e}")

    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin by ID."""
        if plugin_id in self._plugins:
            plugin = self._plugins.pop(plugin_id)
            self._plugin_info.pop(plugin_id, None)
            plugin._state = PluginState.DISABLED
            logger.info(f"Unloaded plugin: {plugin_id}")
            return True
        return False

    def get_plugin(self, plugin_id: str) -> BasePlugin | None:
        """Get a loaded plugin by ID."""
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> list[PluginInfo]:
        """List all loaded plugin info."""
        return list(self._plugin_info.values())


_loader: PluginLoader | None = None


def get_plugin_loader() -> PluginLoader:
    """Get or create global plugin loader."""
    global _loader
    if _loader is None:
        _loader = PluginLoader()
    return _loader
