"""
Anthropic Provider - Implementation for Claude API
"""

import os
import time
from collections.abc import AsyncGenerator
from typing import Any

from anthropic import AsyncAnthropic

from .base import BaseLlmProvider, FinishReason, LlmResponse, ToolCall, ToolDefinition
from .registry import register_provider


@register_provider("anthropic")
class AnthropicProvider(BaseLlmProvider):
    """Anthropic Claude API provider with tool-calling support"""

    # Pricing per 1K tokens (as of 2024)
    PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = AsyncAnthropic(
            api_key=self.api_key or os.getenv("ANTHROPIC_API_KEY"),
            base_url=self.base_url,
        )

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def prepare_tools(self, tools: list[ToolDefinition]) -> list[dict[str, Any]]:
        """Convert to Anthropic tool format"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in tools
        ]

    def format_messages(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> tuple:
        """
        Format messages for Anthropic API.
        Returns (system, messages) as Anthropic separates them.
        """
        formatted = []
        for msg in messages:
            role = msg["role"]
            # Anthropic uses 'assistant' not 'model'
            if role == "model":
                role = "assistant"
            formatted.append(
                {
                    "role": role,
                    "content": msg["content"],
                }
            )

        return system_prompt, formatted

    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> LlmResponse:
        """Generate completion using Anthropic API"""
        start_time = time.time()

        # Format messages
        system, formatted_messages = self.format_messages(messages, system_prompt)

        # Prepare request params
        params = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }

        if system:
            params["system"] = system

        # Add tools if provided
        if tools:
            params["tools"] = self.prepare_tools(tools)

        # Make request
        response = await self._client.messages.create(**params)

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Parse response
        content_text = None
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content_text = block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall.from_anthropic(
                        {
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        }
                    )
                )

        # Map stop reason
        finish_reason_map = {
            "end_turn": FinishReason.STOP,
            "max_tokens": FinishReason.LENGTH,
            "stop_sequence": FinishReason.STOP,
            "tool_use": FinishReason.TOOL_CALLS,
        }

        return LlmResponse(
            content=content_text if not tool_calls else None,
            tool_calls=tool_calls,
            finish_reason=finish_reason_map.get(
                response.stop_reason, FinishReason.ERROR
            ),
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=response.model,
            provider=self.provider_name,
            latency_ms=latency_ms,
            raw_response={
                "id": response.id,
                "type": response.type,
                "role": response.role,
                "content": [c.model_dump() for c in response.content],
                "stop_reason": response.stop_reason,
                "usage": response.usage.model_dump(),
            },
        )

    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion"""
        system, formatted_messages = self.format_messages(messages, system_prompt)

        params = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stream": True,
        }

        if system:
            params["system"] = system

        # Note: Streaming with tools has limitations
        if tools:
            params["tools"] = self.prepare_tools(tools)

        async with self._client.messages.stream(**params) as stream:
            async for text in stream.text_stream:
                yield text

    async def get_token_count(self, text: str) -> int:
        """Estimate token count for Claude"""
        try:
            # Use Anthropic's tokenizer if available
            response = await self._client.messages.count_tokens(
                model=self.model,
                messages=[{"role": "user", "content": text}],
            )
            return response.input_tokens
        except Exception:
            # Fallback: Claude uses ~4 chars per token
            return len(text) // 4

    async def test_connection(self) -> bool:
        """Test API connectivity"""
        try:
            await self._client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on model pricing"""
        pricing = self.PRICING.get(self.model, {"input": 0, "output": 0})

        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]

        return round(input_cost + output_cost, 6)
