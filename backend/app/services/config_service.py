"""
Configuration Service - Complete CRUD for system configuration
Supports both environment variables and database-stored dynamic config

Features:
- Automatic caching for performance
- Encryption for secrets
- Comprehensive validation
- Audit logging
- Workspace/tenant support
"""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings as env_settings
from ..models.config import (
    ConfigCategory,
    ConfigHistory,
    ConfigPreset,
    ConfigValueType,
    SystemConfig,
)

# Simple in-memory cache with TTL
_config_cache: dict[str, dict[str, Any]] = {}
_cache_timestamps: dict[str, datetime] = {}
CACHE_TTL_SECONDS = 60  # Cache TTL


class ConfigError(Exception):
    """Configuration error"""

    pass


class ConfigValidationError(ConfigError):
    """Configuration validation error"""

    pass


class ConfigNotFoundError(ConfigError):
    """Configuration not found error"""

    pass


class ConfigService:
    """Service for managing system configuration with caching and validation"""

    # Default configurations that are created on first run
    DEFAULT_CONFIGS = [
        # General
        {
            "key": "app_name",
            "value": "Qubot",
            "type": "string",
            "category": "general",
            "description": "Application name displayed in UI",
        },
        {
            "key": "app_description",
            "value": "AI-Powered Multi-Agent Platform",
            "type": "string",
            "category": "general",
            "description": "Application description",
        },
        {
            "key": "maintenance_mode",
            "value": False,
            "type": "boolean",
            "category": "general",
            "description": "Enable maintenance mode",
        },
        {
            "key": "maintenance_message",
            "value": "System is under maintenance. Please try again later.",
            "type": "string",
            "category": "general",
            "description": "Maintenance mode message",
        },
        # Security
        {
            "key": "max_login_attempts",
            "value": 5,
            "type": "integer",
            "category": "security",
            "description": "Maximum failed login attempts before lockout",
            "min": 1,
            "max": 10,
        },
        {
            "key": "lockout_duration_minutes",
            "value": 30,
            "type": "integer",
            "category": "security",
            "description": "Account lockout duration in minutes",
            "min": 5,
            "max": 1440,
        },
        {
            "key": "require_email_verification",
            "value": False,
            "type": "boolean",
            "category": "security",
            "description": "Require email verification for new accounts",
        },
        {
            "key": "session_timeout_hours",
            "value": 24,
            "type": "integer",
            "category": "security",
            "description": "User session timeout in hours",
            "min": 1,
            "max": 720,
        },
        {
            "key": "password_min_length",
            "value": 8,
            "type": "integer",
            "category": "security",
            "description": "Minimum password length",
            "min": 6,
            "max": 128,
        },
        {
            "key": "password_require_special",
            "value": False,
            "type": "boolean",
            "category": "security",
            "description": "Require special characters in password",
        },
        {
            "key": "two_factor_auth_enabled",
            "value": False,
            "type": "boolean",
            "category": "security",
            "description": "Enable two-factor authentication option",
        },
        {
            "key": "allowed_email_domains",
            "value": [],
            "type": "json",
            "category": "security",
            "description": "List of allowed email domains (empty = all)",
        },
        # LLM
        {
            "key": "llm_request_timeout",
            "value": 60,
            "type": "integer",
            "category": "llm",
            "description": "LLM request timeout in seconds",
            "min": 10,
            "max": 300,
        },
        {
            "key": "llm_retry_attempts",
            "value": 3,
            "type": "integer",
            "category": "llm",
            "description": "Number of retry attempts for LLM calls",
            "min": 0,
            "max": 10,
        },
        {
            "key": "llm_enable_caching",
            "value": True,
            "type": "boolean",
            "category": "llm",
            "description": "Enable LLM response caching",
        },
        {
            "key": "llm_cache_ttl_minutes",
            "value": 60,
            "type": "integer",
            "category": "llm",
            "description": "LLM cache TTL in minutes",
            "min": 1,
            "max": 1440,
        },
        {
            "key": "llm_cost_tracking_enabled",
            "value": True,
            "type": "boolean",
            "category": "llm",
            "description": "Enable cost tracking for LLM calls",
        },
        {
            "key": "llm_fallback_enabled",
            "value": True,
            "type": "boolean",
            "category": "llm",
            "description": "Enable fallback to alternative providers",
        },
        {
            "key": "llm_max_tokens_limit",
            "value": 4000,
            "type": "integer",
            "category": "llm",
            "description": "Maximum tokens allowed per request",
            "min": 100,
            "max": 16000,
        },
        {
            "key": "llm_streaming_enabled",
            "value": True,
            "type": "boolean",
            "category": "llm",
            "description": "Enable streaming responses",
        },
        {
            "key": "llm_default_system_prompt",
            "value": "You are a helpful AI assistant.",
            "type": "string",
            "category": "llm",
            "description": "Default system prompt for LLM calls",
        },
        # Messaging
        {
            "key": "telegram_auto_setup",
            "value": True,
            "type": "boolean",
            "category": "messaging",
            "description": "Auto-setup Telegram webhook on startup",
        },
        {
            "key": "telegram_allowed_users",
            "value": [],
            "type": "json",
            "category": "messaging",
            "description": "List of allowed Telegram user IDs (empty = all)",
        },
        {
            "key": "telegram_admin_users",
            "value": [],
            "type": "json",
            "category": "messaging",
            "description": "List of Telegram admin user IDs",
        },
        {
            "key": "discord_auto_setup",
            "value": True,
            "type": "boolean",
            "category": "messaging",
            "description": "Auto-setup Discord on startup",
        },
        {
            "key": "discord_allowed_guilds",
            "value": [],
            "type": "json",
            "category": "messaging",
            "description": "List of allowed Discord guild IDs",
        },
        {
            "key": "slack_auto_setup",
            "value": True,
            "type": "boolean",
            "category": "messaging",
            "description": "Auto-setup Slack on startup",
        },
        {
            "key": "slack_allowed_workspaces",
            "value": [],
            "type": "json",
            "category": "messaging",
            "description": "List of allowed Slack workspace IDs",
        },
        {
            "key": "whatsapp_auto_setup",
            "value": False,
            "type": "boolean",
            "category": "messaging",
            "description": "Auto-setup WhatsApp on startup",
        },
        {
            "key": "messaging_rate_limit_per_minute",
            "value": 30,
            "type": "integer",
            "category": "messaging",
            "description": "Rate limit per user per minute",
            "min": 1,
            "max": 1000,
        },
        {
            "key": "messaging_welcome_message",
            "value": "Welcome! I'm Qubot, your AI assistant. How can I help you today?",
            "type": "string",
            "category": "messaging",
            "description": "Welcome message for new users",
        },
        # Features
        {
            "key": "enable_user_registration",
            "value": True,
            "type": "boolean",
            "category": "features",
            "description": "Allow new user registration",
        },
        {
            "key": "enable_public_agent_gallery",
            "value": True,
            "type": "boolean",
            "category": "features",
            "description": "Enable public agent gallery",
        },
        {
            "key": "enable_agent_sharing",
            "value": True,
            "type": "boolean",
            "category": "features",
            "description": "Allow sharing agents between users",
        },
        {
            "key": "enable_marketplace",
            "value": False,
            "type": "boolean",
            "category": "features",
            "description": "Enable agent marketplace",
        },
        {
            "key": "enable_analytics",
            "value": True,
            "type": "boolean",
            "category": "features",
            "description": "Enable usage analytics",
        },
        {
            "key": "enable_notifications",
            "value": True,
            "type": "boolean",
            "category": "features",
            "description": "Enable notification system",
        },
        {
            "key": "max_agents_per_user",
            "value": 10,
            "type": "integer",
            "category": "features",
            "description": "Maximum agents per user",
            "min": 1,
            "max": 100,
        },
        {
            "key": "max_tasks_per_user_per_day",
            "value": 100,
            "type": "integer",
            "category": "features",
            "description": "Maximum tasks per user per day",
            "min": 1,
            "max": 10000,
        },
        {
            "key": "enable_guest_mode",
            "value": False,
            "type": "boolean",
            "category": "features",
            "description": "Allow guest access without registration",
        },
        {
            "key": "enable_api_key_auth",
            "value": True,
            "type": "boolean",
            "category": "features",
            "description": "Allow API key authentication",
        },
        # UI
        {
            "key": "ui_theme",
            "value": "dark",
            "type": "string",
            "category": "ui",
            "description": "Default UI theme (dark/light/auto)",
            "allowed_values": ["dark", "light", "auto"],
        },
        {
            "key": "ui_language",
            "value": "es",
            "type": "string",
            "category": "ui",
            "description": "Default UI language (es/en/pt/fr/de)",
            "allowed_values": ["es", "en", "pt", "fr", "de"],
        },
        {
            "key": "ui_show_tour",
            "value": True,
            "type": "boolean",
            "category": "ui",
            "description": "Show onboarding tour for new users",
        },
        {
            "key": "ui_items_per_page",
            "value": 20,
            "type": "integer",
            "category": "ui",
            "description": "Default items per page",
            "min": 5,
            "max": 100,
        },
        {
            "key": "ui_realtime_updates",
            "value": True,
            "type": "boolean",
            "category": "ui",
            "description": "Enable real-time UI updates",
        },
        {
            "key": "ui_agent_animations",
            "value": True,
            "type": "boolean",
            "category": "ui",
            "description": "Enable agent office animations",
        },
        {
            "key": "ui_auto_save_interval",
            "value": 30,
            "type": "integer",
            "category": "ui",
            "description": "Auto-save interval in seconds",
            "min": 5,
            "max": 300,
        },
        {
            "key": "ui_compact_mode",
            "value": False,
            "type": "boolean",
            "category": "ui",
            "description": "Enable compact UI mode",
        },
        {
            "key": "ui_show_debug_info",
            "value": False,
            "type": "boolean",
            "category": "ui",
            "description": "Show debug information in UI",
        },
        # Task Execution
        {
            "key": "task_default_priority",
            "value": "MEDIUM",
            "type": "string",
            "category": "advanced",
            "description": "Default task priority",
            "allowed_values": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        },
        {
            "key": "task_max_retries",
            "value": 3,
            "type": "integer",
            "category": "advanced",
            "description": "Maximum task retries",
            "min": 0,
            "max": 10,
        },
        {
            "key": "task_retry_delay_seconds",
            "value": 5,
            "type": "integer",
            "category": "advanced",
            "description": "Delay between retries",
            "min": 1,
            "max": 300,
        },
        {
            "key": "worker_max_concurrent_tasks",
            "value": 5,
            "type": "integer",
            "category": "advanced",
            "description": "Max concurrent tasks per worker",
            "min": 1,
            "max": 50,
        },
        {
            "key": "cleanup_completed_tasks_days",
            "value": 30,
            "type": "integer",
            "category": "advanced",
            "description": "Days to keep completed tasks",
            "min": 1,
            "max": 365,
        },
        {
            "key": "log_retention_days",
            "value": 90,
            "type": "integer",
            "category": "advanced",
            "description": "Days to keep logs",
            "min": 7,
            "max": 365,
        },
        {
            "key": "enable_detailed_logging",
            "value": False,
            "type": "boolean",
            "category": "advanced",
            "description": "Enable detailed debug logging",
        },
        {
            "key": "performance_profiling_enabled",
            "value": False,
            "type": "boolean",
            "category": "advanced",
            "description": "Enable performance profiling",
        },
    ]

    def __init__(self, session: AsyncSession, workspace_id: str | None = None):
        self.session = session
        self.workspace_id = workspace_id

    def _get_cache_key(self, key: str) -> str:
        """Generate cache key including workspace"""
        if self.workspace_id:
            return f"{self.workspace_id}:{key}"
        return f"global:{key}"

    def _get_from_cache(self, key: str) -> Any | None:
        """Get value from cache if not expired"""
        cache_key = self._get_cache_key(key)
        if cache_key in _config_cache:
            timestamp = _cache_timestamps.get(cache_key)
            if (
                timestamp
                and (datetime.utcnow() - timestamp).seconds < CACHE_TTL_SECONDS
            ):
                return _config_cache[cache_key]["value"]
            else:
                # Expired, remove from cache
                del _config_cache[cache_key]
                del _cache_timestamps[cache_key]
        return None

    def _set_in_cache(self, key: str, value: Any):
        """Set value in cache"""
        cache_key = self._get_cache_key(key)
        _config_cache[cache_key] = {"value": value}
        _cache_timestamps[cache_key] = datetime.utcnow()

    def _invalidate_cache(self, key: str):
        """Invalidate cache for a key"""
        cache_key = self._get_cache_key(key)
        if cache_key in _config_cache:
            del _config_cache[cache_key]
            del _cache_timestamps[cache_key]

    def _invalidate_all_cache(self):
        """Invalidate all cache"""
        global _config_cache, _cache_timestamps
        if self.workspace_id:
            # Only invalidate this workspace
            prefix = f"{self.workspace_id}:"
            for key in list(_config_cache.keys()):
                if key.startswith(prefix):
                    del _config_cache[key]
                    del _cache_timestamps[key]
        else:
            # Invalidate global cache
            _config_cache = {}
            _cache_timestamps = {}

    async def initialize_defaults(self) -> dict[str, bool]:
        """Initialize default configurations if they don't exist"""
        results = {}
        for config_data in self.DEFAULT_CONFIGS:
            try:
                existing = await self.get_by_key(config_data["key"])
                if not existing:
                    await self.create(
                        key=config_data["key"],
                        value=config_data["value"],
                        value_type=ConfigValueType(config_data["type"]),
                        category=ConfigCategory(config_data["category"]),
                        description=config_data["description"],
                        is_editable=True,
                        is_secret=False,
                        requires_restart=False,
                        skip_cache=True,
                    )
                    results[config_data["key"]] = True
                else:
                    results[config_data["key"]] = False
            except Exception:
                results[config_data["key"]] = False

        await self.session.commit()
        return results

    # CRUD Operations for SystemConfig

    async def get_by_key(self, key: str, use_cache: bool = True) -> SystemConfig | None:
        """Get configuration by key with optional caching"""
        # Try cache first
        if use_cache:
            cached = self._get_from_cache(key)
            if cached is not None:
                # Return a mock config object
                config = SystemConfig(key=key)
                config.set_value(cached)
                return config

        # Query database
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()

        if config and use_cache:
            self._set_in_cache(key, config.get_value())

        return config

    async def get_value(
        self, key: str, default: Any = None, use_cache: bool = True
    ) -> Any:
        """Get configuration value with default fallback and caching"""
        # Try cache first
        if use_cache:
            cached = self._get_from_cache(key)
            if cached is not None:
                return cached

        # Try database
        config = await self.get_by_key(key, use_cache=False)
        if config:
            value = config.get_value()
            if use_cache:
                self._set_in_cache(key, value)
            return value

        # Try environment variables
        env_value = getattr(env_settings, key.upper(), None)
        if env_value is not None and env_value != "":
            if use_cache:
                self._set_in_cache(key, env_value)
            return env_value

        return default

    async def get_value_typed(
        self, key: str, value_type: type, default: Any = None, use_cache: bool = True
    ) -> Any:
        """Get configuration value with type conversion"""
        value = await self.get_value(key, default, use_cache)
        if value is None:
            return default

        try:
            if value_type is bool and isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on", "enabled")
            return value_type(value)
        except (ValueError, TypeError):
            return default

    async def get_by_category(self, category: ConfigCategory) -> list[SystemConfig]:
        """Get all configurations in a category"""
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.category == category)
        )
        return result.scalars().all()

    async def get_all(
        self, include_secrets: bool = False, category: ConfigCategory | None = None
    ) -> list[SystemConfig]:
        """Get all configurations with optional filtering"""
        query = select(SystemConfig)

        if category:
            query = query.where(SystemConfig.category == category)

        result = await self.session.execute(query)
        configs = result.scalars().all()

        if not include_secrets:
            for config in configs:
                if config.is_secret:
                    config.value_string = "***MASKED***"

        return configs

    async def create(
        self,
        key: str,
        value: Any,
        value_type: ConfigValueType,
        category: ConfigCategory,
        description: str = "",
        is_editable: bool = True,
        is_secret: bool = False,
        requires_restart: bool = False,
        updated_by: str | None = None,
        skip_cache: bool = False,
    ) -> SystemConfig:
        """Create a new configuration"""
        # Validate key format
        if not self._validate_key_format(key):
            raise ConfigValidationError(
                f"Invalid key format: {key}. Use lowercase with underscores."
            )

        config = SystemConfig(
            key=key,
            category=category,
            value_type=value_type,
            description=description,
            is_editable=is_editable,
            is_secret=is_secret,
            requires_restart=requires_restart,
            updated_by=updated_by,
        )
        config.set_value(value, value_type)

        self.session.add(config)

        try:
            await self.session.commit()
            await self.session.refresh(config)
        except IntegrityError:
            await self.session.rollback()
            raise ConfigError(f"Configuration key '{key}' already exists")

        # Update cache
        if not skip_cache:
            self._set_in_cache(key, config.get_value())

        # Log the change
        await self._log_history(
            key, category.value, None, str(value), updated_by, "Created"
        )

        return config

    async def update(
        self,
        key: str,
        value: Any,
        updated_by: str | None = None,
        change_reason: str | None = None,
        skip_validation: bool = False,
    ) -> SystemConfig:
        """Update a configuration value"""
        config = await self.get_by_key(key, use_cache=False)
        if not config:
            raise ConfigNotFoundError(f"Configuration key '{key}' not found")

        if not config.is_editable:
            raise ConfigError(f"Configuration '{key}' is not editable")

        # Validate
        if not skip_validation:
            is_valid, error_msg = await self.validate_config(key, value)
            if not is_valid:
                raise ConfigValidationError(error_msg)

        old_value = config.get_value()
        config.set_value(value)
        config.updated_at = datetime.utcnow()
        config.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(config)

        # Invalidate cache
        self._invalidate_cache(key)

        # Log the change
        await self._log_history(
            key,
            config.category.value,
            str(old_value),
            str(value),
            updated_by,
            change_reason,
        )

        return config

    async def delete(self, key: str) -> bool:
        """Delete a configuration"""
        config = await self.get_by_key(key, use_cache=False)
        if not config:
            raise ConfigNotFoundError(f"Configuration key '{key}' not found")

        if not config.is_editable:
            raise ConfigError(f"Configuration '{key}' cannot be deleted")

        await self.session.delete(config)
        await self.session.commit()

        # Invalidate cache
        self._invalidate_cache(key)

        return True

    # Bulk Operations

    async def bulk_update(
        self,
        updates: dict[str, Any],
        updated_by: str | None = None,
        change_reason: str | None = None,
    ) -> dict[str, bool | str]:
        """Update multiple configurations at once"""
        results = {}
        for key, value in updates.items():
            try:
                await self.update(key, value, updated_by, change_reason)
                results[key] = True
            except ConfigError as e:
                results[key] = str(e)
            except Exception as e:
                results[key] = f"Unexpected error: {str(e)}"
        return results

    # Import/Export

    async def export_config(
        self, category: ConfigCategory | None = None, include_secrets: bool = False
    ) -> dict[str, Any]:
        """Export configuration to JSON"""
        if category:
            configs = await self.get_by_category(category)
        else:
            configs = await self.get_all(include_secrets=include_secrets)

        return {
            "exported_at": datetime.utcnow().isoformat(),
            "category": category.value if category else "all",
            "workspace_id": self.workspace_id,
            "config": {
                config.key: {
                    "value": config.get_value()
                    if not config.is_secret
                    else "***MASKED***",
                    "type": config.value_type.value,
                    "category": config.category.value,
                    "description": config.description,
                }
                for config in configs
            },
        }

    async def import_config(
        self,
        data: dict[str, Any],
        updated_by: str | None = None,
        overwrite_existing: bool = True,
        skip_validation: bool = False,
    ) -> dict[str, bool | str]:
        """Import configuration from JSON"""
        results = {}
        config_data = data.get("config", data)  # Support both formats

        for key, config_info in config_data.items():
            try:
                if isinstance(config_info, dict):
                    value = config_info.get("value")
                    value_type = ConfigValueType(config_info.get("type", "string"))
                    category = ConfigCategory(config_info.get("category", "general"))
                    description = config_info.get("description", "")
                else:
                    # Simple key-value format
                    value = config_info
                    value_type = ConfigValueType.STRING
                    category = ConfigCategory.GENERAL
                    description = ""

                existing = await self.get_by_key(key, use_cache=False)

                if existing:
                    if not overwrite_existing:
                        results[key] = "Skipped (already exists)"
                        continue
                    if not existing.is_editable:
                        results[key] = "Not editable"
                        continue
                    await self.update(key, value, updated_by, "Import", skip_validation)
                else:
                    await self.create(
                        key=key,
                        value=value,
                        value_type=value_type,
                        category=category,
                        description=description,
                        updated_by=updated_by,
                    )
                results[key] = True
            except Exception as e:
                results[key] = str(e)

        return results

    # Preset Management

    async def create_preset(
        self,
        name: str,
        description: str,
        values: dict[str, Any],
        category: str = "custom",
    ) -> ConfigPreset:
        """Create a configuration preset"""
        preset = ConfigPreset(
            name=name, description=description, values=values, category=category
        )
        self.session.add(preset)
        await self.session.commit()
        await self.session.refresh(preset)
        return preset

    async def apply_preset(
        self, preset_id: UUID, updated_by: str | None = None
    ) -> bool:
        """Apply a preset configuration"""
        result = await self.session.execute(
            select(ConfigPreset).where(ConfigPreset.id == preset_id)
        )
        preset = result.scalar_one_or_none()
        if not preset:
            raise ConfigNotFoundError(f"Preset '{preset_id}' not found")

        await self.bulk_update(
            preset.values, updated_by, f"Applied preset: {preset.name}"
        )

        # Update active status
        preset.is_active = True
        preset.updated_at = datetime.utcnow()
        await self.session.commit()

        return True

    # History

    async def _log_history(
        self,
        config_key: str,
        category: str,
        old_value: str | None,
        new_value: str,
        changed_by: str | None,
        change_reason: str | None,
    ) -> None:
        """Log configuration change"""
        # Truncate values if too long
        max_length = 1000
        old_value = (
            (old_value[:max_length] + "...")
            if old_value and len(old_value) > max_length
            else old_value
        )
        new_value = (
            (new_value[:max_length] + "...")
            if len(new_value) > max_length
            else new_value
        )

        history = ConfigHistory(
            config_key=config_key,
            category=category,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            change_reason=change_reason,
        )
        self.session.add(history)
        await self.session.commit()

    async def get_history(
        self,
        key: str | None = None,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ConfigHistory]:
        """Get configuration change history"""
        query = select(ConfigHistory).order_by(desc(ConfigHistory.changed_at))

        if key:
            query = query.where(ConfigHistory.config_key == key)
        if category:
            query = query.where(ConfigHistory.category == category)

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    # Validation

    def _validate_key_format(self, key: str) -> bool:
        """Validate configuration key format"""
        import re

        # Allow lowercase letters, numbers, and underscores
        # Must start with a letter
        pattern = r"^[a-z][a-z0-9_]*$"
        return bool(re.match(pattern, key))

    async def validate_config(self, key: str, value: Any) -> tuple[bool, str | None]:
        """Validate a configuration value"""
        # Find default config for validation rules
        default_config = None
        for dc in self.DEFAULT_CONFIGS:
            if dc["key"] == key:
                default_config = dc
                break

        if default_config:
            # Type validation
            expected_type = default_config.get("type", "string")
            try:
                if expected_type == "integer":
                    int(value)
                elif expected_type == "float":
                    float(value)
                elif expected_type == "boolean":
                    if isinstance(value, str):
                        if value.lower() not in ("true", "false", "1", "0", "yes", "no"):
                            raise ValueError(f"Invalid boolean value: {value}")
                elif expected_type == "json":
                    if isinstance(value, str):
                        json.loads(value)
            except (ValueError, TypeError):
                return False, f"Invalid type for '{key}'. Expected {expected_type}"

            # Range validation
            if expected_type in ("integer", "float"):
                if "min" in default_config and value < default_config["min"]:
                    return (
                        False,
                        f"Value for '{key}' must be >= {default_config['min']}",
                    )
                if "max" in default_config and value > default_config["max"]:
                    return (
                        False,
                        f"Value for '{key}' must be <= {default_config['max']}",
                    )

            # Allowed values validation
            if "allowed_values" in default_config:
                if value not in default_config["allowed_values"]:
                    return (
                        False,
                        f"Value for '{key}' must be one of: {', '.join(default_config['allowed_values'])}",
                    )

        # Custom validations
        if key == "password_min_length" and int(value) < 6:
            return False, "Password minimum length must be at least 6"

        if key == "llm_max_tokens_limit" and int(value) > 32000:
            return False, "Max tokens limit cannot exceed 32000"

        if key == "ui_language" and value not in ["es", "en", "pt", "fr", "de"]:
            return False, "Language must be one of: es, en, pt, fr, de"

        return True, None

    # Statistics

    async def get_statistics(self) -> dict[str, Any]:
        """Get configuration statistics"""
        total = await self.session.execute(select(func.count(SystemConfig.id)))
        by_category = {}

        for category in ConfigCategory:
            count = await self.session.execute(
                select(func.count(SystemConfig.id)).where(
                    SystemConfig.category == category
                )
            )
            by_category[category.value] = count.scalar()

        editable = await self.session.execute(
            select(func.count(SystemConfig.id)).where(SystemConfig.is_editable == True)
        )

        secrets = await self.session.execute(
            select(func.count(SystemConfig.id)).where(SystemConfig.is_secret == True)
        )

        return {
            "total_configs": total.scalar(),
            "by_category": by_category,
            "editable": editable.scalar(),
            "secrets": secrets.scalar(),
            "cache_entries": len(_config_cache),
        }
