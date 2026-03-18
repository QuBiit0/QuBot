"""
DeepSeek Provider — OpenAI-compatible API for DeepSeek V3 and R1 (reasoning).

DeepSeek's API is fully OpenAI-compatible with a different base URL.

Env var: DEEPSEEK_API_KEY
Docs:    https://platform.deepseek.com/docs
"""

import os
import time
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from .base import BaseLlmProvider, FinishReason, LlmResponse, ToolCall, ToolDefinition
from .registry import register_provider


@register_provider("deepseek")
class DeepSeekProvider(BaseLlmProvider):
    """DeepSeek LLM provider (DeepSeek-V3, DeepSeek-R1, etc.)"""

    DEEPSEEK_BASE_URL = "https://api.deepseek.com"

    # Pricing per 1M tokens (USD) — DeepSeek is extremely cheap
    PRICING = {
        "deepseek-chat": {"input": 0.14, "output": 0.28},
        "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    }

    def __init__(self, **kwargs):
        if not kwargs.get("api_key"):
            kwargs["api_key"] = os.getenv("DEEPSEEK_API_KEY", "")

        kwargs.setdefault("base_url", self.DEEPSEEK_BASE_URL)
        super().__init__(**kwargs)

        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    @property
    def provider_name(self) -> str:
        return "deepseek"

    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> LlmResponse:
        start_time = time.time()
        formatted_messages = self.format_messages(messages, system_prompt)

        params: dict = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

        if tools:
            params["tools"] = self.prepare_tools(tools)
            params["tool_choice"] = "auto"

        response = await self._client.chat.completions.create(**params)
        latency_ms = int((time.time() - start_time) * 1000)

        choice = response.choices[0]
        message = choice.message

        tool_calls = []
        if message.tool_calls:
            tool_calls = [
                ToolCall.from_openai(tc.model_dump()) for tc in message.tool_calls
            ]

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
            input_tokens=getattr(response.usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(response.usage, "completion_tokens", 0) or 0,
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
        formatted_messages = self.format_messages(messages, system_prompt)

        params: dict = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stream": True,
        }

        if tools:
            raise ValueError(
                "DeepSeek does not reliably support streaming with tool calls. "
                "Use complete() instead."
            )

        stream = await self._client.chat.completions.create(**params)

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    async def get_token_count(self, text: str) -> int:
        try:
            import tiktoken

            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except ImportError:
            return len(text) // 4

    async def test_connection(self) -> bool:
        try:
            await self._client.chat.completions.create(
                model=self.model or "deepseek-chat",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self.PRICING.get(self.model, {"input": 0.14, "output": 0.28})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)
