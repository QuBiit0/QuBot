"""
Custom OpenAI-Compatible Provider — connects to ANY OpenAI-compatible endpoint.

Covers: LM Studio, Together AI, Fireworks, vLLM, llama.cpp, text-generation-webui,
        Azure OpenAI, and any other server that speaks the OpenAI chat completions API.

Required config:
    api_key:  Any non-empty string (use "no-key" for local servers)
    base_url: Full API base URL, e.g. "http://localhost:1234/v1"
    model:    Model name as the server expects it

Env vars:
    CUSTOM_OPENAI_API_KEY
    CUSTOM_OPENAI_BASE_URL
"""

import os
import time
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from .base import BaseLlmProvider, FinishReason, LlmResponse, ToolCall, ToolDefinition
from .registry import register_provider


@register_provider("custom")
class CustomOpenAiProvider(BaseLlmProvider):
    """
    Generic OpenAI-compatible provider.

    Works with any server that implements the /v1/chat/completions endpoint
    following the OpenAI specification.
    """

    def __init__(self, **kwargs):
        if not kwargs.get("api_key"):
            kwargs["api_key"] = os.getenv("CUSTOM_OPENAI_API_KEY", "no-key")

        if not kwargs.get("base_url"):
            kwargs["base_url"] = os.getenv(
                "CUSTOM_OPENAI_BASE_URL", "http://localhost:1234/v1"
            )

        super().__init__(**kwargs)

        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    @property
    def provider_name(self) -> str:
        return "custom"

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
        if "reasoning_effort" in self.extra_config:
            params["reasoning_effort"] = self.extra_config["reasoning_effort"]

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

        usage = response.usage
        return LlmResponse(
            content=message.content if not tool_calls else None,
            tool_calls=tool_calls,
            finish_reason=finish_reason_map.get(
                choice.finish_reason, FinishReason.ERROR
            ),
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0 if usage else 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0 if usage else 0,
            model=getattr(response, "model", self.model) or self.model,
            provider=self.provider_name,
            latency_ms=latency_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else None,
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
                "Streaming with tool calls is not supported on custom endpoints. "
                "Use complete() instead."
            )

        stream = await self._client.chat.completions.create(**params)

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    async def get_token_count(self, text: str) -> int:
        # Generic fallback — custom servers rarely expose tokenization
        return len(text) // 4

    async def test_connection(self) -> bool:
        try:
            await self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False
