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
from .code_executor_tool import CodeExecutorTool
from .database_query_tool import DatabaseQueryTool
from .docs_search_tool import DocsSearchTool
from .document_reader_tool import DocumentReaderTool
from .email_tool import EmailTool
from .filesystem_tool import FilesystemTool
from .github_tool import GitHubTool
from .http_tool import HttpApiTool
from .mcp_installer_tool import MCPInstallerTool
from .memory_tool import AgentMemoryTool
from .notification_tool import NotificationTool
from .playwright_tool import PlaywrightBrowserTool
from .scheduler_tool import SchedulerTool
from .shell_tool import SystemShellTool
from .web_search_tool import WebSearchTool
from .delegate_tool import DelegateTool
from .agent_creator_tool import AgentCreatorTool
from .skill_creator_tool import SkillCreatorTool
from .channel_manager_tool import ChannelManagerTool
from .sessions_tool import SessionsTool, SubagentSpawnTool
from .gateway_tool import GatewayTool
from .nodes_tool import NodesTool
from .canvas_tool import CanvasTool
from .image_generation_tool import ImageGenerationTool
from .browser_profiles_tool import BrowserProfilesTool
from .apply_patch_tool import ApplyPatchTool
from .calendar_tool import CalendarTool
from .voice_tool import VoiceTool
from .secrets_tool import SecretsTool

__all__ = [
    "AgentCreatorTool",
    "SkillCreatorTool",
    "ChannelManagerTool",
    "SessionsTool",
    "SubagentSpawnTool",
    "GatewayTool",
    "NodesTool",
    "CanvasTool",
    "ImageGenerationTool",
    "BrowserProfilesTool",
    "ApplyPatchTool",
    "CalendarTool",
    "VoiceTool",
    "SecretsTool",
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

    # Original tools
    registry.register(HttpApiTool, config.get("http", {}))
    registry.register(SystemShellTool, config.get("shell", {}))
    registry.register(WebBrowserTool, config.get("browser", {}))
    registry.register(FilesystemTool, config.get("filesystem", {}))
    registry.register(SchedulerTool, config.get("scheduler", {}))
    registry.register(WebSearchTool, config.get("web_search", {}))
    registry.register(PlaywrightBrowserTool, config.get("playwright", {}))

    # New tools
    registry.register(CodeExecutorTool, config.get("code_executor", {}))
    registry.register(DocumentReaderTool, config.get("document_reader", {}))
    registry.register(DatabaseQueryTool, config.get("database_query", {}))
    registry.register(AgentMemoryTool, config.get("agent_memory", {}))
    registry.register(GitHubTool, config.get("github", {}))
    registry.register(EmailTool, config.get("email", {}))
    registry.register(NotificationTool, config.get("notification", {}))
    registry.register(DocsSearchTool, config.get("docs_search", {}))
    registry.register(MCPInstallerTool, config.get("mcp_installer", {}))
    registry.register(DelegateTool, config.get("delegate_tool", {}))
    registry.register(AgentCreatorTool, config.get("agent_creator", {}))
    registry.register(SkillCreatorTool, config.get("skill_creator", {}))
    registry.register(ChannelManagerTool, config.get("channel_manager", {}))
    registry.register(SessionsTool, config.get("sessions", {}))
    registry.register(SubagentSpawnTool, config.get("subagent_spawn", {}))
    registry.register(GatewayTool, config.get("gateway", {}))
    registry.register(NodesTool, config.get("nodes", {}))
    registry.register(CanvasTool, config.get("canvas", {}))
    registry.register(ImageGenerationTool, config.get("image_generation", {}))
    registry.register(BrowserProfilesTool, config.get("browser_profiles", {}))
    registry.register(ApplyPatchTool, config.get("apply_patch", {}))
    registry.register(CalendarTool, config.get("calendar", {}))
    registry.register(VoiceTool, config.get("voice", {}))
    registry.register(SecretsTool, config.get("secrets", {}))

    return registry
