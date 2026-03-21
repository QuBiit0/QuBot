"""
Plugin System Base - Abstract interfaces for Qubot plugins

This module defines the base classes and interfaces for all Qubot plugins.
Plugins can extend: Channels, Tools, Skills, and Integrations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from pathlib import Path


class PluginType(str, Enum):
    """Types of plugins supported by Qubot."""

    CHANNEL = "channel"
    TOOL = "tool"
    SKILL = "skill"
    INTEGRATION = "integration"
    PROVIDER = "provider"


class PluginState(str, Enum):
    """Plugin lifecycle states."""

    DISCOVERED = "discovered"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginInfo:
    """Plugin metadata."""

    id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    file_path: Path | None = None


class BasePlugin(ABC):
    """
    Abstract base class for all Qubot plugins.

    Plugins must implement:
    - get_info(): Return PluginInfo metadata
    - initialize(): Setup plugin resources
    - shutdown(): Cleanup plugin resources

    Optional:
    - validate_config(): Validate plugin configuration
    - get_routes(): Register API routes (for web plugins)
    """

    def __init__(self):
        self._state = PluginState.DISCOVERED
        self._config: dict[str, Any] = {}
        self._info: PluginInfo | None = None

    @property
    def state(self) -> PluginState:
        """Get current plugin state."""
        return self._state

    @property
    def info(self) -> PluginInfo | None:
        """Get plugin info."""
        return self._info

    @property
    def config(self) -> dict[str, Any]:
        """Get plugin configuration."""
        return self._config

    def set_config(self, config: dict[str, Any]) -> None:
        """Set plugin configuration."""
        self._config = config

    @abstractmethod
    def get_info(self) -> PluginInfo:
        """Return plugin metadata."""
        pass

    async def initialize(self) -> None:
        """
        Initialize plugin resources.
        Override for async initialization.
        """
        self._state = PluginState.INITIALIZED

    async def shutdown(self) -> None:
        """
        Shutdown plugin and cleanup resources.
        Override for cleanup logic.
        """
        self._state = PluginState.DISABLED

    def validate_config(self, config: dict[str, Any]) -> tuple[bool, str | None]:
        """
        Validate plugin configuration.
        Returns (is_valid, error_message).
        Override for custom validation.
        """
        return True, None

    def get_routes(self) -> list[Any]:
        """
        Return list of FastAPI routes to register.
        Override for web plugins.
        """
        return []


class ChannelPlugin(ABC):
    """Base class for messaging channel plugins."""

    @abstractmethod
    async def handle_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle incoming webhook."""
        pass

    @abstractmethod
    async def send_message(self, recipient: str, message: str) -> bool:
        """Send message to recipient."""
        pass

    async def setup_webhook(self, webhook_url: str) -> None:
        """Setup webhook for channel."""
        pass

    async def teardown_webhook(self) -> None:
        """Remove webhook configuration."""
        pass


class ToolPlugin(ABC):
    """Base class for tool plugins."""

    @abstractmethod
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute tool with parameters."""
        pass

    @abstractmethod
    def get_schema(self) -> dict[str, Any]:
        """Return tool schema for LLM."""
        pass


class IntegrationPlugin(ABC):
    """Base class for integration plugins."""

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to external service."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from external service."""
        pass

    async def get_status(self) -> dict[str, Any]:
        """Get integration status."""
        return {"connected": False, "status": "unknown"}
