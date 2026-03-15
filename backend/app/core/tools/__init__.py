"""
Qubot Tools - Built-in tool implementations
"""
from .base import (
    BaseTool,
    ToolResult,
    ToolParameter,
    ToolCategory,
    ToolRiskLevel,
    ToolRegistry,
    get_tool_registry,
)
# Re-export from providers for convenience
from ..providers.base import ToolDefinition
from .http_tool import HttpApiTool
from .shell_tool import SystemShellTool
from .browser_tool import WebBrowserTool
from .filesystem_tool import FilesystemTool
from .scheduler_tool import SchedulerTool

__all__ = [
    # Base classes
    "BaseTool",
    "ToolResult",
    "ToolParameter",
    "ToolCategory",
    "ToolRiskLevel",
    "ToolRegistry",
    "get_tool_registry",
    # Tool implementations
    "HttpApiTool",
    "SystemShellTool",
    "WebBrowserTool",
    "FilesystemTool",
    "SchedulerTool",
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
    
    return registry
