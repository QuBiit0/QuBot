"""
LLM Service - Business logic for LLM configuration and cost tracking
"""
import os
from typing import List, Optional, Dict, Any, AsyncGenerator
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models.llm import LlmConfig, LlmCallLog
from ..models.enums import LlmProviderEnum
from ..core.providers import (
    get_provider_registry,
    LlmResponse,
    ToolDefinition,
    FinishReason,
)


class LLMService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._provider_registry = get_provider_registry()
    
    async def create_provider(self, config_id: UUID):
        """
        Create a provider instance from a stored configuration.
        
        Args:
            config_id: UUID of the LLM configuration
            
        Returns:
            Configured provider instance
        """
        config = await self.get_config(config_id)
        if not config:
            raise ValueError(f"LLM config not found: {config_id}")
        
        # Get API key from environment variable reference
        api_key = None
        if config.api_key_ref:
            api_key = os.getenv(config.api_key_ref)
        
        # Get base URL from extra_config if present
        base_url = config.extra_config.get("base_url") if config.extra_config else None
        
        # Create provider
        return self._provider_registry.create_provider(
            provider_name=config.provider.value,
            model=config.model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            extra_config=config.extra_config or {},
        )
    
    async def complete(
        self,
        config_id: UUID,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolDefinition]] = None,
        system_prompt: Optional[str] = None,
        agent_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
    ) -> LlmResponse:
        """
        Generate completion with automatic cost logging.
        
        Args:
            config_id: LLM configuration to use
            messages: List of message dicts with 'role' and 'content'
            tools: Optional tools for function calling
            system_prompt: Optional system prompt
            agent_id: Optional agent ID for cost tracking
            task_id: Optional task ID for cost tracking
            
        Returns:
            LlmResponse with standardized format
        """
        # Create provider
        provider = await self.create_provider(config_id)
        
        # Get config for logging
        config = await self.get_config(config_id)
        
        try:
            # Generate completion
            response = await provider.complete(
                messages=messages,
                tools=tools,
                system_prompt=system_prompt,
            )
            
            # Log the call
            await self.log_call(
                provider=config.provider,
                model_name=config.model_name,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost_usd=self._estimate_cost(provider, response),
                latency_ms=response.latency_ms,
                finish_reason=response.finish_reason.value,
                agent_id=agent_id,
                task_id=task_id,
                llm_config_id=config_id,
            )
            
            return response
            
        finally:
            # Clean up provider
            await provider.close()
    
    async def complete_stream(
        self,
        config_id: UUID,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming completion.
        
        Note: Cost tracking is not available for streaming completions.
        """
        provider = await self.create_provider(config_id)
        
        try:
            async for chunk in provider.complete_stream(
                messages=messages,
                system_prompt=system_prompt,
            ):
                yield chunk
        finally:
            await provider.close()
    
    async def test_config(self, config_id: UUID) -> bool:
        """Test if an LLM configuration is valid and working"""
        try:
            provider = await self.create_provider(config_id)
            result = await provider.test_connection()
            await provider.close()
            return result
        except Exception:
            return False
    
    def _estimate_cost(self, provider, response: LlmResponse) -> float:
        """Estimate cost using provider's pricing"""
        return provider._estimate_cost(
            response.input_tokens,
            response.output_tokens,
        )
    
    # Configuration Management
    
    async def create_config(
        self,
        name: str,
        provider: LlmProviderEnum,
        model_name: str,
        api_key_ref: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int = 4096,
        extra_config: Optional[dict] = None,
    ) -> LlmConfig:
        """Create a new LLM configuration"""
        config = LlmConfig(
            name=name,
            provider=provider,
            model_name=model_name,
            api_key_ref=api_key_ref,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            extra_config=extra_config or {},
        )
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config
    
    async def get_config(self, config_id: UUID) -> Optional[LlmConfig]:
        """Get LLM config by ID"""
        result = await self.session.execute(
            select(LlmConfig).where(LlmConfig.id == config_id)
        )
        return result.scalar_one_or_none()
    
    async def get_configs(self, skip: int = 0, limit: int = 100) -> List[LlmConfig]:
        """Get all LLM configurations"""
        result = await self.session.execute(
            select(LlmConfig).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def update_config(
        self,
        config_id: UUID,
        **updates
    ) -> Optional[LlmConfig]:
        """Update LLM config fields"""
        config = await self.get_config(config_id)
        if not config:
            return None
        
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        await self.session.commit()
        await self.session.refresh(config)
        return config
    
    async def delete_config(self, config_id: UUID) -> bool:
        """Delete an LLM config"""
        config = await self.get_config(config_id)
        if not config:
            return False
        
        await self.session.delete(config)
        await self.session.commit()
        return True
    
    # Cost Tracking
    
    async def log_call(
        self,
        provider: LlmProviderEnum,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: int,
        finish_reason: str,
        agent_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        llm_config_id: Optional[UUID] = None,
    ) -> LlmCallLog:
        """Log an LLM API call for cost tracking"""
        log = LlmCallLog(
            provider=provider,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            agent_id=agent_id,
            task_id=task_id,
            llm_config_id=llm_config_id,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log
    
    async def get_cost_stats(
        self,
        agent_id: Optional[UUID] = None,
        days: int = 30,
    ) -> dict:
        """Get cost statistics"""
        since = datetime.utcnow() - timedelta(days=days)
        
        query = select(LlmCallLog).where(LlmCallLog.created_at >= since)
        if agent_id:
            query = query.where(LlmCallLog.agent_id == agent_id)
        
        result = await self.session.execute(query)
        logs = result.scalars().all()
        
        total_cost = sum(log.cost_usd for log in logs)
        total_tokens = sum(log.input_tokens + log.output_tokens for log in logs)
        total_calls = len(logs)
        
        # Cost by provider
        provider_costs = {}
        for log in logs:
            provider = log.provider.value
            provider_costs[provider] = provider_costs.get(provider, 0) + log.cost_usd
        
        # Cost by model
        model_costs = {}
        for log in logs:
            model_costs[log.model_name] = model_costs.get(log.model_name, 0) + log.cost_usd
        
        return {
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "total_calls": total_calls,
            "by_provider": {k: round(v, 4) for k, v in provider_costs.items()},
            "by_model": {k: round(v, 4) for k, v in model_costs.items()},
        }
    
    async def get_default_configs(self) -> List[LlmConfig]:
        """Get or create default LLM configurations"""
        result = await self.session.execute(select(LlmConfig))
        configs = result.scalars().all()
        
        if not configs:
            default_configs = [
                {
                    "name": "GPT-4o",
                    "provider": LlmProviderEnum.OPENAI,
                    "model_name": "gpt-4o",
                    "api_key_ref": "OPENAI_API_KEY",
                },
                {
                    "name": "Claude 3.5 Sonnet",
                    "provider": LlmProviderEnum.ANTHROPIC,
                    "model_name": "claude-3-5-sonnet-20241022",
                    "api_key_ref": "ANTHROPIC_API_KEY",
                },
                {
                    "name": "Gemini 1.5 Pro",
                    "provider": LlmProviderEnum.GOOGLE,
                    "model_name": "gemini-1.5-pro",
                    "api_key_ref": "GOOGLE_API_KEY",
                },
                {
                    "name": "Llama 3.3 70B (Groq)",
                    "provider": LlmProviderEnum.GROQ,
                    "model_name": "llama-3.3-70b-versatile",
                    "api_key_ref": "GROQ_API_KEY",
                },
                {
                    "name": "Local (Ollama)",
                    "provider": LlmProviderEnum.LOCAL,
                    "model_name": "llama3.2",
                    "api_key_ref": "OLLAMA_HOST",
                    "extra_config": {"base_url": "http://localhost:11434"},
                },
            ]
            
            for config_data in default_configs:
                config = LlmConfig(**config_data)
                self.session.add(config)
            
            await self.session.commit()
            
            result = await self.session.execute(select(LlmConfig))
            return result.scalars().all()
        
        return configs
    
    # Utility methods
    
    def list_available_providers(self) -> List[str]:
        """List all registered provider names"""
        return self._provider_registry.list_providers()
