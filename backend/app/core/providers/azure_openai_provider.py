"""
Azure OpenAI Provider — Microsoft Azure-hosted OpenAI models.

Requires three pieces of configuration:
  1. AZURE_OPENAI_API_KEY   — Azure API key
  2. AZURE_OPENAI_ENDPOINT  — e.g. https://my-resource.openai.azure.com
  3. AZURE_OPENAI_API_VERSION — e.g. 2024-10-21

The `model` parameter should match your Azure *deployment name*.

Docs: https://learn.microsoft.com/en-us/azure/ai-services/openai/
"""

import os
import time
from collections.abc import AsyncGenerator

from openai import AsyncAzureOpenAI

from .base import BaseLlmProvider, FinishReason, LlmResponse, ToolCall, ToolDefinition
from .registry import register_provider


@register_provider("azure_openai")
class AzureOpenAiProvider(BaseLlmProvider):
    """Azure-hosted OpenAI models with full tool-calling support."""

    def __init__(self, **kwargs):
        if not kwargs.get("api_key"):
            kwargs["api_key"] = os.getenv("AZURE_OPENAI_API_KEY", "")

        super().__init__(**kwargs)

        self._azure_endpoint = self.extra_config.get(
            "azure_endpoint", os.getenv("AZURE_OPENAI_ENDPOINT", "")
        )
        self._api_version = self.extra_config.get(
            "api_version", os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
        )

        self._client = AsyncAzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self._azure_endpoint,
            api_version=self._api_version,
        )

    @property
    def provider_name(self) -> str:
        return "azure_openai"

    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> LlmResponse:
        start_time = time.time()
        formatted_messages = self.format_messages(messages, system_prompt)

        params: dict = {
            "model": self.model,  # This is the deployment name in Azure
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
            model=response.model or self.model,
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
                "Azure OpenAI does not support streaming with tool calls. "
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
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False
