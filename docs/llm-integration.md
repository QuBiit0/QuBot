# Qubot — LLM Integration

> **Module**: `backend/app/llm/`
> **Service**: `backend/app/services/llm_service.py`

---

## 1. Overview

All LLM interactions go through a provider abstraction layer. No module outside `llm/` ever imports an LLM SDK directly. This enables:
- Per-agent provider and model configuration
- Unified cost tracking across all providers
- Easy testing (mock the provider interface)
- Runtime switching between providers without code changes
- **Universal compatibility**: any OpenAI-compatible endpoint works with `CustomLlmProvider`

**Qubot is LLM-agnostic** — it works with cloud providers, local models, regional APIs, and anything with an HTTP interface.

```
AgentExecutionService / OrchestratorService
         │
         │ provider = get_provider(agent.llm_config)
         │ response = await provider.complete(config, messages, tools)
         ▼
    BaseLlmProvider (abstract)
    │
    ├── OpenAiProvider         → openai SDK          (GPT-4o, GPT-4o-mini, o1, o3...)
    ├── AnthropicProvider      → anthropic SDK        (Claude 3.5/4.x Sonnet/Opus/Haiku)
    ├── GoogleProvider         → google-generativeai  (Gemini 2.0 Flash, 1.5 Pro...)
    ├── GroqProvider           → OpenAI-compat        (Llama 3.3, Mixtral, DeepSeek-R1...)
    ├── OpenRouterProvider     → OpenAI-compat        (400+ models via single endpoint)
    ├── DeepSeekProvider       → OpenAI-compat        (DeepSeek-V3, DeepSeek-R1)
    ├── KimiProvider           → OpenAI-compat        (Moonshot: kimi-k1.5, moonshot-v1-*)
    ├── MiniMaxProvider        → MiniMax REST API     (abab6.5s, MiniMax-Text-01)
    ├── ZhipuProvider          → Zhipu SDK/REST       (GLM-4-Plus, GLM-4-Air, GLM-Z1)
    ├── OllamaProvider         → OpenAI-compat        (any local model via Ollama)
    └── CustomLlmProvider      → configurable         (ANY OpenAI-compat or raw HTTP endpoint)
```

### Provider Compatibility Matrix

| Provider | API Style | Tool Calling | Streaming | Notes |
|----------|-----------|-------------|-----------|-------|
| OpenAI | Native | ✅ | ✅ | Reference implementation |
| Anthropic | Native | ✅ | ✅ | tool_use format |
| Google | Native SDK | ✅ | ✅ | function_declarations format |
| Groq | OpenAI-compat | ✅ | ✅ | Ultra-fast inference |
| OpenRouter | OpenAI-compat | ✅ (model-dependent) | ✅ | Routes to 400+ models |
| DeepSeek | OpenAI-compat | ✅ | ✅ | Excellent cost/performance |
| Kimi | OpenAI-compat | ✅ | ✅ | Long context (128K+) |
| MiniMax | REST | ✅ | ✅ | Chinese/multilingual |
| Zhipu (GLM) | SDK/REST | ✅ | ✅ | GLM-4 series |
| Ollama | OpenAI-compat | ✅ (model-dependent) | ✅ | Local inference |
| **Custom** | **Configurable** | **Configurable** | **Configurable** | **Any provider** |

---

## 2. Core Data Types

```python
# backend/app/llm/base.py
from abc import ABC, abstractmethod
from typing import Literal, Optional, Union
from pydantic import BaseModel


class LlmMessage(BaseModel):
    """A single message in the conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[Union[str, list]] = None  # list for multimodal (future)
    name: Optional[str] = None
    tool_call_id: Optional[str] = None  # for role=tool responses
    tool_calls: Optional[list] = None   # for role=assistant with tool calls


class LlmToolCall(BaseModel):
    """A tool call requested by the LLM."""
    id: str
    name: str
    arguments: dict  # Already parsed from JSON


class LlmUsage(BaseModel):
    """Token usage and cost for a single completion."""
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int


class LlmResponse(BaseModel):
    """Unified response from any LLM provider."""
    content: Optional[str] = None
    tool_calls: list[LlmToolCall] = []
    finish_reason: Literal["stop", "tool_calls", "length", "error"]
    usage: LlmUsage


class BaseLlmProvider(ABC):
    """Abstract interface all providers must implement."""

    @abstractmethod
    async def complete(
        self,
        config: "LlmConfig",
        messages: list[LlmMessage],
        tools: Optional[list[dict]] = None,
    ) -> LlmResponse:
        """
        Send messages to the LLM and return unified response.

        Args:
            config: LlmConfig with provider-specific settings
            messages: Conversation history
            tools: Optional list of OpenAI-format function schemas

        Returns:
            LlmResponse with content, tool_calls, finish_reason, usage
        """
        ...

    @abstractmethod
    async def test_connectivity(self, config: "LlmConfig") -> bool:
        """
        Verify provider is reachable and API key is valid.
        Uses a minimal request (no input tokens if possible).
        """
        ...
```

---

## 3. Provider Registry

```python
# backend/app/llm/registry.py
from ..models.enums import LlmProviderEnum
from .base import BaseLlmProvider
from .openai import OpenAiProvider
from .anthropic import AnthropicProvider
from .google import GoogleProvider
from .groq import GroqProvider
from .ollama import OllamaProvider
from .openrouter import OpenRouterProvider
from .deepseek import DeepSeekProvider
from .kimi import KimiProvider
from .minimax import MiniMaxProvider
from .zhipu import ZhipuProvider
from .custom import CustomLlmProvider

PROVIDERS: dict[LlmProviderEnum, type[BaseLlmProvider]] = {
    LlmProviderEnum.OPENAI: OpenAiProvider,
    LlmProviderEnum.ANTHROPIC: AnthropicProvider,
    LlmProviderEnum.GOOGLE: GoogleProvider,
    LlmProviderEnum.GROQ: GroqProvider,
    LlmProviderEnum.OPENROUTER: OpenRouterProvider,
    LlmProviderEnum.DEEPSEEK: DeepSeekProvider,
    LlmProviderEnum.KIMI: KimiProvider,
    LlmProviderEnum.MINIMAX: MiniMaxProvider,
    LlmProviderEnum.ZHIPU: ZhipuProvider,
    LlmProviderEnum.LOCAL: OllamaProvider,
    LlmProviderEnum.CUSTOM: CustomLlmProvider,   # Fully configurable via extra_config
}

def get_provider(config: "LlmConfig") -> BaseLlmProvider:
    """
    Factory function — returns instantiated provider for given config.
    Falls back to CustomLlmProvider for unknown providers
    (handles future additions without code change).
    """
    provider_class = PROVIDERS.get(config.provider, CustomLlmProvider)
    return provider_class()
```

---

## 4. OpenAI Provider

```python
# backend/app/llm/openai.py
import json
import time
import os
from openai import AsyncOpenAI
from .base import BaseLlmProvider, LlmMessage, LlmResponse, LlmToolCall, LlmUsage
from ..core.logging import get_logger

logger = get_logger()

OPENAI_PRICING = {
    "gpt-4o": {"input": 0.0025, "output": 0.010},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.000600},
    "gpt-4-turbo": {"input": 0.010, "output": 0.030},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    # Default for unknown models
    "_default": {"input": 0.005, "output": 0.015},
}

class OpenAiProvider(BaseLlmProvider):

    async def complete(self, config, messages, tools=None) -> LlmResponse:
        api_key = os.getenv(config.api_key_ref)
        if not api_key:
            raise ValueError(f"API key env var '{config.api_key_ref}' not set")

        client = AsyncOpenAI(api_key=api_key)
        start_time = time.monotonic()

        # Convert LlmMessage list to OpenAI format
        oai_messages = [self._to_oai_message(m) for m in messages]

        kwargs = {
            "model": config.model_name,
            "messages": oai_messages,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "max_tokens": config.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await client.chat.completions.create(**kwargs)
        latency_ms = int((time.monotonic() - start_time) * 1000)

        choice = response.choices[0]
        finish_reason = choice.finish_reason

        # Parse tool calls if present
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(LlmToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=args
                ))

        # Calculate cost
        pricing = OPENAI_PRICING.get(config.model_name, OPENAI_PRICING["_default"])
        cost = (
            (response.usage.prompt_tokens / 1000) * pricing["input"] +
            (response.usage.completion_tokens / 1000) * pricing["output"]
        )

        logger.info(
            "llm_call_complete",
            provider="openai",
            model=config.model_name,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            cost_usd=round(cost, 6),
            latency_ms=latency_ms
        )

        return LlmResponse(
            content=choice.message.content,
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else finish_reason,
            usage=LlmUsage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                cost_usd=round(cost, 6),
                latency_ms=latency_ms
            )
        )

    async def test_connectivity(self, config) -> bool:
        try:
            api_key = os.getenv(config.api_key_ref)
            client = AsyncOpenAI(api_key=api_key)
            # Minimal call using models list (no token cost)
            await client.models.list()
            return True
        except Exception:
            return False

    def _to_oai_message(self, msg: LlmMessage) -> dict:
        d = {"role": msg.role}
        if msg.content:
            d["content"] = msg.content
        if msg.tool_call_id:
            d["tool_call_id"] = msg.tool_call_id
        if msg.tool_calls:
            d["tool_calls"] = msg.tool_calls
        if msg.name:
            d["name"] = msg.name
        return d
```

---

## 5. Anthropic Provider

```python
# backend/app/llm/anthropic.py
import json
import time
import os
import anthropic
from .base import BaseLlmProvider, LlmMessage, LlmResponse, LlmToolCall, LlmUsage

ANTHROPIC_PRICING = {
    "claude-opus-4-6": {"input": 0.015, "output": 0.075},
    "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
    "claude-haiku-4-5-20251001": {"input": 0.00025, "output": 0.00125},
    "_default": {"input": 0.003, "output": 0.015},
}

class AnthropicProvider(BaseLlmProvider):

    async def complete(self, config, messages, tools=None) -> LlmResponse:
        api_key = os.getenv(config.api_key_ref)
        client = anthropic.AsyncAnthropic(api_key=api_key)
        start_time = time.monotonic()

        # Separate system message from conversation
        system_msg = ""
        conv_messages = []
        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            elif msg.role == "tool":
                # Convert tool result to Anthropic format
                conv_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content
                    }]
                })
            elif msg.role == "assistant" and msg.tool_calls:
                # Convert assistant tool calls to Anthropic format
                content_blocks = []
                if msg.content:
                    content_blocks.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": json.loads(tc["function"]["arguments"])
                    })
                conv_messages.append({"role": "assistant", "content": content_blocks})
            else:
                conv_messages.append({"role": msg.role, "content": msg.content})

        # Convert OpenAI-format tools to Anthropic format
        anthropic_tools = []
        if tools:
            for t in tools:
                fn = t["function"]
                anthropic_tools.append({
                    "name": fn["name"],
                    "description": fn["description"],
                    "input_schema": fn.get("parameters", {"type": "object", "properties": {}})
                })

        kwargs = {
            "model": config.model_name,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "messages": conv_messages,
        }
        if system_msg:
            kwargs["system"] = system_msg
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        response = await client.messages.create(**kwargs)
        latency_ms = int((time.monotonic() - start_time) * 1000)

        # Parse response content
        text_content = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text_content += block.text
            elif block.type == "tool_use":
                tool_calls.append(LlmToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input
                ))

        pricing = ANTHROPIC_PRICING.get(config.model_name, ANTHROPIC_PRICING["_default"])
        cost = (
            (response.usage.input_tokens / 1000) * pricing["input"] +
            (response.usage.output_tokens / 1000) * pricing["output"]
        )

        finish_reason = "tool_calls" if tool_calls else (
            "stop" if response.stop_reason == "end_turn" else response.stop_reason
        )

        return LlmResponse(
            content=text_content or None,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=LlmUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                cost_usd=round(cost, 6),
                latency_ms=latency_ms
            )
        )

    async def test_connectivity(self, config) -> bool:
        try:
            api_key = os.getenv(config.api_key_ref)
            client = anthropic.AsyncAnthropic(api_key=api_key)
            await client.messages.create(
                model=config.model_name,
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}]
            )
            return True
        except Exception:
            return False
```

---

## 6. Groq Provider

```python
# backend/app/llm/groq.py
# Groq uses OpenAI-compatible API — inherit and override endpoint
import os
from openai import AsyncOpenAI
from .openai import OpenAiProvider

GROQ_PRICING = {
    "llama-3.3-70b-versatile": {"input": 0.00059, "output": 0.00079},
    "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00008},
    "mixtral-8x7b-32768": {"input": 0.00027, "output": 0.00027},
    "_default": {"input": 0.0006, "output": 0.0008},
}

class GroqProvider(OpenAiProvider):
    """Groq uses OpenAI-compatible API at a different base URL."""

    async def complete(self, config, messages, tools=None):
        api_key = os.getenv(config.api_key_ref)
        # Override client with Groq endpoint
        self._groq_key = api_key
        self._pricing = GROQ_PRICING
        # Temporarily monkey-patch — in production, pass client as dependency
        import openai
        old_base = openai.base_url if hasattr(openai, 'base_url') else None
        # Use Groq's OpenAI-compatible endpoint
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        # ... rest same as OpenAiProvider but with client above
        return await super().complete(config, messages, tools)

    async def test_connectivity(self, config) -> bool:
        try:
            api_key = os.getenv(config.api_key_ref)
            client = AsyncOpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            await client.models.list()
            return True
        except Exception:
            return False
```

---

## 7. Ollama Provider (Local)

```python
# backend/app/llm/ollama.py
import json
import time
import httpx
from .base import BaseLlmProvider, LlmMessage, LlmResponse, LlmToolCall, LlmUsage
from openai import AsyncOpenAI

class OllamaProvider(BaseLlmProvider):
    """
    Supports any OpenAI-compatible local endpoint.
    Default: Ollama at http://localhost:11434/v1
    Configure via extra_config: {"base_url": "http://your-host:port/v1"}
    """

    async def complete(self, config, messages, tools=None) -> LlmResponse:
        base_url = config.extra_config.get("base_url", "http://localhost:11434/v1")
        api_key = config.extra_config.get("api_key", "ollama")  # Ollama doesn't need a real key

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        start_time = time.monotonic()

        oai_messages = [self._to_oai_message(m) for m in messages]

        kwargs = {
            "model": config.model_name,
            "messages": oai_messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        response = await client.chat.completions.create(**kwargs)
        latency_ms = int((time.monotonic() - start_time) * 1000)

        choice = response.choices[0]
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(LlmToolCall(id=tc.id, name=tc.function.name, arguments=args))

        return LlmResponse(
            content=choice.message.content,
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else choice.finish_reason,
            usage=LlmUsage(
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
                cost_usd=0.0,  # Local model, no cost
                latency_ms=latency_ms
            )
        )

    async def test_connectivity(self, config) -> bool:
        base_url = config.extra_config.get("base_url", "http://localhost:11434")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/tags", timeout=5.0)
                return response.status_code == 200
        except Exception:
            return False

    def _to_oai_message(self, msg: LlmMessage) -> dict:
        d = {"role": msg.role}
        if msg.content:
            d["content"] = msg.content
        if msg.tool_call_id:
            d["tool_call_id"] = msg.tool_call_id
        return d
```

---

## 8. OpenRouter Provider

OpenRouter is a unified gateway that routes requests to 400+ models from any provider via a single OpenAI-compatible endpoint. Ideal for trying models without setting up individual API keys.

**Popular models via OpenRouter**: `anthropic/claude-opus-4`, `google/gemini-2.0-flash`, `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1`, `qwen/qwen-2.5-72b-instruct`, `mistralai/mistral-large`, and hundreds more.

```python
# backend/app/llm/openrouter.py
import os
from openai import AsyncOpenAI
from .openai import OpenAiProvider

OPENROUTER_PRICING = {
    # Prices vary by model — OpenRouter charges per model's actual cost
    # These are rough defaults; actual cost is in the response headers
    "_default": {"input": 0.003, "output": 0.015},
}

class OpenRouterProvider(OpenAiProvider):
    """
    OpenRouter: single endpoint for 400+ models.

    Config:
        api_key_ref: env var with OpenRouter API key (get at openrouter.ai)
        model_name: e.g. "anthropic/claude-opus-4", "google/gemini-2.0-flash"
        extra_config:
            site_url: your app URL (for OpenRouter rankings)
            app_name: your app name
    """
    BASE_URL = "https://openrouter.ai/api/v1"

    def _make_client(self, config) -> AsyncOpenAI:
        api_key = os.getenv(config.api_key_ref, "")
        extra_headers = {}
        if config.extra_config.get("site_url"):
            extra_headers["HTTP-Referer"] = config.extra_config["site_url"]
        if config.extra_config.get("app_name"):
            extra_headers["X-Title"] = config.extra_config["app_name"]
        return AsyncOpenAI(
            api_key=api_key,
            base_url=self.BASE_URL,
            default_headers=extra_headers,
        )

    async def complete(self, config, messages, tools=None):
        # OpenRouter returns actual cost in response metadata
        # We use the usage field if available, else estimate
        response = await super().complete(config, messages, tools)
        return response

    async def test_connectivity(self, config) -> bool:
        try:
            client = self._make_client(config)
            await client.models.list()
            return True
        except Exception:
            return False
```

**`LlmConfig` example for OpenRouter:**
```json
{
  "provider": "openrouter",
  "model_name": "anthropic/claude-opus-4",
  "api_key_ref": "OPENROUTER_API_KEY",
  "temperature": 0.7,
  "max_tokens": 4096,
  "extra_config": {
    "site_url": "https://yourdomain.com",
    "app_name": "Qubot"
  }
}
```

---

## 9. DeepSeek Provider

DeepSeek offers state-of-the-art models at very competitive pricing. Fully OpenAI-compatible.

**Models**: `deepseek-chat` (DeepSeek-V3), `deepseek-reasoner` (DeepSeek-R1 — chain-of-thought)

```python
# backend/app/llm/deepseek.py
import os
from openai import AsyncOpenAI
from .openai import OpenAiProvider

DEEPSEEK_PRICING = {
    "deepseek-chat": {"input": 0.00027, "output": 0.00110},        # DeepSeek-V3
    "deepseek-reasoner": {"input": 0.00055, "output": 0.00219},    # DeepSeek-R1
    "_default": {"input": 0.0003, "output": 0.0012},
}

class DeepSeekProvider(OpenAiProvider):
    """
    DeepSeek: OpenAI-compatible endpoint.
    Excellent cost/performance ratio. Supports tool calling.

    Config:
        api_key_ref: env var with DeepSeek API key (platform.deepseek.com)
        model_name: "deepseek-chat" | "deepseek-reasoner"
    """
    BASE_URL = "https://api.deepseek.com/v1"
    PRICING = DEEPSEEK_PRICING

    def _make_client(self, config) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=os.getenv(config.api_key_ref, ""),
            base_url=self.BASE_URL,
        )

    async def test_connectivity(self, config) -> bool:
        try:
            client = self._make_client(config)
            await client.models.list()
            return True
        except Exception:
            return False
```

---

## 10. Kimi Provider (Moonshot AI)

Kimi (by Moonshot AI) specializes in very long context windows (up to 128K tokens). Fully OpenAI-compatible.

**Models**: `moonshot-v1-8k`, `moonshot-v1-32k`, `moonshot-v1-128k`, `kimi-k1.5-32k`, `kimi-k1.5-128k`

```python
# backend/app/llm/kimi.py
import os
from openai import AsyncOpenAI
from .openai import OpenAiProvider

KIMI_PRICING = {
    "moonshot-v1-8k":    {"input": 0.0012,  "output": 0.0012},
    "moonshot-v1-32k":   {"input": 0.0024,  "output": 0.0024},
    "moonshot-v1-128k":  {"input": 0.0060,  "output": 0.0060},
    "kimi-k1.5-32k":     {"input": 0.0015,  "output": 0.0060},
    "kimi-k1.5-128k":    {"input": 0.0015,  "output": 0.0060},
    "_default":          {"input": 0.0024,  "output": 0.0024},
}

class KimiProvider(OpenAiProvider):
    """
    Kimi (Moonshot AI): long-context specialist.
    Excellent for tasks requiring processing large documents.

    Config:
        api_key_ref: env var with Moonshot API key (platform.moonshot.cn)
        model_name: "moonshot-v1-8k" | "moonshot-v1-128k" | "kimi-k1.5-128k"
    """
    BASE_URL = "https://api.moonshot.cn/v1"
    PRICING = KIMI_PRICING

    def _make_client(self, config) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=os.getenv(config.api_key_ref, ""),
            base_url=self.BASE_URL,
        )
```

---

## 11. MiniMax Provider

MiniMax is a Chinese AI company with strong multilingual capabilities. Uses its own REST API (not OpenAI-compatible).

**Models**: `MiniMax-Text-01`, `abab6.5s-chat`, `abab6.5g-chat`

```python
# backend/app/llm/minimax.py
import os, time, json
import httpx
from .base import BaseLlmProvider, LlmMessage, LlmResponse, LlmToolCall, LlmUsage

MINIMAX_PRICING = {
    "MiniMax-Text-01":   {"input": 0.00100, "output": 0.00100},
    "abab6.5s-chat":     {"input": 0.00010, "output": 0.00010},
    "abab6.5g-chat":     {"input": 0.00050, "output": 0.00050},
    "_default":          {"input": 0.00100, "output": 0.00100},
}

class MiniMaxProvider(BaseLlmProvider):
    """
    MiniMax: strong multilingual and long-context models.

    Config:
        api_key_ref: env var with MiniMax API key (api.minimax.chat)
        extra_config:
            group_id: your MiniMax Group ID (required)
    """
    BASE_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

    async def complete(self, config, messages, tools=None) -> LlmResponse:
        api_key = os.getenv(config.api_key_ref, "")
        group_id = config.extra_config.get("group_id", "")

        # MiniMax uses OpenAI-compatible chatcompletion_v2 endpoint
        # but requires group_id in headers
        start = time.monotonic()
        payload = {
            "model": config.model_name,
            "messages": [self._convert_message(m) for m in messages],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()

        latency_ms = int((time.monotonic() - start) * 1000)
        choice = data["choices"][0]
        msg = choice["message"]

        tool_calls = []
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                tool_calls.append(LlmToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=json.loads(tc["function"].get("arguments", "{}")),
                ))

        usage = data.get("usage", {})
        pricing = MINIMAX_PRICING.get(config.model_name, MINIMAX_PRICING["_default"])
        input_t = usage.get("prompt_tokens", 0)
        output_t = usage.get("completion_tokens", 0)
        cost = (input_t / 1000) * pricing["input"] + (output_t / 1000) * pricing["output"]

        return LlmResponse(
            content=msg.get("content"),
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else choice.get("finish_reason", "stop"),
            usage=LlmUsage(input_tokens=input_t, output_tokens=output_t,
                           cost_usd=round(cost, 6), latency_ms=latency_ms),
        )

    def _convert_message(self, msg: LlmMessage) -> dict:
        d = {"role": msg.role, "content": msg.content or ""}
        if msg.tool_call_id:
            d["tool_call_id"] = msg.tool_call_id
        return d

    async def test_connectivity(self, config) -> bool:
        try:
            api_key = os.getenv(config.api_key_ref, "")
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.minimax.chat/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=5.0,
                )
                return resp.status_code == 200
        except Exception:
            return False
```

---

## 12. Zhipu AI Provider (GLM)

Zhipu AI (智谱AI) offers the GLM (General Language Model) series — strong multilingual models with excellent Chinese language support.

**Models**: `glm-4-plus`, `glm-4-air`, `glm-4-flash`, `glm-z1-flash`, `glm-z1-air`, `glm-4v-plus` (vision)

```python
# backend/app/llm/zhipu.py
import os, time, json
from openai import AsyncOpenAI
from .openai import OpenAiProvider

ZHIPU_PRICING = {
    "glm-4-plus":   {"input": 0.00700, "output": 0.00700},
    "glm-4-air":    {"input": 0.00014, "output": 0.00014},
    "glm-4-flash":  {"input": 0.00001, "output": 0.00001},
    "glm-z1-flash": {"input": 0.00001, "output": 0.00001},
    "glm-z1-air":   {"input": 0.00100, "output": 0.00100},
    "_default":     {"input": 0.00100, "output": 0.00100},
}

class ZhipuProvider(OpenAiProvider):
    """
    Zhipu AI (智谱AI): GLM series models.
    Excellent for Chinese language tasks. OpenAI-compatible endpoint.

    Config:
        api_key_ref: env var with Zhipu API key (open.bigmodel.cn)
        model_name: "glm-4-plus" | "glm-4-air" | "glm-4-flash" | "glm-z1-flash"
    """
    BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
    PRICING = ZHIPU_PRICING

    def _make_client(self, config) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=os.getenv(config.api_key_ref, ""),
            base_url=self.BASE_URL,
        )

    async def test_connectivity(self, config) -> bool:
        try:
            client = self._make_client(config)
            await client.models.list()
            return True
        except Exception:
            return False
```

---

## 13. Custom LLM Provider (Universal Adapter)

The `CustomLlmProvider` is the most important provider for a universal, agnostic system. It allows any OpenAI-compatible endpoint — or raw HTTP endpoint — to be used without writing any code. Everything is configured via `LlmConfig.extra_config`.

**Use cases**:
- Any provider not in the built-in list
- Private or enterprise LLM deployments
- Self-hosted models (vLLM, LM Studio, llama.cpp server, LocalAI, text-generation-webui)
- Regional providers (Baidu ERNIE, Alibaba Qwen, Naver HyperCLOVA, etc.)
- Research models or custom fine-tunes via any inference server

```python
# backend/app/llm/custom.py
import os, time, json
import httpx
from openai import AsyncOpenAI
from .base import BaseLlmProvider, LlmMessage, LlmResponse, LlmToolCall, LlmUsage

class CustomLlmProvider(BaseLlmProvider):
    """
    Universal LLM provider — adapts to any endpoint.

    Supports two modes controlled by extra_config.mode:

    MODE 1: "openai_compatible" (default)
        Uses the OpenAI SDK pointed at a custom base_url.
        Works for: vLLM, LM Studio, LocalAI, Ollama, llama.cpp,
                   DeepSeek, Kimi, any OpenAI-compat endpoint.

    MODE 2: "raw_http"
        Direct HTTP POST to any endpoint with configurable
        request/response mapping. For non-standard APIs.

    extra_config fields:
        mode:               "openai_compatible" | "raw_http"    (default: openai_compatible)
        base_url:           Base URL of the API endpoint         (required)
        api_key_ref:        Env var name for API key             (optional)
        request_headers:    Static headers to include            (optional, dict)
        cost_per_1k_input:  Estimated cost per 1K input tokens   (optional, default 0)
        cost_per_1k_output: Estimated cost per 1K output tokens  (optional, default 0)

        # raw_http mode only:
        request_template:   JSON template for request body       (see below)
        response_content_path: JSONPath to content in response   (e.g. "choices.0.message.content")
        response_tokens_path:  JSONPath to token count           (e.g. "usage.total_tokens")
    """

    async def complete(self, config, messages, tools=None) -> LlmResponse:
        mode = config.extra_config.get("mode", "openai_compatible")
        if mode == "raw_http":
            return await self._complete_raw_http(config, messages, tools)
        return await self._complete_openai_compat(config, messages, tools)

    async def _complete_openai_compat(self, config, messages, tools=None) -> LlmResponse:
        """Mode 1: OpenAI-compatible endpoint via openai SDK."""
        base_url = config.extra_config.get("base_url", "http://localhost:11434/v1")
        api_key = os.getenv(
            config.extra_config.get("api_key_ref", config.api_key_ref or ""),
            "custom"   # Fallback: many local servers don't check the key
        )
        extra_headers = config.extra_config.get("request_headers", {})

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers=extra_headers,
        )

        oai_messages = []
        for m in messages:
            d = {"role": m.role, "content": m.content or ""}
            if m.tool_call_id:
                d["tool_call_id"] = m.tool_call_id
            if m.tool_calls:
                d["tool_calls"] = m.tool_calls
            oai_messages.append(d)

        kwargs = {
            "model": config.model_name,
            "messages": oai_messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        # Pass any extra model parameters from extra_config
        for k, v in config.extra_config.get("model_params", {}).items():
            kwargs[k] = v
        if tools:
            kwargs["tools"] = tools

        start = time.monotonic()
        response = await client.chat.completions.create(**kwargs)
        latency_ms = int((time.monotonic() - start) * 1000)

        choice = response.choices[0]
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, AttributeError):
                    args = {}
                tool_calls.append(LlmToolCall(id=tc.id, name=tc.function.name, arguments=args))

        input_t = response.usage.prompt_tokens if response.usage else 0
        output_t = response.usage.completion_tokens if response.usage else 0
        cost_in = config.extra_config.get("cost_per_1k_input", 0)
        cost_out = config.extra_config.get("cost_per_1k_output", 0)
        cost = (input_t / 1000) * cost_in + (output_t / 1000) * cost_out

        return LlmResponse(
            content=choice.message.content,
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else (choice.finish_reason or "stop"),
            usage=LlmUsage(input_tokens=input_t, output_tokens=output_t,
                           cost_usd=round(cost, 6), latency_ms=latency_ms),
        )

    async def _complete_raw_http(self, config, messages, tools=None) -> LlmResponse:
        """Mode 2: Raw HTTP POST — for non-OpenAI-compatible endpoints."""
        base_url = config.extra_config.get("base_url", "")
        api_key = os.getenv(config.extra_config.get("api_key_ref", ""), "")
        headers = {
            "Content-Type": "application/json",
            **config.extra_config.get("request_headers", {}),
        }
        if api_key:
            auth_style = config.extra_config.get("auth_style", "bearer")
            if auth_style == "bearer":
                headers["Authorization"] = f"Bearer {api_key}"
            elif auth_style == "api_key_header":
                headers[config.extra_config.get("api_key_header_name", "X-API-Key")] = api_key

        # Build request body from template
        template = config.extra_config.get("request_template", {
            "model": "{model}",
            "messages": "{messages}",
            "temperature": "{temperature}",
            "max_tokens": "{max_tokens}",
        })
        body = self._resolve_template(template, config, messages, tools)

        start = time.monotonic()
        async with httpx.AsyncClient() as client:
            resp = await client.post(base_url, headers=headers, json=body, timeout=120.0)
            resp.raise_for_status()
            data = resp.json()
        latency_ms = int((time.monotonic() - start) * 1000)

        # Extract content using configurable path
        content_path = config.extra_config.get("response_content_path", "choices.0.message.content")
        content = self._extract_path(data, content_path)

        tokens_path = config.extra_config.get("response_tokens_path", "usage.total_tokens")
        total_tokens = self._extract_path(data, tokens_path) or 0
        input_t = total_tokens // 2  # Rough estimate if not split
        output_t = total_tokens - input_t

        cost_in = config.extra_config.get("cost_per_1k_input", 0)
        cost_out = config.extra_config.get("cost_per_1k_output", 0)
        cost = (input_t / 1000) * cost_in + (output_t / 1000) * cost_out

        return LlmResponse(
            content=str(content) if content else None,
            tool_calls=[],  # raw_http mode doesn't support tool calling
            finish_reason="stop",
            usage=LlmUsage(input_tokens=input_t, output_tokens=output_t,
                           cost_usd=round(cost, 6), latency_ms=latency_ms),
        )

    def _resolve_template(self, template: dict, config, messages, tools) -> dict:
        """Replace {placeholder} values in request template."""
        import copy
        body = copy.deepcopy(template)
        replacements = {
            "{model}": config.model_name,
            "{temperature}": config.temperature,
            "{max_tokens}": config.max_tokens,
            "{messages}": [{"role": m.role, "content": m.content or ""} for m in messages],
        }
        for key, val in body.items():
            if isinstance(val, str) and val in replacements:
                body[key] = replacements[val]
        return body

    def _extract_path(self, data: dict, path: str):
        """Extract value from nested dict using dot notation: 'choices.0.message.content'."""
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, list):
                try: current = current[int(part)]
                except (IndexError, ValueError): return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    async def test_connectivity(self, config) -> bool:
        base_url = config.extra_config.get("base_url", "")
        if not base_url:
            return False
        try:
            async with httpx.AsyncClient() as client:
                # Try /models endpoint (OpenAI-compat) or just GET the base URL
                resp = await client.get(
                    base_url.rstrip("/") + "/models",
                    timeout=5.0,
                )
                return resp.status_code in (200, 404)  # 404 = reachable but no /models
        except Exception:
            return False
```

### Custom Provider Configuration Examples

**Example 1 — vLLM self-hosted (OpenAI-compatible)**
```json
{
  "provider": "custom",
  "model_name": "meta-llama/Llama-3.3-70B-Instruct",
  "api_key_ref": "",
  "temperature": 0.7,
  "max_tokens": 2048,
  "extra_config": {
    "mode": "openai_compatible",
    "base_url": "http://192.168.1.100:8000/v1",
    "cost_per_1k_input": 0,
    "cost_per_1k_output": 0
  }
}
```

**Example 2 — LM Studio (local GUI, OpenAI-compatible)**
```json
{
  "provider": "custom",
  "model_name": "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF",
  "api_key_ref": "",
  "temperature": 0.8,
  "max_tokens": 4096,
  "extra_config": {
    "mode": "openai_compatible",
    "base_url": "http://localhost:1234/v1"
  }
}
```

**Example 3 — Alibaba Qwen via DashScope (OpenAI-compatible)**
```json
{
  "provider": "custom",
  "model_name": "qwen-max",
  "api_key_ref": "DASHSCOPE_API_KEY",
  "temperature": 0.7,
  "max_tokens": 8192,
  "extra_config": {
    "mode": "openai_compatible",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "cost_per_1k_input": 0.004,
    "cost_per_1k_output": 0.012
  }
}
```

**Example 4 — Baidu ERNIE (raw HTTP)**
```json
{
  "provider": "custom",
  "model_name": "ernie-4.0-8k",
  "api_key_ref": "BAIDU_API_KEY",
  "temperature": 0.7,
  "max_tokens": 2048,
  "extra_config": {
    "mode": "raw_http",
    "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
    "auth_style": "api_key_header",
    "api_key_header_name": "Authorization",
    "request_template": {
      "model": "{model}",
      "messages": "{messages}",
      "temperature": "{temperature}",
      "max_output_tokens": "{max_tokens}"
    },
    "response_content_path": "result",
    "response_tokens_path": "usage.total_tokens",
    "cost_per_1k_input": 0.005,
    "cost_per_1k_output": 0.005
  }
}
```

**Example 5 — Any future provider (zero code change)**
```json
{
  "provider": "custom",
  "model_name": "some-future-model",
  "api_key_ref": "FUTURE_PROVIDER_API_KEY",
  "extra_config": {
    "mode": "openai_compatible",
    "base_url": "https://api.futureprovider.ai/v1",
    "cost_per_1k_input": 0.002,
    "cost_per_1k_output": 0.008
  }
}
```

---

## 14. Google Provider

```python
# backend/app/llm/google.py
import time
import os
import google.generativeai as genai
from .base import BaseLlmProvider, LlmMessage, LlmResponse, LlmToolCall, LlmUsage

GOOGLE_PRICING = {
    "gemini-2.0-flash": {"input": 0.00010, "output": 0.00040},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.00030},
    "_default": {"input": 0.00015, "output": 0.0006},
}

class GoogleProvider(BaseLlmProvider):

    async def complete(self, config, messages, tools=None) -> LlmResponse:
        api_key = os.getenv(config.api_key_ref)
        genai.configure(api_key=api_key)

        # Separate system instruction
        system_instruction = None
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                chat_messages.append({"role": "user", "parts": [msg.content]})
            elif msg.role == "assistant":
                chat_messages.append({"role": "model", "parts": [msg.content or ""]})
            elif msg.role == "tool":
                # Tool result — append as user function response
                chat_messages.append({
                    "role": "user",
                    "parts": [{"function_response": {
                        "name": "tool",
                        "response": {"result": msg.content}
                    }}]
                })

        model_config = {"temperature": config.temperature, "max_output_tokens": config.max_tokens}
        model = genai.GenerativeModel(
            model_name=config.model_name,
            system_instruction=system_instruction,
            generation_config=model_config
        )

        # Convert tools to Google format
        google_tools = None
        if tools:
            function_declarations = []
            for t in tools:
                fn = t["function"]
                function_declarations.append(genai.protos.FunctionDeclaration(
                    name=fn["name"],
                    description=fn["description"],
                    parameters=fn.get("parameters")
                ))
            google_tools = [genai.protos.Tool(function_declarations=function_declarations)]

        start_time = time.monotonic()
        chat = model.start_chat(history=chat_messages[:-1] if chat_messages else [])
        response = await chat.send_message_async(
            chat_messages[-1]["parts"] if chat_messages else "Hello",
            tools=google_tools
        )
        latency_ms = int((time.monotonic() - start_time) * 1000)

        # Parse response
        tool_calls = []
        text_content = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                tool_calls.append(LlmToolCall(
                    id=f"call_{part.function_call.name}",
                    name=part.function_call.name,
                    arguments=dict(part.function_call.args)
                ))
            elif hasattr(part, 'text'):
                text_content += part.text

        pricing = GOOGLE_PRICING.get(config.model_name, GOOGLE_PRICING["_default"])
        input_tokens = response.usage_metadata.prompt_token_count
        output_tokens = response.usage_metadata.candidates_token_count
        cost = (input_tokens / 1000) * pricing["input"] + (output_tokens / 1000) * pricing["output"]

        return LlmResponse(
            content=text_content or None,
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else "stop",
            usage=LlmUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=round(cost, 6),
                latency_ms=latency_ms
            )
        )

    async def test_connectivity(self, config) -> bool:
        try:
            api_key = os.getenv(config.api_key_ref)
            genai.configure(api_key=api_key)
            models = genai.list_models()
            return bool(list(models))
        except Exception:
            return False
```

---

## 9. LLM Service (Cost Tracking + Retry)

```python
# backend/app/services/llm_service.py
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai
import anthropic

RETRYABLE_OPENAI_ERRORS = (
    openai.RateLimitError,
    openai.APIConnectionError,
    openai.APITimeoutError,
    openai.InternalServerError,
)

RETRYABLE_ANTHROPIC_ERRORS = (
    anthropic.RateLimitError,
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.InternalServerError,
)

class LlmService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((*RETRYABLE_OPENAI_ERRORS, *RETRYABLE_ANTHROPIC_ERRORS)),
        reraise=True
    )
    async def complete_with_retry(
        self,
        config: LlmConfig,
        messages: list[LlmMessage],
        tools: Optional[list[dict]] = None,
        agent_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
    ) -> LlmResponse:
        """
        Call LLM with automatic retry on transient errors.
        Logs cost to LlmCallLog table.
        """
        provider = get_provider(config)
        response = await provider.complete(config, messages, tools)

        # Log every call for cost tracking
        log_entry = LlmCallLog(
            agent_id=agent_id,
            task_id=task_id,
            provider=config.provider,
            model_name=config.model_name,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cost_usd=response.usage.cost_usd,
            latency_ms=response.usage.latency_ms,
            finish_reason=response.finish_reason,
        )
        self.session.add(log_entry)
        await self.session.flush()

        return response

    async def test_provider(self, config: LlmConfig) -> dict:
        """Test if provider is reachable. Used by /llm-configs/{id}/test endpoint."""
        provider = get_provider(config)
        start_time = time.monotonic()

        try:
            success = await asyncio.wait_for(
                provider.test_connectivity(config),
                timeout=10.0
            )
            latency_ms = int((time.monotonic() - start_time) * 1000)
            return {
                "success": success,
                "provider": config.provider.value,
                "model": config.model_name,
                "latency_ms": latency_ms,
                "error": None if success else "Connectivity test failed"
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Connection timed out (10s)", "latency_ms": 10000}
        except Exception as e:
            return {"success": False, "error": str(e), "latency_ms": 0}
```

---

## 10. Cost Tracking & Reporting

### LlmCallLog Table (see database-schema.md)

All completions are logged with:
- `agent_id` + `task_id` for attribution
- `input_tokens` + `output_tokens` + `cost_usd`
- `latency_ms` for performance monitoring

### Stats Aggregation Queries

```python
# Used by GET /system/stats
async def get_cost_stats(session: AsyncSession) -> dict:
    from datetime import date, timedelta

    today_start = datetime.combine(date.today(), datetime.min.time())
    month_start = today_start.replace(day=1)

    # Today's cost
    today_cost = await session.exec(
        select(func.sum(LlmCallLog.cost_usd))
        .where(LlmCallLog.created_at >= today_start)
    ).one()

    # This month's cost
    month_cost = await session.exec(
        select(func.sum(LlmCallLog.cost_usd))
        .where(LlmCallLog.created_at >= month_start)
    ).one()

    # Cost by provider this month
    by_provider = await session.exec(
        select(LlmCallLog.provider, func.sum(LlmCallLog.cost_usd))
        .where(LlmCallLog.created_at >= month_start)
        .group_by(LlmCallLog.provider)
    ).all()

    return {
        "today_usd": round(today_cost or 0, 4),
        "this_month_usd": round(month_cost or 0, 4),
        "by_provider": {str(row[0].value): round(row[1], 4) for row in by_provider}
    }
```

---

## 11. Adding a New Provider

To add a new LLM provider:

1. Create `backend/app/llm/{provider_name}.py`
2. Implement `BaseLlmProvider` interface (`complete` + `test_connectivity`)
3. Add to `PROVIDERS` dict in `backend/app/llm/registry.py`
4. Add to `LlmProviderEnum` in `backend/app/models/enums.py`
5. Add pricing to the provider file's `PRICING` dict
6. Add Alembic migration to update the enum type in PostgreSQL

---

## 12. Requirements

```
# LLM providers
openai>=1.40.0
anthropic>=0.34.0
google-generativeai>=0.8.0

# Retry logic
tenacity>=8.2.0

# HTTP client for Ollama
httpx>=0.27.0
```
