"""
LLM Providers - Unified interface for multiple LLM backends
"""

from .base import (
    BaseLlmProvider,
    FinishReason,
    LlmResponse,
    ToolCall,
    ToolDefinition,
    ToolResult,
)
from .failover import FailoverProvider
from .registry import LlmProviderRegistry, get_provider_registry, register_provider

# Import providers to register them (with graceful fallback if deps not installed)
try:
    from .openai_provider import OpenAiProvider
except ImportError:
    pass

try:
    from .anthropic_provider import AnthropicProvider
except ImportError:
    pass

try:
    from .google_provider import GoogleProvider
except ImportError:
    pass

try:
    from .groq_provider import GroqProvider
except ImportError:
    pass

try:
    from .ollama_provider import OllamaProvider
except ImportError:
    pass

# New providers (Phase 1)
try:
    from .openrouter_provider import OpenRouterProvider
except ImportError:
    pass

try:
    from .deepseek_provider import DeepSeekProvider
except ImportError:
    pass

try:
    from .azure_openai_provider import AzureOpenAiProvider
except ImportError:
    pass

try:
    from .custom_openai_provider import CustomOpenAiProvider
except ImportError:
    pass

__all__ = [
    # Base classes
    "BaseLlmProvider",
    "LlmResponse",
    "ToolCall",
    "ToolDefinition",
    "ToolResult",
    "FinishReason",
    # Registry
    "LlmProviderRegistry",
    "get_provider_registry",
    "register_provider",
    # Failover
    "FailoverProvider",
    # Providers (may not be available)
    "OpenAiProvider",
    "AnthropicProvider",
    "GoogleProvider",
    "GroqProvider",
    "OllamaProvider",
    "OpenRouterProvider",
    "DeepSeekProvider",
    "AzureOpenAiProvider",
    "CustomOpenAiProvider",
]
