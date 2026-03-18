"""
Model Failover System — Automatic retry with fallback provider chain.

Inspired by OpenClaw's model-failover feature. When the primary provider
fails (rate limit, downtime, error), the system automatically retries with
the next provider in the chain.

Usage:
    failover = FailoverProvider(
        chain=[
            {"provider": "openai", "model": "gpt-4o", "api_key": "sk-..."},
            {"provider": "anthropic", "model": "claude-sonnet-4-20250514", "api_key": "sk-..."},
            {"provider": "openrouter", "model": "openai/gpt-4o", "api_key": "sk-..."},
        ],
        max_retries=2,
    )
    response = await failover.complete(messages)
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from .base import BaseLlmProvider, FinishReason, LlmResponse, ToolDefinition
from .registry import get_provider_registry

logger = logging.getLogger(__name__)


class FailoverProvider(BaseLlmProvider):
    """
    Meta-provider that wraps a chain of providers and tries each one
    in order until one succeeds.

    This is NOT registered in the registry—it's created on demand
    by the ExecutionService or OrchestratorService when failover is configured.
    """

    def __init__(
        self,
        chain: list[dict[str, Any]],
        max_retries: int = 2,
        retry_delay_ms: int = 500,
        **kwargs,
    ):
        """
        Args:
            chain: List of provider configs, each with keys:
                   {provider, model, api_key, base_url?, extra_config?}
            max_retries: Retries per provider before moving to next
            retry_delay_ms: Delay between retries (ms)
        """
        # Initialize base with first provider's model
        first = chain[0] if chain else {}
        super().__init__(
            model=first.get("model", "unknown"),
            api_key=first.get("api_key"),
            **kwargs,
        )

        self._chain = chain
        self._max_retries = max_retries
        self._retry_delay_ms = retry_delay_ms
        self._providers: list[BaseLlmProvider] = []
        self._active_index: int = 0

        # Instantiate all providers lazily
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazily initialize all providers in the chain."""
        if self._initialized:
            return

        registry = get_provider_registry()

        for config in self._chain:
            provider_name = config.get("provider", "openai")
            provider_class = registry.get(provider_name)
            if not provider_class:
                logger.warning(f"[failover] unknown provider '{provider_name}', skipping")
                continue

            try:
                provider = provider_class(
                    model=config.get("model", ""),
                    api_key=config.get("api_key"),
                    base_url=config.get("base_url"),
                    temperature=config.get("temperature", self.temperature),
                    max_tokens=config.get("max_tokens", self.max_tokens),
                    extra_config=config.get("extra_config", {}),
                )
                self._providers.append(provider)
            except Exception as e:
                logger.warning(f"[failover] failed to init '{provider_name}': {e}")

        if not self._providers:
            raise ValueError("No valid providers in failover chain")

        self._initialized = True

    @property
    def provider_name(self) -> str:
        return "failover"

    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> LlmResponse:
        """Try each provider in chain until one succeeds."""
        self._ensure_initialized()

        last_error: Exception | None = None

        for idx, provider in enumerate(self._providers):
            for attempt in range(self._max_retries + 1):
                try:
                    logger.info(
                        f"[failover] trying {provider.provider_name}/{provider.model} "
                        f"(provider {idx + 1}/{len(self._providers)}, "
                        f"attempt {attempt + 1}/{self._max_retries + 1})"
                    )

                    response = await provider.complete(messages, tools, system_prompt)
                    self._active_index = idx

                    # Tag response with failover metadata
                    if response.raw_response:
                        response.raw_response["_failover"] = {
                            "provider_index": idx,
                            "attempt": attempt + 1,
                            "original_provider": provider.provider_name,
                        }

                    return response

                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"[failover] {provider.provider_name}/{provider.model} "
                        f"failed (attempt {attempt + 1}): {e}"
                    )

                    if attempt < self._max_retries:
                        import asyncio
                        await asyncio.sleep(self._retry_delay_ms / 1000)

        # All providers exhausted
        raise RuntimeError(
            f"All {len(self._providers)} providers in failover chain failed. "
            f"Last error: {last_error}"
        )

    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming failover — try providers until one streams successfully."""
        self._ensure_initialized()

        last_error: Exception | None = None

        for idx, provider in enumerate(self._providers):
            try:
                logger.info(
                    f"[failover/stream] trying {provider.provider_name}/{provider.model}"
                )
                async for chunk in provider.complete_stream(
                    messages, tools, system_prompt
                ):
                    yield chunk
                self._active_index = idx
                return  # Success

            except Exception as e:
                last_error = e
                logger.warning(
                    f"[failover/stream] {provider.provider_name} failed: {e}"
                )

        raise RuntimeError(
            f"All providers in failover chain failed (stream). Last error: {last_error}"
        )

    async def get_token_count(self, text: str) -> int:
        """Delegate to first available provider."""
        self._ensure_initialized()
        return await self._providers[self._active_index].get_token_count(text)

    async def test_connection(self) -> bool:
        """Test all providers in chain, return True if at least one works."""
        self._ensure_initialized()
        for provider in self._providers:
            try:
                if await provider.test_connection():
                    return True
            except Exception:
                continue
        return False

    async def close(self):
        """Close all provider connections."""
        for provider in self._providers:
            try:
                await provider.close()
            except Exception:
                pass

    @property
    def active_provider(self) -> BaseLlmProvider | None:
        """Get the currently active (last successful) provider."""
        if self._providers and self._active_index < len(self._providers):
            return self._providers[self._active_index]
        return None
