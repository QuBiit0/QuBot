"""
OpenRouter Provider — Gateway to 100+ LLM models via a single API key.

OpenRouter is fully OpenAI-compatible so we inherit from OpenAiProvider and
override only what differs (base_url, headers, pricing, provider_name).

Usage:
    Set OPENROUTER_API_KEY in your environment (or pass api_key to the constructor).
    Models are referenced as "provider/model", e.g. "anthropic/claude-opus-4-5".

Docs: https://openrouter.ai/docs
"""

import os
import time
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from .base import BaseLlmProvider, FinishReason, LlmResponse, ToolCall, ToolDefinition
from .registry import register_provider


@register_provider("openrouter")
class OpenRouterProvider(BaseLlmProvider):
    """
    OpenRouter — access 100+ models from OpenAI, Anthropic, Google, Meta,
    Mistral, DeepSeek and more through a single OpenAI-compatible API.
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, **kwargs):
        # Allow callers to skip api_key; we fall back to env var
        if not kwargs.get("api_key"):
            kwargs["api_key"] = os.getenv("OPENROUTER_API_KEY", "")

        # Force base_url to OpenRouter
        kwargs["base_url"] = self.OPENROUTER_BASE_URL
        super().__init__(**kwargs)

        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": os.getenv("PUBLIC_DOMAIN", "https://qubot.local"),
                "X-Title": "Qubot AI",
            },
        )

    @property
    def provider_name(self) -> str:
        return "openrouter"

    # ── complete ──────────────────────────────────────────────────────────────

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

    # ── streaming ─────────────────────────────────────────────────────────────

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
                "OpenRouter does not reliably support streaming with tool calls. "
                "Use complete() instead."
            )

        stream = await self._client.chat.completions.create(**params)

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    # ── utility ───────────────────────────────────────────────────────────────

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
                model=self.model or "openai/gpt-4o-mini",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False
