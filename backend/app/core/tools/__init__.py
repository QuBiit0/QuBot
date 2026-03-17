"""
Qubot Tools - Built-in tool implementations
"""

# Re-export from providers for convenience
from ..providers.base import ToolDefinition
from .base import (
    BaseTool,
    ToolCategory,
    ToolParameter,
    ToolRegistry,
    ToolResult,
    ToolRiskLevel,
    get_tool_registry,
)
from .browser_tool import WebBrowserTool
from .filesystem_tool import FilesystemTool
from .http_tool import HttpApiTool
from .playwright_tool import PlaywrightBrowserTool
from .scheduler_tool import SchedulerTool
from .shell_tool import SystemShellTool
from .web_search_tool import WebSearchTool

__all__ = [
    # Base classes
    "BaseTool",
    "ToolResult",
    "ToolParameter",
    "ToolCategory",
    "ToolRiskLevel",
    "ToolRegistry",
    "get_tool_registry",
    "ToolDefinition",
    # Tool implementations
    "HttpApiTool",
    "SystemShellTool",
    "WebBrowserTool",
    "FilesystemTool",
    "SchedulerTool",
    "WebSearchTool",
    "PlaywrightBrowserTool",
]


def register_default_tools(config: dict = None) -> ToolRegistry:
    """
    Register all default tools with the global registry.

    Args:
        config: Configuration dictionary for tools

    Returns:
        ToolRegistry with all tools registered
    """
    registry = get_tool_registry()
    config = config or {}

    # Register tools
    registry.register(HttpApiTool, config.get("http", {}))
    registry.register(SystemShellTool, config.get("shell", {}))
    registry.register(WebBrowserTool, config.get("browser", {}))
    registry.register(FilesystemTool, config.get("filesystem", {}))
    registry.register(SchedulerTool, config.get("scheduler", {}))
    registry.register(WebSearchTool, config.get("web_search", {}))
    registry.register(PlaywrightBrowserTool, config.get("playwright", {}))

    return registry
