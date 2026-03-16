"""
Ollama Provider - Implementation for local Ollama API
"""

import json
import os
import time
from collections.abc import AsyncGenerator
from typing import Any

import aiohttp

from .base import BaseLlmProvider, FinishReason, LlmResponse, ToolCall, ToolDefinition
from .registry import register_provider


@register_provider("ollama")
class OllamaProvider(BaseLlmProvider):
    """
    Ollama provider for local LLM inference.
    Supports tool calling via Ollama's tool support (if model supports it).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Default to localhost
        self.base_url = self.base_url or os.getenv(
            "OLLAMA_HOST", "http://localhost:11434"
        )
        self._session: aiohttp.ClientSession | None = None

    @property
    def provider_name(self) -> str:
        return "ollama"

    def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def prepare_tools(self, tools: list[ToolDefinition]) -> list[dict[str, Any]]:
        """Convert to Ollama tool format (OpenAI-compatible)"""
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

    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> LlmResponse:
        """Generate completion using Ollama API"""
        start_time = time.time()

        # Format messages
        formatted_messages = self.format_messages(messages, system_prompt)

        # Prepare request body
        body = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "top_p": self.top_p,
            },
        }

        # Add tools if provided (Ollama supports tools in newer versions)
        if tools:
            body["tools"] = self.prepare_tools(tools)

        session = self._get_session()

        try:
            async with session.post(
                f"{self.base_url}/api/chat",
                json=body,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama error: {error_text}")

                data = await response.json()
        except aiohttp.ClientError as e:
            raise Exception(f"Failed to connect to Ollama: {e}")

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Parse response
        message = data.get("message", {})
        content = message.get("content", "")

        # Check for tool calls in response
        tool_calls = []
        if "tool_calls" in message:
            for tc in message["tool_calls"]:
                tool_calls.append(
                    ToolCall(
                        id=tc.get("id", f"call_{time.time()}"),
                        name=tc["function"]["name"],
                        arguments=json.loads(tc["function"]["arguments"]),
                    )
                )

        # Ollama doesn't always provide token counts
        # Try to get from response or estimate
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)

        # If not provided, estimate
        if prompt_tokens == 0:
            prompt_tokens = len(json.dumps(formatted_messages)) // 4
        if completion_tokens == 0:
            completion_tokens = len(content) // 4

        # Determine finish reason
        done_reason = data.get("done_reason", "")
        if done_reason == "stop":
            finish_reason = FinishReason.STOP
        elif done_reason == "length":
            finish_reason = FinishReason.LENGTH
        elif tool_calls:
            finish_reason = FinishReason.TOOL_CALLS
        else:
            finish_reason = FinishReason.STOP

        return LlmResponse(
            content=content if not tool_calls else None,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            model=self.model,
            provider=self.provider_name,
            latency_ms=latency_ms,
            raw_response=data,
        )

    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion"""
        formatted_messages = self.format_messages(messages, system_prompt)

        body = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "top_p": self.top_p,
            },
        }

        # Note: Ollama streaming with tools is complex
        if tools:
            raise ValueError(
                "Ollama streaming with tool calls not supported. "
                "Use complete() instead."
            )

        session = self._get_session()

        async with session.post(
            f"{self.base_url}/api/chat",
            json=body,
        ) as response:
            async for line in response.content:
                line = line.decode("utf-8").strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    message = data.get("message", {})
                    content = message.get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue

    async def get_token_count(self, text: str) -> int:
        """Estimate token count for local models"""
        # Rough estimate for Llama-type models
        return len(text) // 4

    async def test_connection(self) -> bool:
        """Test API connectivity"""
        try:
            session = self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    # Check if our model is available
                    models = [m["name"] for m in data.get("models", [])]
                    return any(self.model in m for m in models)
                return False
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """List available local models"""
        try:
            session = self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return [m["name"] for m in data.get("models", [])]
                return []
        except Exception:
            return []

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Local models are free to use (just compute cost)"""
        return 0.0

    async def close(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
