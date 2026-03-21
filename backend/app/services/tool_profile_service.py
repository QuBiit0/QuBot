"""
Tool Profiles - Control granular de qué tools puede usar cada agente.

Profiles predefinidos:
- minimal: Solo session_status
- coding: filesystem, runtime, sessions, memory
- messaging: Canales de comunicación
- full: Sin restricciones

También soporta provider-specific configs.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


class ToolProfile(str, Enum):
    """Tool profile types."""

    MINIMAL = "minimal"
    CODING = "coding"
    MESSAGING = "messaging"
    FULL = "full"


@dataclass
class ToolPolicy:
    """Policy for a single tool or group."""

    allowed: bool = True
    requires_approval: bool = False
    max_calls_per_session: int | None = None


@dataclass
class ToolProfileConfig:
    """Complete tool profile configuration."""

    profile: ToolProfile
    allow_list: list[str] = field(default_factory=list)
    deny_list: list[str] = field(default_factory=list)
    by_provider: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_model: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Tool-specific policies
    tool_policies: dict[str, ToolPolicy] = field(default_factory=dict)

    # Group mappings
    tool_groups: dict[str, list[str]] = field(
        default_factory=lambda: {
            "runtime": ["exec", "bash", "process"],
            "fs": ["filesystem", "read", "write"],
            "sessions": ["sessions", "sessions_list", "sessions_history"],
            "memory": ["agent_memory", "memory_search"],
            "web": ["web_search", "web_fetch", "web_browser"],
            "ui": ["browser_automation", "canvas"],
            "automation": ["scheduler", "cron"],
            "messaging": ["channel_manager", "email", "notification"],
            "nodes": ["nodes", "imessage"],
            "openclaw": [],  # All built-in tools
        }
    )


# Predefined profiles
PROFILE_DEFINITIONS: dict[ToolProfile, list[str]] = {
    ToolProfile.MINIMAL: [
        "session_status",
    ],
    ToolProfile.CODING: [
        "group:fs",
        "group:runtime",
        "group:sessions",
        "group:memory",
        "code_executor",
        "document_reader",
        "docs_search",
    ],
    ToolProfile.MESSAGING: [
        "group:messaging",
        "sessions_list",
        "sessions_history",
        "sessions_send",
        "session_status",
    ],
    ToolProfile.FULL: [
        "*",  # All tools
    ],
}


class ToolProfileService:
    """
    Service for managing tool profiles and permissions.

    Allows granular control over which tools each agent can use,
    with support for profiles, allow/deny lists, and provider-specific configs.
    """

    def __init__(self):
        self._profiles: dict[UUID, ToolProfileConfig] = {}

    def get_profile_config(
        self,
        agent_id: UUID,
        provider: str | None = None,
        model: str | None = None,
    ) -> ToolProfileConfig:
        """Get effective tool config for an agent."""
        if agent_id not in self._profiles:
            self._profiles[agent_id] = ToolProfileConfig(profile=ToolProfile.FULL)

        config = self._profiles[agent_id]

        effective_config = ToolProfileConfig(
            profile=config.profile,
            allow_list=config.allow_list.copy(),
            deny_list=config.deny_list.copy(),
            by_provider=config.by_provider.copy(),
            by_model=config.by_model.copy(),
            tool_policies=config.tool_policies.copy(),
        )

        # Apply provider-specific overrides
        if provider and provider in config.by_provider:
            provider_config = config.by_provider[provider]
            self._merge_config(effective_config, provider_config)

        # Apply model-specific overrides
        if model and model in config.by_model:
            model_config = config.by_model[model]
            self._merge_config(effective_config, model_config)

        return effective_config

    def _merge_config(self, target: ToolProfileConfig, source: dict[str, Any]) -> None:
        """Merge source config into target."""
        if "allow" in source:
            target.allow_list.extend(source["allow"])
        if "deny" in source:
            target.deny_list.extend(source["deny"])
        if "profile" in source:
            target.profile = ToolProfile(source["profile"])

    def set_profile(self, agent_id: UUID, profile: ToolProfile) -> None:
        """Set a predefined profile for an agent."""
        if agent_id not in self._profiles:
            self._profiles[agent_id] = ToolProfileConfig(profile=profile)
        else:
            self._profiles[agent_id].profile = profile

        # Apply profile allow list
        profile_tools = PROFILE_DEFINITIONS.get(profile, [])
        self._profiles[agent_id].allow_list = profile_tools.copy()

    def add_allow(self, agent_id: UUID, *tools: str) -> None:
        """Add tools to agent's allow list."""
        if agent_id not in self._profiles:
            self._profiles[agent_id] = ToolProfileConfig(profile=ToolProfile.FULL)

        self._profiles[agent_id].allow_list.extend(tools)

    def add_deny(self, agent_id: UUID, *tools: str) -> None:
        """Add tools to agent's deny list."""
        if agent_id not in self._profiles:
            self._profiles[agent_id] = ToolProfileConfig(profile=ToolProfile.FULL)

        self._profiles[agent_id].deny_list.extend(tools)

    def set_provider_policy(
        self, agent_id: UUID, provider: str, config: dict[str, Any]
    ) -> None:
        """Set tool policy for a specific provider."""
        if agent_id not in self._profiles:
            self._profiles[agent_id] = ToolProfileConfig(profile=ToolProfile.FULL)

        self._profiles[agent_id].by_provider[provider] = config

    def set_tool_policy(self, agent_id: UUID, tool: str, policy: ToolPolicy) -> None:
        """Set policy for a specific tool."""
        if agent_id not in self._profiles:
            self._profiles[agent_id] = ToolProfileConfig(profile=ToolProfile.FULL)

        self._profiles[agent_id].tool_policies[tool] = policy

    def is_tool_allowed(
        self,
        agent_id: UUID,
        tool_name: str,
        provider: str | None = None,
        model: str | None = None,
    ) -> bool:
        """Check if a tool is allowed for an agent."""
        config = self.get_profile_config(agent_id, provider, model)

        # Check specific tool policy
        if tool_name in config.tool_policies:
            return config.tool_policies[tool_name].allowed

        # Check deny list first
        if self._matches_any(tool_name, config.deny_list, config):
            return False

        # Check allow list
        if self._matches_any(tool_name, config.allow_list, config):
            return True

        # Default: allow if profile is full, deny otherwise
        return config.profile == ToolProfile.FULL

    def _matches_any(
        self, tool_name: str, patterns: list[str], config: ToolProfileConfig
    ) -> bool:
        """Check if tool matches any pattern in list."""
        for pattern in patterns:
            if pattern == "*":
                return True

            if pattern.startswith("group:"):
                group_name = pattern[6:]
                group_tools = config.tool_groups.get(group_name, [])
                if tool_name in group_tools:
                    return True
                continue

            if pattern.lower() == tool_name.lower():
                return True

            # Wildcard matching
            if "*" in pattern:
                import fnmatch

                if fnmatch.fnmatch(tool_name.lower(), pattern.lower()):
                    return True

        return False

    def get_allowed_tools(
        self,
        agent_id: UUID,
        all_tools: list[str],
        provider: str | None = None,
        model: str | None = None,
    ) -> list[str]:
        """Get list of allowed tools for an agent."""
        config = self.get_profile_config(agent_id, provider, model)

        if config.profile == ToolProfile.FULL and not config.deny_list:
            return all_tools

        allowed = []
        for tool in all_tools:
            if self.is_tool_allowed(agent_id, tool, provider, model):
                allowed.append(tool)

        return allowed

    def requires_approval(self, agent_id: UUID, tool_name: str) -> bool:
        """Check if tool requires approval before execution."""
        if agent_id not in self._profiles:
            return False

        policy = self._profiles[agent_id].tool_policies.get(tool_name)
        return policy.requires_approval if policy else False

    def get_stats(self, agent_id: UUID) -> dict[str, Any]:
        """Get profile stats for an agent."""
        if agent_id not in self._profiles:
            return {"profile": "full", "configured": False}

        config = self._profiles[agent_id]
        return {
            "profile": config.profile.value,
            "configured": True,
            "allow_count": len(config.allow_list),
            "deny_count": len(config.deny_list),
            "providers": list(config.by_provider.keys()),
            "tool_policies": {
                tool: {"allowed": p.allowed, "approval": p.requires_approval}
                for tool, p in config.tool_policies.items()
            },
        }

    def reset(self, agent_id: UUID) -> None:
        """Reset profile for an agent."""
        if agent_id in self._profiles:
            del self._profiles[agent_id]


_tool_profile_service: ToolProfileService | None = None


def get_tool_profile_service() -> ToolProfileService:
    """Get or create the global tool profile service instance."""
    global _tool_profile_service
    if _tool_profile_service is None:
        _tool_profile_service = ToolProfileService()
    return _tool_profile_service
