"""
Base Tool - Abstract base class for all Qubot tools
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToolCategory(Enum):
    """Categories of tools"""

    COMMUNICATION = "communication"
    DATA = "data"
    SYSTEM = "system"
    WEB = "web"
    FILE = "file"
    CODE = "code"
    MISC = "misc"


class ToolRiskLevel(Enum):
    """Risk levels for tools"""

    SAFE = "safe"  # Read-only, no side effects
    NORMAL = "normal"  # Standard operations
    DANGEROUS = "dangerous"  # Can modify/delete data or execute code


@dataclass
class ToolParameter:
    """Definition of a tool parameter"""

    name: str
    type: str  # string, integer, number, boolean, array, object
    description: str
    required: bool = True
    default: Any = None
    enum: list[Any] | None = None


@dataclass
class ToolResult:
    """Result of executing a tool"""

    success: bool
    data: Any = None
    error: str | None = None
    stdout: str | None = None
    stderr: str | None = None
    execution_time_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert result to JSON string"""
        return json.dumps(self.to_dict(), default=str)


class BaseTool(ABC):
    """
    Abstract base class for all Qubot tools.

    All tools must implement:
    - execute(): Execute the tool with given parameters
    - get_schema(): Return JSON Schema for the tool

    Tools can optionally override:
    - validate_params(): Custom parameter validation
    - format_result(): Custom result formatting
    """

    # Tool metadata - override in subclasses
    name: str = "base_tool"
    description: str = "Base tool description"
    category: ToolCategory = ToolCategory.MISC
    risk_level: ToolRiskLevel = ToolRiskLevel.SAFE

    # Tool configuration
    timeout_seconds: int = 30
    max_retries: int = 0

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize tool with configuration.

        Args:
            config: Tool-specific configuration (e.g., API keys, paths)
        """
        self.config = config or {}
        self._validate_config()

    @abstractmethod
    async def execute(self, **params) -> ToolResult:
        """
        Execute the tool with given parameters.

        Args:
            **params: Tool-specific parameters

        Returns:
            ToolResult with execution outcome
        """
        pass

    def get_schema(self) -> dict[str, Any]:
        """
        Get JSON Schema for tool parameters (OpenAI function format).

        Returns:
            Dict with name, description, and parameters schema
        """
        parameters = self._get_parameters_schema()

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        name: self._param_to_schema(param)
                        for name, param in parameters.items()
                    },
                    "required": [
                        name for name, param in parameters.items() if param.required
                    ],
                },
            },
        }

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        """
        Define tool parameters. Override in subclasses.

        Returns:
            Dict mapping parameter names to ToolParameter definitions
        """
        return {}

    def _param_to_schema(self, param: ToolParameter) -> dict[str, Any]:
        """Convert ToolParameter to JSON Schema property"""
        schema = {
            "type": param.type,
            "description": param.description,
        }
        if param.enum:
            schema["enum"] = param.enum
        if param.default is not None:
            schema["default"] = param.default
        return schema

    def validate_params(self, params: dict[str, Any]) -> tuple[bool, str | None]:
        """
        Validate parameters before execution.

        Args:
            params: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        schema = self._get_parameters_schema()

        # Check required parameters
        for name, param in schema.items():
            if param.required and name not in params:
                return False, f"Missing required parameter: {name}"

        # Check for unknown parameters
        for name in params:
            if name not in schema:
                return False, f"Unknown parameter: {name}"

        return True, None

    def _validate_config(self) -> None:  # noqa: B027
        """Validate tool configuration. Override in subclasses if needed."""
        pass

    def format_result(self, result: ToolResult) -> str:
        """
        Format result for LLM consumption.
        Override for custom formatting.
        """
        if not result.success:
            return f"Tool execution failed: {result.error}"

        if result.data is not None:
            if isinstance(result.data, (dict, list)):
                return json.dumps(result.data, indent=2, default=str)
            return str(result.data)

        if result.stdout:
            return result.stdout

        return "Tool executed successfully (no output)"


class ToolRegistry:
    """Registry for tools"""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._tool_classes: dict[str, type] = {}

    def register(self, tool_class: type, config: dict | None = None) -> None:
        """Register a tool class"""
        # Create instance to get name
        instance = tool_class(config)
        self._tools[instance.name] = instance
        self._tool_classes[instance.name] = tool_class

    def get(self, name: str) -> BaseTool | None:
        """Get tool by name"""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """List all registered tool names"""
        return list(self._tools.keys())

    def get_tools_by_category(self, category: ToolCategory) -> list[BaseTool]:
        """Get tools by category"""
        return [tool for tool in self._tools.values() if tool.category == category]

    def get_tools_for_llm(self) -> list[dict[str, Any]]:
        """Get all tools formatted for LLM function calling"""
        return [tool.get_schema() for tool in self._tools.values()]

    def unregister(self, name: str) -> None:
        """Unregister a tool"""
        self._tools.pop(name, None)
        self._tool_classes.pop(name, None)


# Global registry instance
_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get or create global tool registry"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
