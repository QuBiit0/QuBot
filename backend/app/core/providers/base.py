"""
Base LLM Provider - Abstract interface for all LLM backends
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class FinishReason(Enum):
    """Reason why the LLM stopped generating"""

    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"


@dataclass
class ToolDefinition:
    """Definition of a tool that can be called by the LLM"""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema


@dataclass
class ToolCall:
    """A tool call requested by the LLM"""

    id: str
    name: str
    arguments: dict[str, Any]

    @classmethod
    def from_openai(cls, tool_call: dict[str, Any]) -> "ToolCall":
        """Parse OpenAI-style tool call"""
        import json

        return cls(
            id=tool_call["id"],
            name=tool_call["function"]["name"],
            arguments=json.loads(tool_call["function"]["arguments"]),
        )

    @classmethod
    def from_anthropic(cls, tool_use: dict[str, Any]) -> "ToolCall":
        """Parse Anthropic-style tool call"""
        return cls(
            id=tool_use["id"],
            name=tool_use["name"],
            arguments=tool_use["input"],
        )

    @classmethod
    def from_google(cls, function_call: dict[str, Any]) -> "ToolCall":
        """Parse Google/Gemini-style tool call"""
        return cls(
            id=function_call.get("id", "") or f"call_{datetime.utcnow().timestamp()}",
            name=function_call["name"],
            arguments=function_call["args"],
        )


@dataclass
class LlmResponse:
    """Standardized LLM response across all providers"""

    content: str | None  # Text content (None if tool calls)
    tool_calls: list[ToolCall]  # Tool calls requested
    finish_reason: FinishReason
    input_tokens: int
    output_tokens: int
    model: str
    provider: str
    latency_ms: int
    raw_response: dict[str, Any] | None = None  # Provider-specific raw response

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class BaseLlmProvider(ABC):
    """
    Abstract base class for all LLM providers.

    All providers must implement:
    - complete(): Non-streaming completion
    - complete_stream(): Streaming completion
    - get_token_count(): Count tokens in text
    - test_connection(): Verify API connectivity

    Optional overrides:
    - prepare_tools(): Convert ToolDefinition to provider-specific format
    - format_messages(): Convert generic messages to provider format
    """

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 1.0,
        extra_config: dict[str, Any] | None = None,
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.extra_config = extra_config or {}

        # Initialize client (provider-specific)
        self._client = None

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'openai', 'anthropic')"""
        pass

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> LlmResponse:
        """
        Generate a completion.

        Args:
            messages: List of {"role": "user"|"assistant", "content": str}
            tools: Optional list of tools the LLM can call
            system_prompt: Optional system prompt

        Returns:
            LlmResponse with standardized format
        """
        pass

    @abstractmethod
    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming completion.

        Yields:
            Chunks of text as they're generated
        """
        pass

    @abstractmethod
    async def get_token_count(self, text: str) -> int:
        """Get token count for text (for cost estimation)"""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test API connectivity"""
        pass

    def prepare_tools(self, tools: list[ToolDefinition]) -> list[dict[str, Any]]:
        """
        Convert ToolDefinitions to provider-specific format.
        Override in subclass for custom formatting.
        """
        # Default OpenAI-compatible format
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in tools
        ]

    def format_messages(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> list[dict[str, str]]:
        """
        Format messages for provider. Override for custom formatting.
        """
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        formatted.extend(messages)
        return formatted

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost in USD. Override with provider-specific pricing.
        """
        # Default: $0 (unknown)
        return 0.0

    async def close(self):
        """Close any open connections"""
        if self._client:
            await self._client.close()


class ToolResult:
    """Result of executing a tool call"""

    def __init__(
        self,
        tool_call_id: str,
        name: str,
        result: Any,
        error: str | None = None,
    ):
        self.tool_call_id = tool_call_id
        self.name = name
        self.result = result
        self.error = error
        self.success = error is None

    def to_message(self) -> dict[str, Any]:
        """Convert to message format for LLM"""
        content = str(self.result) if self.success else f"Error: {self.error}"
        return {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "name": self.name,
            "content": content,
        }
