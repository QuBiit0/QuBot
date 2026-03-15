from typing import Dict, Type
from .base import BaseLlmProvider
from ..config import settings

class LlmProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, Type[BaseLlmProvider]] = {}

    def register(self, name: str, provider_class: Type[BaseLlmProvider]):
        self._providers[name] = provider_class

    def get_provider_instance(self, name: str, **kwargs) -> BaseLlmProvider:
        if name not in self._providers:
            raise ValueError(f"Proveedor LLM '{name}' no encontrado.")
        return self._providers[name](**kwargs)

# Singleton registry
llm_registry = LlmProviderRegistry()

# Implementación rápida de OpenAI Provider (Placeholder para esta etapa)
class OpenAIProvider(BaseLlmProvider):
    def __init__(self, api_key: str = settings.OPENAI_API_KEY):
        self.api_key = api_key
        # Iniciar cliente OpenAI aquí

    async def complete(self, messages, tools=None, temperature=0.7, max_tokens=2000):
        # Lógica real de OpenAI
        pass

    async def test_connectivity(self):
        return bool(self.api_key)

# Registrar proveedores iniciales
llm_registry.register("openai", OpenAIProvider)
# llm_registry.register("anthropic", AnthropicProvider)
