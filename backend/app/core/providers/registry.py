"""
LLM Provider Registry - Factory and registry for all LLM providers
"""
from typing import Dict, Type, Optional, List
from .base import BaseLlmProvider


class LlmProviderRegistry:
    """Registry for LLM provider classes"""
    
    def __init__(self):
        self._providers: Dict[str, Type[BaseLlmProvider]] = {}
    
    def register(
        self,
        provider_name: str,
        provider_class: Type[BaseLlmProvider],
    ) -> None:
        """Register a provider class"""
        self._providers[provider_name.lower()] = provider_class
    
    def get(
        self,
        provider_name: str,
    ) -> Optional[Type[BaseLlmProvider]]:
        """Get provider class by name"""
        return self._providers.get(provider_name.lower())
    
    def create_provider(
        self,
        provider_name: str,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs,
    ) -> BaseLlmProvider:
        """
        Create a provider instance.
        
        Args:
            provider_name: Name of the provider (e.g., 'openai', 'anthropic')
            model: Model name
            api_key: API key for the provider
            base_url: Optional custom base URL
            **kwargs: Additional configuration
            
        Returns:
            Configured provider instance
            
        Raises:
            ValueError: If provider not found
        """
        provider_class = self.get(provider_name)
        if not provider_class:
            available = ", ".join(self.list_providers())
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Available: {available}"
            )
        
        return provider_class(
            model=model,
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )
    
    def list_providers(self) -> List[str]:
        """List all registered provider names"""
        return list(self._providers.keys())
    
    def unregister(self, provider_name: str) -> None:
        """Unregister a provider"""
        self._providers.pop(provider_name.lower(), None)


# Global registry instance
_registry: Optional[LlmProviderRegistry] = None


def get_provider_registry() -> LlmProviderRegistry:
    """Get or create global provider registry"""
    global _registry
    if _registry is None:
        _registry = LlmProviderRegistry()
    return _registry


def register_provider(provider_name: str):
    """Decorator to register a provider class"""
    def decorator(cls: Type[BaseLlmProvider]):
        registry = get_provider_registry()
        registry.register(provider_name, cls)
        return cls
    return decorator
