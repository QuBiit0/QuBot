"""
OpenAI Provider - Implementation for OpenAI API
"""

import os
import time
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from .base import BaseLlmProvider, FinishReason, LlmResponse, ToolCall, ToolDefinition
from .registry import register_provider


@register_provider("openai")
class OpenAiProvider(BaseLlmProvider):
    """OpenAI API provider with tool-calling support"""

    # Pricing per 1K tokens (as of 2024) - update as needed
    PRICING = {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = AsyncOpenAI(
            api_key=self.api_key or os.getenv("OPENAI_API_KEY"),
            base_url=self.base_url,
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> LlmResponse:
        """Generate completion using OpenAI API"""
        start_time = time.time()

        # Format messages
        formatted_messages = self.format_messages(messages, system_prompt)

        # Prepare request params
        params = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

        # Add tools if provided
        if tools:
            params["tools"] = self.prepare_tools(tools)
            params["tool_choice"] = "auto"

        # Make request
        response = await self._client.chat.completions.create(**params)

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Parse response
        choice = response.choices[0]
        message = choice.message

        # Extract tool calls
        tool_calls = []
        if message.tool_calls:
            tool_calls = [
                ToolCall.from_openai(tc.model_dump()) for tc in message.tool_calls
            ]

        # Map finish reason
        finish_reason_map = {
            "stop": FinishReason.STOP,
            "length": FinishReason.LENGTH,
            "tool_calls": FinishReason.TOOL_CALLS,
            "content_filter": FinishReason.CONTENT_FILTER,
        }

        return LlmResponse(
            content=message.content if not tool_calls else None,
            tool_calls=tool_calls,
            finish_reason=finish_reason_map.get(
                choice.finish_reason, FinishReason.ERROR
            ),
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            model=response.model,
            provider=self.provider_name,
            latency_ms=latency_ms,
            raw_response=response.model_dump(),
        )

    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion"""
        formatted_messages = self.format_messages(messages, system_prompt)

        params = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stream": True,
        }

        # Note: OpenAI doesn't support streaming with tools
        if tools:
            raise ValueError(
                "OpenAI does not support streaming with tool calls. "
                "Use complete() instead."
            )

        stream = await self._client.chat.completions.create(**params)

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def get_token_count(self, text: str) -> int:
        """Estimate token count using tiktoken"""
        try:
            import tiktoken

            # Use cl100k_base for GPT-4/GPT-3.5
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except ImportError:
            # Fallback: rough estimate (4 chars per token)
            return len(text) // 4

    async def test_connection(self) -> bool:
        """Test API connectivity"""
        try:
            # Make a simple request
            await self._client.chat.completions.create(
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
