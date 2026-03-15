"""
LLM Configs API Endpoints
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_session
from ...services import LLMService
from ...models.enums import LlmProviderEnum
from ...core.providers import ToolDefinition

router = APIRouter()


@router.get("/llm-configs", response_model=dict)
async def list_llm_configs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """List all LLM configurations"""
    service = LLMService(session)
    configs = await service.get_configs(
        skip=skip,
        limit=limit,
    )
    
    return {
        "data": configs,
        "meta": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": len(configs),
        },
    }


@router.post("/llm-configs", response_model=dict)
async def create_llm_config(
    config_data: dict,
    session: AsyncSession = Depends(get_session),
):
    """Create a new LLM configuration"""
    service = LLMService(session)
    
    config = await service.create_config(
        name=config_data["name"],
        provider=LlmProviderEnum(config_data["provider"]),
        model_name=config_data["model_name"],
        api_key_ref=config_data.get("api_key_ref"),
        temperature=config_data.get("temperature", 0.7),
        max_tokens=config_data.get("max_tokens", 4096),
        top_p=config_data.get("top_p", 1.0),
        extra_config=config_data.get("extra_config", {}),
    )
    
    return {"data": config}


@router.get("/llm-configs/{config_id}", response_model=dict)
async def get_llm_config(
    config_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get LLM config by ID"""
    service = LLMService(session)
    config = await service.get_config(config_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="LLM config not found")
    
    return {"data": config}


@router.put("/llm-configs/{config_id}", response_model=dict)
async def update_llm_config(
    config_id: UUID,
    updates: dict,
    session: AsyncSession = Depends(get_session),
):
    """Update LLM configuration"""
    service = LLMService(session)
    config = await service.update_config(config_id, **updates)
    
    if not config:
        raise HTTPException(status_code=404, detail="LLM config not found")
    
    return {"data": config}


@router.delete("/llm-configs/{config_id}", response_model=dict)
async def delete_llm_config(
    config_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete LLM configuration"""
    service = LLMService(session)
    success = await service.delete_config(config_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="LLM config not found")
    
    return {"message": "LLM config deleted successfully"}


# Providers info

@router.get("/llm-providers", response_model=dict)
async def list_llm_providers(
    session: AsyncSession = Depends(get_session),
):
    """List all available LLM providers with their models"""
    service = LLMService(session)
    registered = service.list_available_providers()
    
    providers = {
        "openai": {
            "name": "OpenAI",
            "models": [
                {"id": "gpt-4o", "name": "GPT-4o", "context_window": 128000},
                {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context_window": 128000},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context_window": 128000},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context_window": 16385},
            ],
        },
        "anthropic": {
            "name": "Anthropic",
            "models": [
                {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "context_window": 200000},
                {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "context_window": 200000},
                {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "context_window": 200000},
                {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "context_window": 200000},
            ],
        },
        "groq": {
            "name": "Groq",
            "models": [
                {"id": "llama-3.1-70b-versatile", "name": "Llama 3.1 70B", "context_window": 131072},
                {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B", "context_window": 131072},
                {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "context_window": 32768},
                {"id": "gemma-7b-it", "name": "Gemma 7B", "context_window": 8192},
            ],
        },
        "ollama": {
            "name": "Ollama (Local)",
            "models": [
                {"id": "llama3.1", "name": "Llama 3.1", "context_window": 128000},
                {"id": "mistral", "name": "Mistral", "context_window": 8192},
                {"id": "codellama", "name": "CodeLlama", "context_window": 16384},
                {"id": "llama2", "name": "Llama 2", "context_window": 4096},
            ],
        },
        "google": {
            "name": "Google AI",
            "models": [
                {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "context_window": 2097152},
                {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "context_window": 1048576},
                {"id": "gemini-1.0-pro", "name": "Gemini 1.0 Pro", "context_window": 32768},
            ],
        },
    }
    
    # Filter to only registered providers
    available = {k: v for k, v in providers.items() if k in registered}
    
    return {"data": available}


# Test connectivity

@router.post("/llm-configs/{config_id}/test", response_model=dict)
async def test_llm_connection(
    config_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Test connectivity to LLM provider"""
    service = LLMService(session)
    
    connected = await service.test_config(config_id)
    
    return {
        "data": {
            "connected": connected,
            "message": "Connection successful" if connected else "Connection failed",
        },
    }


@router.get("/llm-configs/{config_id}/usage", response_model=dict)
async def get_llm_usage_stats(
    config_id: UUID,
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
):
    """Get usage statistics for a config"""
    service = LLMService(session)
    # Note: get_cost_stats filters by config_id not implemented yet
    stats = await service.get_cost_stats(agent_id=None, days=days)
    
    return {"data": stats}


# Chat completion endpoint

@router.post("/llm-configs/{config_id}/chat", response_model=dict)
async def chat_completion(
    config_id: UUID,
    chat_data: dict,
    session: AsyncSession = Depends(get_session),
):
    """
    Generate chat completion using a specific config.
    
    Request body:
    {
        "messages": [{"role": "user", "content": "Hello"}],
        "system_prompt": "Optional system prompt",
        "tools": [{"name": "...", "description": "...", "parameters": {...}}]
    }
    """
    service = LLMService(session)
    
    messages = chat_data.get("messages", [])
    system_prompt = chat_data.get("system_prompt")
    
    # Convert tool definitions
    tools = None
    if "tools" in chat_data:
        tools = [
            ToolDefinition(
                name=t["name"],
                description=t["description"],
                parameters=t["parameters"],
            )
            for t in chat_data["tools"]
        ]
    
    try:
        response = await service.complete(
            config_id=config_id,
            messages=messages,
            tools=tools,
            system_prompt=system_prompt,
        )
        
        return {
            "data": {
                "content": response.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments,
                    }
                    for tc in response.tool_calls
                ],
                "finish_reason": response.finish_reason.value,
                "usage": {
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "total_tokens": response.total_tokens,
                },
                "model": response.model,
                "latency_ms": response.latency_ms,
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")
