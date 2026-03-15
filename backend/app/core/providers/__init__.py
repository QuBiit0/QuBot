"""
LLM Providers - Unified interface for multiple LLM backends
"""
from .base import BaseLlmProvider, LlmResponse, ToolCall, ToolDefinition, ToolResult, FinishReason
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
    # Providers (may not be available)
    "OpenAiProvider",
    "AnthropicProvider",
    "GoogleProvider",
    "GroqProvider",
    "OllamaProvider",
]
