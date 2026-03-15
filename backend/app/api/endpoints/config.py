"""
Configuration Endpoints - Complete configuration management API

Provides endpoints for:
- Reading/Writing system configuration
- Managing configuration presets
- Importing/Exporting configuration
- Viewing configuration history
- Environment-specific overrides
- Statistics and validation
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.config_service import (
    ConfigService, 
    ConfigError, 
    ConfigValidationError, 
    ConfigNotFoundError
)
from app.models.config import (
    ConfigCategory, 
    ConfigValueType, 
    SystemConfig,
    ConfigPreset,
    ConfigHistory
)
from app.config import settings as env_settings

router = APIRouter(prefix="/config", tags=["config"])


# Helper function
async def get_config_service(session: AsyncSession = Depends(get_session)) -> ConfigService:
    return ConfigService(session)


# ============================================
# Configuration CRUD
# ============================================

@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="List all configurations",
    description="Get all system configurations with optional filtering by category"
)
async def get_all_configuration(
    category: Optional[ConfigCategory] = None,
    include_secrets: bool = Query(False, description="Include secret values (admin only)"),
    service: ConfigService = Depends(get_config_service)
):
    """
    Get all configuration values.
    
    - **category**: Filter by category (general, security, llm, messaging, features, ui, advanced)
    - **include_secrets**: If true, include secret values (requires admin permissions)
    """
    try:
        if category:
            configs = await service.get_by_category(category)
        else:
            configs = await service.get_all(include_secrets=include_secrets)
        
        return {
            "success": True,
            "configs": [
                {
                    "id": str(config.id),
                    "key": config.key,
                    "value": config.get_value() if not config.is_secret else "***MASKED***",
                    "type": config.value_type.value,
                    "category": config.category.value,
                    "description": config.description,
                    "is_editable": config.is_editable,
                    "is_secret": config.is_secret,
                    "requires_restart": config.requires_restart,
                    "updated_at": config.updated_at.isoformat(),
                    "updated_by": config.updated_by,
                }
                for config in configs
            ],
            "count": len(configs),
            "categories": list(ConfigCategory.__members__.keys())
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving configurations: {str(e)}"
        )


@router.get(
    "/{key}",
    response_model=Dict[str, Any],
    summary="Get configuration by key",
    description="Retrieve a specific configuration value by its key"
)
async def get_configuration_value(
    key: str,
    service: ConfigService = Depends(get_config_service)
):
    """Get a specific configuration value by key"""
    try:
        config = await service.get_by_key(key)
        if not config:
            raise ConfigNotFoundError(f"Configuration key '{key}' not found")
        
        return {
            "success": True,
            "config": {
                "id": str(config.id),
                "key": config.key,
                "value": config.get_value() if not config.is_secret else "***MASKED***",
                "type": config.value_type.value,
                "category": config.category.value,
                "description": config.description,
                "is_editable": config.is_editable,
                "is_secret": config.is_secret,
                "requires_restart": config.requires_restart,
                "updated_at": config.updated_at.isoformat(),
                "updated_by": config.updated_by,
            }
        }
    except ConfigNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving configuration: {str(e)}"
        )


@router.post(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create configuration",
    description="Create a new configuration value"
)
async def create_configuration(
    key: str = Body(..., description="Configuration key (lowercase with underscores)"),
    value: Any = Body(..., description="Configuration value"),
    value_type: ConfigValueType = Body(default=ConfigValueType.STRING, description="Value type"),
    category: ConfigCategory = Body(default=ConfigCategory.GENERAL, description="Category"),
    description: str = Body(default="", description="Description"),
    is_editable: bool = Body(default=True, description="Is editable"),
    is_secret: bool = Body(default=False, description="Is secret"),
    requires_restart: bool = Body(default=False, description="Requires restart"),
    updated_by: Optional[str] = Body(default=None, description="Updated by user"),
    service: ConfigService = Depends(get_config_service)
):
    """Create a new configuration value"""
    try:
        config = await service.create(
            key=key,
            value=value,
            value_type=value_type,
            category=category,
            description=description,
            is_editable=is_editable,
            is_secret=is_secret,
            requires_restart=requires_restart,
            updated_by=updated_by
        )
        return {
            "success": True,
            "message": "Configuration created successfully",
            "config": {
                "id": str(config.id),
                "key": config.key,
                "value": config.get_value() if not config.is_secret else "***MASKED***",
                "type": config.value_type.value,
                "category": config.category.value,
            }
        }
    except ConfigValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConfigError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating configuration: {str(e)}"
        )


@router.put(
    "/{key}",
    response_model=Dict[str, Any],
    summary="Update configuration",
    description="Update an existing configuration value"
)
async def update_configuration(
    key: str,
    value: Any = Body(..., description="New value"),
    updated_by: Optional[str] = Body(default=None, description="Updated by user"),
    change_reason: Optional[str] = Body(default=None, description="Reason for change"),
    skip_validation: bool = Body(default=False, description="Skip validation"),
    service: ConfigService = Depends(get_config_service)
):
    """Update a configuration value"""
    try:
        config = await service.update(key, value, updated_by, change_reason, skip_validation)
        
        return {
            "success": True,
            "message": "Configuration updated successfully. Restart required." if config.requires_restart else "Configuration updated successfully.",
            "config": {
                "key": config.key,
                "value": config.get_value() if not config.is_secret else "***MASKED***",
                "requires_restart": config.requires_restart,
                "updated_at": config.updated_at.isoformat(),
            }
        }
    except ConfigNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConfigValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConfigError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating configuration: {str(e)}"
        )


@router.delete(
    "/{key}",
    response_model=Dict[str, Any],
    summary="Delete configuration",
    description="Delete a configuration value"
)
async def delete_configuration(
    key: str,
    service: ConfigService = Depends(get_config_service)
):
    """Delete a configuration value"""
    try:
        success = await service.delete(key)
        return {
            "success": True,
            "message": f"Configuration '{key}' deleted successfully"
        }
    except ConfigNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConfigError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting configuration: {str(e)}"
        )


@router.post(
    "/bulk-update",
    response_model=Dict[str, Any],
    summary="Bulk update configurations",
    description="Update multiple configuration values at once"
)
async def bulk_update_configuration(
    updates: Dict[str, Any] = Body(..., description="Dictionary of key-value pairs to update"),
    updated_by: Optional[str] = Body(default=None, description="Updated by user"),
    change_reason: Optional[str] = Body(default=None, description="Reason for changes"),
    service: ConfigService = Depends(get_config_service)
):
    """Update multiple configuration values at once"""
    try:
        results = await service.bulk_update(updates, updated_by, change_reason)
        
        success_count = sum(1 for result in results.values() if result is True)
        
        return {
            "success": True,
            "results": results,
            "summary": {
                "total": len(results),
                "successful": success_count,
                "failed": len(results) - success_count
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in bulk update: {str(e)}"
        )


# ============================================
# Import/Export
# ============================================

@router.get(
    "/export/all",
    response_model=Dict[str, Any],
    summary="Export configuration",
    description="Export all configuration to JSON format for backup or migration"
)
async def export_all_configuration(
    category: Optional[ConfigCategory] = None,
    include_secrets: bool = Query(False, description="Include secret values"),
    service: ConfigService = Depends(get_config_service)
):
    """Export configuration to JSON (for backup/migration)"""
    try:
        config_data = await service.export_config(category, include_secrets)
        return config_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting configuration: {str(e)}"
        )


@router.post(
    "/import",
    response_model=Dict[str, Any],
    summary="Import configuration",
    description="Import configuration from JSON format"
)
async def import_configuration(
    data: Dict[str, Any] = Body(..., description="Configuration data to import"),
    overwrite_existing: bool = Body(default=True, description="Overwrite existing values"),
    skip_validation: bool = Body(default=False, description="Skip validation"),
    updated_by: Optional[str] = Body(default=None, description="Imported by user"),
    service: ConfigService = Depends(get_config_service)
):
    """Import configuration from JSON"""
    try:
        results = await service.import_config(data, updated_by, overwrite_existing, skip_validation)
        
        success_count = sum(1 for result in results.values() if result is True)
        
        return {
            "success": True,
            "results": results,
            "summary": {
                "total": len(results),
                "successful": success_count,
                "failed": len(results) - success_count
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing configuration: {str(e)}"
        )


# ============================================
# Configuration Presets
# ============================================

@router.get(
    "/presets/list",
    response_model=Dict[str, Any],
    summary="List presets",
    description="List all configuration presets"
)
async def list_presets(
    category: Optional[str] = None,
    service: ConfigService = Depends(get_config_service)
):
    """List all configuration presets"""
    try:
        from sqlalchemy import select
        
        query = select(ConfigPreset)
        if category:
            query = query.where(ConfigPreset.category == category)
        
        result = await service.session.execute(query)
        presets = result.scalars().all()
        
        return {
            "success": True,
            "presets": [
                {
                    "id": str(preset.id),
                    "name": preset.name,
                    "description": preset.description,
                    "category": preset.category,
                    "is_active": preset.is_active,
                    "created_at": preset.created_at.isoformat(),
                }
                for preset in presets
            ],
            "count": len(presets)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing presets: {str(e)}"
        )


@router.post(
    "/presets/create",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create preset",
    description="Create a new configuration preset"
)
async def create_preset(
    name: str = Body(..., description="Preset name"),
    description: str = Body(default="", description="Preset description"),
    values: Dict[str, Any] = Body(default={}, description="Configuration values"),
    category: str = Body(default="custom", description="Preset category"),
    service: ConfigService = Depends(get_config_service)
):
    """Create a new configuration preset"""
    try:
        preset = await service.create_preset(name, description, values, category)
        return {
            "success": True,
            "message": "Preset created successfully",
            "preset": {
                "id": str(preset.id),
                "name": preset.name,
                "description": preset.description,
                "category": preset.category,
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating preset: {str(e)}"
        )


@router.post(
    "/presets/{preset_id}/apply",
    response_model=Dict[str, Any],
    summary="Apply preset",
    description="Apply a configuration preset to the system"
)
async def apply_preset(
    preset_id: UUID,
    updated_by: Optional[str] = Body(default=None, description="Applied by user"),
    service: ConfigService = Depends(get_config_service)
):
    """Apply a configuration preset"""
    try:
        success = await service.apply_preset(preset_id, updated_by)
        return {
            "success": True,
            "message": f"Preset '{preset_id}' applied successfully"
        }
    except ConfigNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error applying preset: {str(e)}"
        )


# ============================================
# Configuration History
# ============================================

@router.get(
    "/history/list",
    response_model=Dict[str, Any],
    summary="Configuration history",
    description="Get configuration change history"
)
async def get_configuration_history(
    key: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    service: ConfigService = Depends(get_config_service)
):
    """Get configuration change history"""
    try:
        history = await service.get_history(key, category, limit, offset)
        
        return {
            "success": True,
            "history": [
                {
                    "id": str(h.id),
                    "config_key": h.config_key,
                    "category": h.category,
                    "old_value": h.old_value,
                    "new_value": h.new_value,
                    "changed_by": h.changed_by,
                    "changed_at": h.changed_at.isoformat(),
                    "change_reason": h.change_reason,
                }
                for h in history
            ],
            "count": len(history),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving history: {str(e)}"
        )


# ============================================
# Statistics & Validation
# ============================================

@router.get(
    "/statistics/overview",
    response_model=Dict[str, Any],
    summary="Configuration statistics",
    description="Get configuration statistics and overview"
)
async def get_statistics(
    service: ConfigService = Depends(get_config_service)
):
    """Get configuration statistics"""
    try:
        stats = await service.get_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )


@router.post(
    "/validate",
    response_model=Dict[str, Any],
    summary="Validate configuration",
    description="Validate a configuration value before updating"
)
async def validate_configuration(
    key: str = Body(..., description="Configuration key"),
    value: Any = Body(..., description="Value to validate"),
    service: ConfigService = Depends(get_config_service)
):
    """Validate a configuration value before updating"""
    try:
        is_valid, error_msg = await service.validate_config(key, value)
        
        return {
            "valid": is_valid,
            "key": key,
            "value": value,
            "error": error_msg
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating configuration: {str(e)}"
        )


@router.post(
    "/validate-bulk",
    response_model=Dict[str, Any],
    summary="Validate multiple configurations",
    description="Validate multiple configuration values before updating"
)
async def validate_bulk_configuration(
    updates: Dict[str, Any] = Body(..., description="Dictionary of key-value pairs to validate"),
    service: ConfigService = Depends(get_config_service)
):
    """Validate multiple configuration values before updating"""
    try:
        results = {}
        for key, value in updates.items():
            is_valid, error_msg = await service.validate_config(key, value)
            results[key] = {
                "valid": is_valid,
                "error": error_msg
            }
        
        all_valid = all(r["valid"] for r in results.values())
        
        return {
            "valid": all_valid,
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating configurations: {str(e)}"
        )


# ============================================
# Initialize
# ============================================

@router.post(
    "/initialize",
    response_model=Dict[str, Any],
    summary="Initialize defaults",
    description="Initialize default configuration values (run once on first setup)"
)
async def initialize_default_configuration(
    service: ConfigService = Depends(get_config_service)
):
    """Initialize default configuration values (run once on first setup)"""
    try:
        results = await service.initialize_defaults()
        
        created_count = sum(1 for v in results.values() if v is True)
        
        return {
            "success": True,
            "message": "Default configuration initialized",
            "created": created_count,
            "skipped": len(results) - created_count,
            "details": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing defaults: {str(e)}"
        )


# ============================================
# Environment Configuration
# ============================================

@router.get(
    "/environment/current",
    response_model=Dict[str, Any],
    summary="Current environment",
    description="Get current environment configuration summary"
)
async def get_current_environment_config():
    """Get current environment configuration summary"""
    return {
        "success": True,
        "environment": "production" if not env_settings.DEBUG else "development",
        "debug": env_settings.DEBUG,
        "log_level": env_settings.LOG_LEVEL,
        "database_configured": bool(env_settings.DATABASE_URL),
        "redis_configured": bool(env_settings.REDIS_URL),
        "public_domain": env_settings.PUBLIC_DOMAIN or "Not set",
        "features": {
            "registration": env_settings.ENABLE_REGISTRATION,
            "ollama": env_settings.ENABLE_OLLAMA,
            "rate_limiting": env_settings.RATE_LIMIT_ENABLED,
        }
    }


# ============================================
# Specific Category Endpoints
# ============================================

@router.get(
    "/category/llm-providers",
    response_model=Dict[str, Any],
    summary="LLM providers status",
    description="Get LLM providers configuration status"
)
async def get_llm_providers_status():
    """Get LLM providers configuration status"""
    providers = []
    
    provider_configs = [
        ("OpenAI", "OPENAI", env_settings.OPENAI_API_KEY, ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]),
        ("Anthropic", "ANTHROPIC", env_settings.ANTHROPIC_API_KEY, ["claude-3-5-sonnet", "claude-3-opus"]),
        ("Google", "GOOGLE", env_settings.GOOGLE_API_KEY, ["gemini-pro", "gemini-pro-vision"]),
        ("Groq", "GROQ", env_settings.GROQ_API_KEY, ["llama-3.1-70b", "mixtral-8x7b"]),
        ("OpenRouter", "OPENROUTER", env_settings.OPENROUTER_API_KEY, ["auto-routing"]),
        ("DeepSeek", "DEEPSEEK", env_settings.DEEPSEEK_API_KEY, ["deepseek-chat", "deepseek-coder"]),
        ("Kimi", "KIMI", env_settings.KIMI_API_KEY, ["kimi-chat"]),
        ("MiniMax", "MINIMAX", env_settings.MINIMAX_API_KEY, ["minimax-chat"]),
        ("Zhipu", "ZHIPU", env_settings.ZHIPU_API_KEY, ["chatglm"]),
    ]
    
    for name, provider, key, models in provider_configs:
        providers.append({
            "name": name,
            "provider": provider,
            "configured": bool(key),
            "models": models
        })
    
    # Add Ollama
    providers.append({
        "name": "Ollama (Local)",
        "provider": "LOCAL",
        "configured": env_settings.ENABLE_OLLAMA,
        "models": ["local-models"],
        "host": env_settings.OLLAMA_HOST
    })
    
    return {
        "success": True,
        "default_provider": env_settings.DEFAULT_LLM_PROVIDER,
        "default_model": env_settings.DEFAULT_LLM_MODEL,
        "default_temperature": env_settings.DEFAULT_LLM_TEMPERATURE,
        "default_max_tokens": env_settings.DEFAULT_LLM_MAX_TOKENS,
        "providers": providers,
        "total_configured": sum(1 for p in providers if p["configured"])
    }


@router.get(
    "/category/messaging",
    response_model=Dict[str, Any],
    summary="Messaging status",
    description="Get messaging platform configuration status"
)
async def get_messaging_status():
    """Get messaging platform configuration status"""
    return {
        "success": True,
        "public_domain": env_settings.PUBLIC_DOMAIN or "Not set - required for webhooks",
        "platforms": {
            "telegram": {
                "name": "Telegram",
                "enabled": env_settings.telegram_enabled,
                "configured": env_settings.telegram_enabled,
                "token_configured": bool(env_settings.TELEGRAM_BOT_TOKEN),
                "webhook_url": env_settings.TELEGRAM_WEBHOOK_URL or (f"{env_settings.PUBLIC_DOMAIN}/api/v1/telegram/webhook" if env_settings.PUBLIC_DOMAIN else None),
                "setup_endpoint": "/api/v1/telegram/setup",
                "config_endpoint": "/api/v1/telegram/config",
            },
            "discord": {
                "name": "Discord",
                "enabled": env_settings.discord_enabled,
                "configured": env_settings.discord_enabled and bool(env_settings.DISCORD_APPLICATION_ID),
                "token_configured": bool(env_settings.DISCORD_BOT_TOKEN),
                "application_id_configured": bool(env_settings.DISCORD_APPLICATION_ID),
                "setup_endpoint": "/api/v1/discord/setup",
            },
            "slack": {
                "name": "Slack",
                "enabled": env_settings.slack_enabled,
                "configured": env_settings.slack_enabled and bool(env_settings.SLACK_SIGNING_SECRET),
                "bot_token_configured": bool(env_settings.SLACK_BOT_TOKEN),
                "signing_secret_configured": bool(env_settings.SLACK_SIGNING_SECRET),
                "app_token_configured": bool(env_settings.SLACK_APP_TOKEN),
                "setup_endpoint": "/api/v1/slack/setup",
            },
            "whatsapp": {
                "name": "WhatsApp",
                "enabled": env_settings.whatsapp_enabled,
                "configured": env_settings.whatsapp_enabled,
                "api_token_configured": bool(env_settings.WHATSAPP_API_TOKEN),
                "phone_number_id_configured": bool(env_settings.WHATSAPP_PHONE_NUMBER_ID),
                "business_account_configured": bool(env_settings.WHATSAPP_BUSINESS_ACCOUNT_ID),
                "setup_endpoint": "/api/v1/whatsapp/setup",
            },
        },
        "setup_instructions": {
            "step1": "Set PUBLIC_DOMAIN environment variable to your public URL",
            "step2": "Configure bot tokens for platforms you want to enable",
            "step3": "Call each platform's setup endpoint to configure webhooks",
            "step4": "Verify status using the config endpoints",
        }
    }


@router.get(
    "/category/features",
    response_model=Dict[str, Any],
    summary="Feature flags",
    description="Get all feature flags and their status"
)
async def get_feature_flags(
    service: ConfigService = Depends(get_config_service)
):
    """Get all feature flags and their status"""
    try:
        # Get from database
        feature_configs = await service.get_by_category(ConfigCategory.FEATURES)
        
        features = {}
        for config in feature_configs:
            features[config.key] = {
                "value": config.get_value(),
                "description": config.description,
                "is_editable": config.is_editable,
                "source": "database"
            }
        
        # Add environment-based features
        features["registration"] = {
            "value": env_settings.ENABLE_REGISTRATION,
            "description": "Allow new user registration",
            "source": "environment"
        }
        features["rate_limiting"] = {
            "value": env_settings.RATE_LIMIT_ENABLED,
            "description": "Enable API rate limiting",
            "source": "environment"
        }
        features["ollama"] = {
            "value": env_settings.ENABLE_OLLAMA,
            "description": "Enable Ollama local LLM integration",
            "source": "environment"
        }
        
        return {
            "success": True,
            "features": features,
            "total_enabled": sum(1 for f in features.values() if f.get("value", False) is True)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving feature flags: {str(e)}"
        )
