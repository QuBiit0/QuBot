"""
Integrations API
----------------
Two concerns in one file:
  1. Tool configuration  — GET/PUT per-tool settings, persisted in DB, reloaded live
  2. MCP server management — add/test/sync/call external MCP servers
"""

from __future__ import annotations

import os
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...core.mcp_client import (
    call_tool_sse,
    call_tool_stdio,
    list_tools_sse,
    list_tools_stdio,
)
from ...core.security import get_current_user
from ...core.tools import get_tool_registry
from ...database import get_session
from ...models.integration_config import IntegrationConfig
from ...models.mcp_server import MCPServer
from ...models.user import User

router = APIRouter(prefix="/integrations", tags=["integrations"])

# ============================================================================
# TOOL CONFIG SCHEMAS — one entry per BaseTool.name
# ============================================================================
# Each entry: label, description, icon, category, fields[]
# Each field: name, label, type (text|password|number|boolean|select),
#             default, description?, env_var?, required?, options? (for select)

TOOL_CONFIG_SCHEMAS: dict = {
    "web_browser": {
        "label": "Web Browser",
        "description": "Fetch and parse web pages using httpx + BeautifulSoup",
        "icon": "🌐",
        "category": "web",
        "fields": [
            {
                "name": "timeout",
                "label": "Timeout (seconds)",
                "type": "number",
                "default": 30,
            },
            {
                "name": "max_length",
                "label": "Max Content Length (chars)",
                "type": "number",
                "default": 10000,
            },
            {
                "name": "user_agent",
                "label": "Custom User Agent",
                "type": "text",
                "default": "",
            },
        ],
    },
    "web_search": {
        "label": "Web Search",
        "description": "Search the web using DuckDuckGo — no API key needed",
        "icon": "🔍",
        "category": "web",
        "fields": [
            {
                "name": "region",
                "label": "Region",
                "type": "text",
                "default": "wt-wt",
                "description": "e.g. wt-wt (global), us-en, es-es",
            },
            {
                "name": "max_results",
                "label": "Default Max Results",
                "type": "number",
                "default": 10,
            },
            {
                "name": "safe_search",
                "label": "Safe Search",
                "type": "select",
                "default": "moderate",
                "options": ["on", "moderate", "off"],
            },
        ],
    },
    "browser_automation": {
        "label": "Browser Automation",
        "description": "Automate Chromium via Playwright for JS-heavy sites",
        "icon": "🤖",
        "category": "web",
        "fields": [
            {
                "name": "headless",
                "label": "Headless Mode",
                "type": "boolean",
                "default": True,
            },
            {
                "name": "timeout",
                "label": "Default Timeout (ms)",
                "type": "number",
                "default": 30000,
            },
        ],
    },
    "http_api": {
        "label": "HTTP API Client",
        "description": "Make HTTP requests to any external REST API",
        "icon": "📡",
        "category": "web",
        "fields": [
            {
                "name": "timeout",
                "label": "Timeout (seconds)",
                "type": "number",
                "default": 30,
            },
        ],
    },
    "system_shell": {
        "label": "System Shell",
        "description": "Execute shell commands on the host system",
        "icon": "💻",
        "category": "system",
        "fields": [
            {
                "name": "timeout",
                "label": "Timeout (seconds)",
                "type": "number",
                "default": 30,
            },
            {
                "name": "allowed_commands",
                "label": "Allowed Commands (comma-separated)",
                "type": "text",
                "default": "ls,cat,grep,find,echo",
                "description": "Whitelist of commands agents are allowed to run",
            },
        ],
    },
    "filesystem": {
        "label": "File System",
        "description": "Read, write, and manage files in a sandboxed directory",
        "icon": "📁",
        "category": "file",
        "fields": [
            {
                "name": "workspace_dir",
                "label": "Workspace Directory",
                "type": "text",
                "default": "/workspace/files",
                "description": "Base directory for all file operations",
            },
        ],
    },
    "scheduler": {
        "label": "Task Scheduler",
        "description": "Schedule one-time or recurring tasks",
        "icon": "⏰",
        "category": "misc",
        "fields": [],
    },
    "code_executor": {
        "label": "Code Executor",
        "description": "Execute Python, Bash, and Node.js code in a sandbox",
        "icon": "⚡",
        "category": "code",
        "fields": [
            {
                "name": "default_timeout",
                "label": "Default Timeout (seconds)",
                "type": "number",
                "default": 30,
            },
            {
                "name": "max_timeout",
                "label": "Max Allowed Timeout (seconds)",
                "type": "number",
                "default": 120,
            },
        ],
    },
    "document_reader": {
        "label": "Document Reader",
        "description": "Extract text and tables from PDF, DOCX, XLSX, CSV files",
        "icon": "📄",
        "category": "file",
        "fields": [
            {
                "name": "max_chars",
                "label": "Max Characters to Extract",
                "type": "number",
                "default": 50000,
            },
        ],
    },
    "database_query": {
        "label": "Database Query",
        "description": "Execute read-only SQL queries against PostgreSQL",
        "icon": "🗄️",
        "category": "data",
        "fields": [
            {
                "name": "max_rows",
                "label": "Max Rows",
                "type": "number",
                "default": 1000,
            },
            {
                "name": "database_url",
                "label": "Custom Database URL (optional)",
                "type": "password",
                "default": "",
                "env_var": "DATABASE_URL",
                "description": "Override the default app database. Leave blank to use the app DB.",
            },
        ],
    },
    "agent_memory": {
        "label": "Agent Memory",
        "description": "Persistent semantic memory with cosine-similarity search",
        "icon": "🧠",
        "category": "data",
        "fields": [
            {
                "name": "openai_api_key",
                "label": "OpenAI API Key (for embeddings)",
                "type": "password",
                "default": "",
                "env_var": "OPENAI_API_KEY",
                "description": "Required for semantic search. Without it, falls back to keyword search.",
            },
        ],
    },
    "github": {
        "label": "GitHub",
        "description": "Read/write repos, issues, PRs, search code via GitHub API",
        "icon": "🐙",
        "category": "code",
        "fields": [
            {
                "name": "token",
                "label": "Personal Access Token",
                "type": "password",
                "default": "",
                "env_var": "GITHUB_TOKEN",
                "required": True,
                "description": "Generate at github.com/settings/tokens (needs repo scope)",
            },
            {
                "name": "default_owner",
                "label": "Default Owner / Organization",
                "type": "text",
                "default": "",
            },
        ],
    },
    "email": {
        "label": "Email (SMTP / IMAP)",
        "description": "Send emails via SMTP and read/search via IMAP",
        "icon": "📧",
        "category": "communication",
        "fields": [
            {
                "name": "smtp_host",
                "label": "SMTP Host",
                "type": "text",
                "default": "",
                "env_var": "EMAIL_SMTP_HOST",
                "description": "e.g. smtp.gmail.com",
            },
            {
                "name": "smtp_port",
                "label": "SMTP Port",
                "type": "number",
                "default": 587,
                "env_var": "EMAIL_SMTP_PORT",
            },
            {
                "name": "smtp_user",
                "label": "SMTP Username / From Address",
                "type": "text",
                "default": "",
                "env_var": "EMAIL_SMTP_USER",
            },
            {
                "name": "smtp_password",
                "label": "SMTP Password / App Password",
                "type": "password",
                "default": "",
                "env_var": "EMAIL_SMTP_PASSWORD",
            },
            {
                "name": "imap_host",
                "label": "IMAP Host (for reading email)",
                "type": "text",
                "default": "",
                "env_var": "EMAIL_IMAP_HOST",
                "description": "e.g. imap.gmail.com — leave blank if same as SMTP host",
            },
            {
                "name": "imap_port",
                "label": "IMAP Port",
                "type": "number",
                "default": 993,
                "env_var": "EMAIL_IMAP_PORT",
            },
        ],
    },
    "notification": {
        "label": "Notifications",
        "description": "Push alerts to Slack, Discord, Teams, or custom webhooks",
        "icon": "🔔",
        "category": "communication",
        "fields": [
            {
                "name": "slack_webhook",
                "label": "Slack Incoming Webhook URL",
                "type": "password",
                "default": "",
                "env_var": "SLACK_WEBHOOK_URL",
                "description": "api.slack.com/apps → Your App → Incoming Webhooks",
            },
            {
                "name": "discord_webhook",
                "label": "Discord Webhook URL",
                "type": "password",
                "default": "",
                "env_var": "DISCORD_WEBHOOK_URL",
                "description": "Channel Settings → Integrations → Webhooks",
            },
            {
                "name": "teams_webhook",
                "label": "Microsoft Teams Connector URL",
                "type": "password",
                "default": "",
                "env_var": "TEAMS_WEBHOOK_URL",
            },
        ],
    },
    "docs_search": {
        "label": "Docs Search (Context7)",
        "description": "Real-time library documentation lookup via Context7",
        "icon": "📚",
        "category": "web",
        "fields": [
            {
                "name": "context7_token",
                "label": "Context7 API Token (optional)",
                "type": "password",
                "default": "",
                "env_var": "CONTEXT7_TOKEN",
                "description": "Get a free token at context7.com for higher rate limits",
            },
            {
                "name": "timeout",
                "label": "Timeout (seconds)",
                "type": "number",
                "default": 20,
            },
        ],
    },
    "mcp_installer": {
        "label": "MCP Installer",
        "description": "Autonomous MCP server manager — agents can discover & register MCP servers",
        "icon": "🔧",
        "category": "misc",
        "fields": [],
    },
    "delegate_task": {
        "label": "Delegate Task",
        "description": "Delegate work to sub-agents with specialized skills",
        "icon": "🎯",
        "category": "agent",
        "fields": [
            {
                "name": "max_depth",
                "label": "Max Delegation Depth",
                "type": "number",
                "default": 3,
            },
            {
                "name": "allow_cross_agent",
                "label": "Allow Cross-Agent Delegation",
                "type": "boolean",
                "default": True,
            },
        ],
    },
    "create_agent": {
        "label": "Create Agent",
        "description": "Create new specialized agents dynamically",
        "icon": "🤖",
        "category": "agent",
        "fields": [
            {
                "name": "max_agents",
                "label": "Max Concurrent Agents",
                "type": "number",
                "default": 5,
            },
        ],
    },
    "create_skill": {
        "label": "Create Skill",
        "description": "Create and manage reusable agent skills",
        "icon": "✨",
        "category": "agent",
        "fields": [],
    },
    "channel_manager": {
        "label": "Channel Manager",
        "description": "Manage communication channels (Telegram, Discord, Slack, etc.)",
        "icon": "📱",
        "category": "communication",
        "fields": [],
    },
    "sessions": {
        "label": "Sessions",
        "description": "Manage agent sessions and context windows",
        "icon": "🔄",
        "category": "agent",
        "fields": [
            {
                "name": "max_sessions",
                "label": "Max Active Sessions",
                "type": "number",
                "default": 10,
            },
            {
                "name": "session_timeout",
                "label": "Session Timeout (minutes)",
                "type": "number",
                "default": 60,
            },
        ],
    },
    "spawn_subagent": {
        "label": "Spawn Subagent",
        "description": "Spawn isolated sub-agents for parallel task execution",
        "icon": "🔀",
        "category": "agent",
        "fields": [
            {
                "name": "max_subagents",
                "label": "Max Concurrent Subagents",
                "type": "number",
                "default": 3,
            },
        ],
    },
    "gateway": {
        "label": "Gateway Control",
        "description": "Control Qubot gateway, view logs, restart services",
        "icon": "⚙️",
        "category": "system",
        "fields": [
            {
                "name": "allow_restart",
                "label": "Allow Service Restart",
                "type": "boolean",
                "default": False,
            },
        ],
    },
    "nodes": {
        "label": "Remote Nodes",
        "description": "Manage remote nodes for distributed task execution",
        "icon": "🖥️",
        "category": "system",
        "fields": [
            {
                "name": "auto_register",
                "label": "Auto-Register New Nodes",
                "type": "boolean",
                "default": True,
            },
        ],
    },
    "canvas": {
        "label": "Visual Canvas",
        "description": "Generate images, diagrams, and UI mockups",
        "icon": "🎨",
        "category": "data",
        "fields": [
            {
                "name": "default_width",
                "label": "Default Width (px)",
                "type": "number",
                "default": 800,
            },
            {
                "name": "default_height",
                "label": "Default Height (px)",
                "type": "number",
                "default": 600,
            },
        ],
    },
    "image_generation": {
        "label": "Image Generation",
        "description": "Generate images using AI models (DALL-E, Stable Diffusion)",
        "icon": "🖼️",
        "category": "data",
        "fields": [
            {
                "name": "default_model",
                "label": "Default Model",
                "type": "select",
                "default": "dalle-3",
                "options": ["dalle-3", "dalle-2", "stable-diffusion"],
            },
            {
                "name": "default_size",
                "label": "Default Size",
                "type": "select",
                "default": "1024x1024",
                "options": [
                    "256x256",
                    "512x512",
                    "1024x1024",
                    "1792x1024",
                    "1024x1792",
                ],
            },
        ],
    },
    "browser_profiles": {
        "label": "Browser Profiles",
        "description": "Manage isolated browser profiles with custom settings",
        "icon": "🌐",
        "category": "web",
        "fields": [
            {
                "name": "default_engine",
                "label": "Default Engine",
                "type": "select",
                "default": "chromium",
                "options": ["chromium", "firefox", "webkit"],
            },
        ],
    },
    "apply_patch": {
        "label": "Apply Patch",
        "description": "Apply code patches to files with diff-based modifications",
        "icon": "🩹",
        "category": "code",
        "fields": [
            {
                "name": "allow_reverse",
                "label": "Allow Patch Reversal",
                "type": "boolean",
                "default": True,
            },
        ],
    },
    "calendar": {
        "label": "Calendar",
        "description": "Manage Google Calendar and Microsoft Outlook events, scheduling, and availability",
        "icon": "📅",
        "category": "productivity",
        "fields": [
            {
                "name": "default_provider",
                "label": "Default Provider",
                "type": "select",
                "default": "google",
                "options": ["google", "outlook"],
            },
            {
                "name": "timezone",
                "label": "Default Timezone",
                "type": "text",
                "default": "UTC",
                "description": "e.g. America/New_York, Europe/London",
            },
            {
                "name": "google_token",
                "label": "Google Access Token",
                "type": "password",
                "env_var": "GOOGLE_ACCESS_TOKEN",
                "description": "OAuth access token from Google Calendar",
            },
            {
                "name": "google_client_id",
                "label": "Google Client ID",
                "type": "text",
                "env_var": "GOOGLE_CLIENT_ID",
            },
            {
                "name": "google_client_secret",
                "label": "Google Client Secret",
                "type": "password",
                "env_var": "GOOGLE_CLIENT_SECRET",
            },
            {
                "name": "microsoft_token",
                "label": "Microsoft Access Token",
                "type": "password",
                "env_var": "MICROSOFT_ACCESS_TOKEN",
                "description": "OAuth access token from Microsoft Graph",
            },
            {
                "name": "microsoft_client_id",
                "label": "Microsoft Client ID",
                "type": "text",
                "env_var": "MICROSOFT_CLIENT_ID",
            },
            {
                "name": "microsoft_client_secret",
                "label": "Microsoft Client Secret",
                "type": "password",
                "env_var": "MICROSOFT_CLIENT_SECRET",
            },
        ],
    },
    "voice": {
        "label": "Voice (STT/TTS)",
        "description": "Speech-to-text and text-to-speech using OpenAI Whisper and TTS",
        "icon": "🎤",
        "category": "communication",
        "fields": [
            {
                "name": "api_key",
                "label": "OpenAI API Key",
                "type": "password",
                "env_var": "OPENAI_API_KEY",
                "description": "OpenAI API key for Whisper (STT) and TTS",
            },
            {
                "name": "default_voice",
                "label": "Default Voice",
                "type": "select",
                "default": "alloy",
                "options": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                "description": "Default TTS voice",
            },
            {
                "name": "language",
                "label": "Default Language",
                "type": "text",
                "default": "en-US",
                "description": "BCP-47 language code (e.g., en-US, es-ES)",
            },
            {
                "name": "speech_speed",
                "label": "Speech Speed",
                "type": "number",
                "default": 1.0,
                "description": "Speech speed for TTS (0.25 to 4.0)",
            },
        ],
    },
    "secrets": {
        "label": "Secrets Manager",
        "description": "Securely store and manage API keys, tokens, and credentials",
        "icon": "🔐",
        "category": "security",
        "fields": [
            {
                "name": "encryption_key",
                "label": "Encryption Key",
                "type": "password",
                "env_var": "SECRETS_ENCRYPTION_KEY",
                "description": "Key used to encrypt secrets at rest",
            },
            {
                "name": "require_auth",
                "label": "Require Authentication",
                "type": "boolean",
                "default": True,
                "description": "Require user authentication to access secrets",
            },
        ],
    },
}

_MASKED = "••••••••"


def _is_password_field(tool_name: str, field_name: str) -> bool:
    schema = TOOL_CONFIG_SCHEMAS.get(tool_name, {})
    for f in schema.get("fields", []):
        if f["name"] == field_name and f.get("type") == "password":
            return True
    return False


def _mask_config(config: dict, tool_name: str) -> dict:
    return {
        k: (_MASKED if _is_password_field(tool_name, k) and v else v)
        for k, v in config.items()
    }


def _merge_with_incoming(existing: dict, incoming: dict, tool_name: str) -> dict:
    """Apply incoming values, keeping existing password values when masked placeholder is sent."""
    result = dict(existing)
    for k, v in incoming.items():
        if _is_password_field(tool_name, k) and v == _MASKED:
            pass  # keep existing
        else:
            result[k] = v
    return result


def _env_defaults(tool_name: str) -> dict:
    """Read env-var defaults declared in the tool schema."""
    defaults: dict = {}
    for f in TOOL_CONFIG_SCHEMAS.get(tool_name, {}).get("fields", []):
        ev = f.get("env_var")
        if ev:
            val = os.getenv(ev, "")
            if val:
                defaults[f["name"]] = val
    return defaults


def _reload_tool(tool_name: str, merged_config: dict) -> None:
    registry = get_tool_registry()
    tool_class = registry._tool_classes.get(tool_name)
    if tool_class:
        registry.reload(tool_class, merged_config)


def _build_tool_response(tool_name: str, db_record: IntegrationConfig | None) -> dict:
    schema = TOOL_CONFIG_SCHEMAS.get(tool_name, {})
    env_cfg = _env_defaults(tool_name)
    db_cfg = db_record.config if db_record else {}
    merged = {**env_cfg, **db_cfg}

    # Compute status
    required_fields = [f["name"] for f in schema.get("fields", []) if f.get("required")]
    optional_fields = [f for f in schema.get("fields", []) if not f.get("required")]
    if required_fields and all(merged.get(n) for n in required_fields):
        status = "configured"
    elif required_fields:
        status = "unconfigured"
    elif any(merged.get(f["name"]) for f in optional_fields):
        status = "configured"
    else:
        status = "optional"

    return {
        "tool_name": tool_name,
        "enabled": db_record.enabled if db_record else True,
        "config": _mask_config(merged, tool_name),
        "schema": schema,
        "status": status,
    }


# ============================================================================
# Tool Config Endpoints
# ============================================================================


@router.get("/tool-schemas")
async def get_tool_schemas(
    _: User = Depends(get_current_user),
):
    """Return config field schemas for all tools."""
    return {"data": TOOL_CONFIG_SCHEMAS}


@router.get("/tool-configs")
async def list_tool_configs(
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all tool configs (DB values merged with env var defaults)."""
    result = await session.execute(select(IntegrationConfig))
    records: dict[str, IntegrationConfig] = {
        r.tool_name: r for r in result.scalars().all()
    }

    tools = []
    for tool_name in TOOL_CONFIG_SCHEMAS:
        tools.append(_build_tool_response(tool_name, records.get(tool_name)))

    return {"data": tools}


@router.get("/tool-configs/{tool_name}")
async def get_tool_config(
    tool_name: str,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if tool_name not in TOOL_CONFIG_SCHEMAS:
        raise HTTPException(404, f"Unknown tool: {tool_name}")

    result = await session.execute(
        select(IntegrationConfig).where(IntegrationConfig.tool_name == tool_name)
    )
    record = result.scalar_one_or_none()
    return {"data": _build_tool_response(tool_name, record)}


@router.put("/tool-configs/{tool_name}")
async def save_tool_config(
    tool_name: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upsert tool config. Password fields sent as '••••••••' are kept unchanged."""
    if tool_name not in TOOL_CONFIG_SCHEMAS:
        raise HTTPException(404, f"Unknown tool: {tool_name}")

    incoming_config: dict = body.get("config", {})
    enabled: bool = body.get("enabled", True)

    result = await session.execute(
        select(IntegrationConfig).where(IntegrationConfig.tool_name == tool_name)
    )
    record = result.scalar_one_or_none()

    if record:
        merged = _merge_with_incoming(record.config, incoming_config, tool_name)
        record.config = merged
        record.enabled = enabled
        record.updated_at = datetime.utcnow()
    else:
        merged = _merge_with_incoming({}, incoming_config, tool_name)
        record = IntegrationConfig(tool_name=tool_name, enabled=enabled, config=merged)
        session.add(record)

    await session.commit()
    await session.refresh(record)

    # Reload the live tool instance with merged config (env defaults + DB)
    live_cfg = {**_env_defaults(tool_name), **merged}
    _reload_tool(tool_name, live_cfg)

    return {"data": _build_tool_response(tool_name, record)}


@router.delete("/tool-configs/{tool_name}")
async def reset_tool_config(
    tool_name: str,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Reset tool config to env-var defaults (removes DB overrides)."""
    if tool_name not in TOOL_CONFIG_SCHEMAS:
        raise HTTPException(404, f"Unknown tool: {tool_name}")

    result = await session.execute(
        select(IntegrationConfig).where(IntegrationConfig.tool_name == tool_name)
    )
    record = result.scalar_one_or_none()
    if record:
        await session.delete(record)
        await session.commit()

    _reload_tool(tool_name, _env_defaults(tool_name))
    return {"data": _build_tool_response(tool_name, None)}


@router.post("/tool-configs/{tool_name}/test")
async def test_tool_config(
    tool_name: str,
    body: dict,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Quick smoke-test for a tool using its current config.
    Runs a safe read-only operation specific to each tool type.
    """
    if tool_name not in TOOL_CONFIG_SCHEMAS:
        raise HTTPException(404, f"Unknown tool: {tool_name}")

    registry = get_tool_registry()
    tool = registry.get(tool_name)
    if not tool:
        raise HTTPException(400, f"Tool '{tool_name}' is not registered")

    try:
        # Each tool gets a lightweight test invocation
        test_params: dict = {}
        if tool_name == "github":
            test_params = {"operation": "list_repos", "per_page": 1}
        elif tool_name == "web_search":
            test_params = {"query": "test", "max_results": 1}
        elif tool_name == "web_browser":
            test_params = {"url": "https://httpbin.org/get"}
        elif tool_name == "http_api":
            test_params = {"url": "https://httpbin.org/get", "method": "GET"}
        elif tool_name == "docs_search":
            test_params = {"library": "requests", "max_tokens": 500}
        elif tool_name == "notification":
            return {
                "data": {
                    "success": True,
                    "message": "Webhook URLs saved — send a test message via agents to verify delivery.",
                }
            }
        elif tool_name == "email":
            return {
                "data": {
                    "success": True,
                    "message": "Email config saved — send a test email via agents to verify SMTP.",
                }
            }
        elif tool_name == "agent_memory":
            test_params = {"operation": "list", "top_k": 1}
        elif tool_name == "database_query":
            test_params = {"query": "SELECT 1 AS ok", "limit": 1}
        elif tool_name == "code_executor":
            test_params = {"code": "print('ok')", "language": "python", "timeout": 5}
        elif tool_name == "filesystem":
            test_params = {"action": "list", "path": "/"}
        elif tool_name in ("browser_automation",):
            return {"data": {"success": True, "message": "Playwright config saved."}}
        elif tool_name == "mcp_installer":
            test_params = {"operation": "list_registered"}
        else:
            return {
                "data": {
                    "success": True,
                    "message": f"{tool_name} has no test operation.",
                }
            }

        result = await tool.execute(**test_params)
        return {
            "data": {
                "success": result.success,
                "output": (result.stdout or str(result.data))[:500]
                if result.success
                else result.error,
                "execution_time_ms": result.execution_time_ms,
            }
        }
    except Exception as e:
        return {"data": {"success": False, "output": str(e)}}


# ============================================================================
# MCP Server Endpoints
# ============================================================================


@router.get("/mcp-servers")
async def list_mcp_servers(
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(MCPServer).order_by(MCPServer.created_at))
    servers = result.scalars().all()
    return {"data": [_server_to_dict(s) for s in servers]}


@router.post("/mcp-servers", status_code=201)
async def create_mcp_server(
    body: dict,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    server = MCPServer(
        name=body["name"],
        description=body.get("description", ""),
        server_type=body.get("server_type", "sse"),
        url=body.get("url", ""),
        command=body.get("command", ""),
        args=body.get("args", []),
        env_vars=body.get("env_vars", {}),
        headers=body.get("headers", {}),
        enabled=body.get("enabled", True),
    )
    session.add(server)
    await session.commit()
    await session.refresh(server)
    return {"data": _server_to_dict(server)}


@router.get("/mcp-servers/{server_id}")
async def get_mcp_server(
    server_id: UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    server = await _get_server_or_404(session, server_id)
    return {"data": _server_to_dict(server)}


@router.put("/mcp-servers/{server_id}")
async def update_mcp_server(
    server_id: UUID,
    body: dict,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    server = await _get_server_or_404(session, server_id)
    updatable = [
        "name",
        "description",
        "server_type",
        "url",
        "command",
        "args",
        "env_vars",
        "headers",
        "enabled",
    ]
    for field in updatable:
        if field in body:
            setattr(server, field, body[field])
    server.updated_at = datetime.utcnow()
    session.add(server)
    await session.commit()
    await session.refresh(server)
    return {"data": _server_to_dict(server)}


@router.delete("/mcp-servers/{server_id}", status_code=204)
async def delete_mcp_server(
    server_id: UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    server = await _get_server_or_404(session, server_id)
    await session.delete(server)
    await session.commit()


@router.post("/mcp-servers/{server_id}/test")
async def test_mcp_server(
    server_id: UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Connect to the MCP server, fetch its tool list, and return it."""
    server = await _get_server_or_404(session, server_id)
    try:
        tools = await _fetch_tools(server)
        server.tools_cache = tools
        server.status = "connected"
        server.error_msg = ""
        server.last_connected = datetime.utcnow()
        server.updated_at = datetime.utcnow()
        session.add(server)
        await session.commit()
        await session.refresh(server)
        return {
            "data": {"status": "connected", "tools": tools, "tool_count": len(tools)}
        }
    except Exception as e:
        server.status = "error"
        server.error_msg = str(e)[:1000]
        server.updated_at = datetime.utcnow()
        session.add(server)
        await session.commit()
        return {"data": {"status": "error", "error": str(e), "tools": []}}


@router.post("/mcp-servers/{server_id}/sync")
async def sync_mcp_server(
    server_id: UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Sync (refresh) tool list from the MCP server."""
    return await test_mcp_server(server_id, _, session)


@router.post("/mcp-servers/{server_id}/call/{tool_name}")
async def call_mcp_tool(
    server_id: UUID,
    tool_name: str,
    body: dict,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Call a specific tool on an MCP server."""
    server = await _get_server_or_404(session, server_id)
    args: dict = body.get("args", {})
    try:
        if server.server_type == "sse":
            result = await call_tool_sse(server.url, tool_name, args, server.headers)
        elif server.server_type == "stdio":
            result = await call_tool_stdio(
                server.command, server.args, tool_name, args, server.env_vars
            )
        else:
            raise HTTPException(400, f"Unsupported server_type: {server.server_type}")
        return {"data": {"success": True, "result": result}}
    except Exception as e:
        return {"data": {"success": False, "error": str(e)}}


# ============================================================================
# Helpers
# ============================================================================


def _server_to_dict(s: MCPServer) -> dict:
    return {
        "id": str(s.id),
        "name": s.name,
        "description": s.description,
        "server_type": s.server_type,
        "url": s.url,
        "command": s.command,
        "args": s.args,
        "env_vars": s.env_vars,
        "headers": {k: "••••••••" if v else "" for k, v in s.headers.items()},
        "enabled": s.enabled,
        "tools_cache": s.tools_cache,
        "tool_count": len(s.tools_cache),
        "status": s.status,
        "error_msg": s.error_msg,
        "last_connected": s.last_connected.isoformat() if s.last_connected else None,
        "created_at": s.created_at.isoformat(),
    }


async def _get_server_or_404(session: AsyncSession, server_id: UUID) -> MCPServer:
    result = await session.execute(select(MCPServer).where(MCPServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(404, "MCP server not found")
    return server


async def _fetch_tools(server: MCPServer) -> list[dict]:
    if server.server_type == "sse":
        if not server.url:
            raise ValueError("SSE server requires a URL")
        return await list_tools_sse(server.url, server.headers)
    elif server.server_type == "stdio":
        if not server.command:
            raise ValueError("stdio server requires a command")
        return await list_tools_stdio(server.command, server.args, server.env_vars)
    else:
        raise ValueError(f"Unsupported server_type: {server.server_type}")


# ============================================================================
# CALENDAR CONFIG SCHEMAS
# ============================================================================

CALENDAR_CONFIG_SCHEMAS: dict = {
    "google_calendar": {
        "label": "Google Calendar",
        "description": "Connect to Google Calendar API for scheduling and events",
        "icon": "📅",
        "category": "productivity",
        "fields": [
            {
                "name": "client_id",
                "label": "Client ID",
                "type": "text",
                "env_var": "GOOGLE_CLIENT_ID",
                "description": "Google OAuth Client ID from Google Cloud Console",
            },
            {
                "name": "client_secret",
                "label": "Client Secret",
                "type": "password",
                "env_var": "GOOGLE_CLIENT_SECRET",
                "description": "Google OAuth Client Secret",
            },
            {
                "name": "redirect_uri",
                "label": "Redirect URI",
                "type": "text",
                "default": "http://localhost:8000/api/calendar/google/callback",
                "description": "OAuth redirect URI (must match Google Cloud Console)",
            },
            {
                "name": "timezone",
                "label": "Default Timezone",
                "type": "text",
                "default": "UTC",
                "description": "e.g. America/New_York, Europe/London",
            },
        ],
    },
    "outlook_calendar": {
        "label": "Microsoft Outlook",
        "description": "Connect to Microsoft Outlook via Graph API",
        "icon": "📤",
        "category": "productivity",
        "fields": [
            {
                "name": "client_id",
                "label": "Application (Client) ID",
                "type": "text",
                "env_var": "MICROSOFT_CLIENT_ID",
                "description": "Azure AD Application ID from Microsoft Entra ID",
            },
            {
                "name": "client_secret",
                "label": "Client Secret",
                "type": "password",
                "env_var": "MICROSOFT_CLIENT_SECRET",
                "description": "Azure AD Client Secret",
            },
            {
                "name": "tenant_id",
                "label": "Tenant ID",
                "type": "text",
                "default": "common",
                "env_var": "MICROSOFT_TENANT_ID",
                "description": "Azure AD Tenant ID (use 'common' for multi-tenant)",
            },
            {
                "name": "redirect_uri",
                "label": "Redirect URI",
                "type": "text",
                "default": "http://localhost:8000/api/calendar/outlook/callback",
                "description": "OAuth redirect URI (must match Azure app registration)",
            },
            {
                "name": "timezone",
                "label": "Default Timezone",
                "type": "text",
                "default": "UTC",
            },
        ],
    },
}


# ============================================================================
# CHANNEL CONFIG SCHEMAS
# ============================================================================

CHANNEL_CONFIG_SCHEMAS: dict = {
    "discord": {
        "label": "Discord",
        "description": "Connect via Discord bot with slash commands",
        "icon": "discord",
        "category": "messaging",
        "fields": [
            {
                "name": "bot_token",
                "label": "Bot Token",
                "type": "password",
                "env_var": "DISCORD_BOT_TOKEN",
            },
            {
                "name": "application_id",
                "label": "Application ID",
                "type": "text",
                "env_var": "DISCORD_APPLICATION_ID",
            },
            {
                "name": "public_key",
                "label": "Public Key",
                "type": "password",
                "env_var": "DISCORD_PUBLIC_KEY",
            },
        ],
    },
    "slack": {
        "label": "Slack",
        "description": "Slack app with slash commands and events",
        "icon": "slack",
        "category": "messaging",
        "fields": [
            {
                "name": "bot_token",
                "label": "Bot Token (xoxb-...)",
                "type": "password",
                "env_var": "SLACK_BOT_TOKEN",
            },
            {
                "name": "signing_secret",
                "label": "Signing Secret",
                "type": "password",
                "env_var": "SLACK_SIGNING_SECRET",
            },
            {
                "name": "workspace_id",
                "label": "Workspace ID",
                "type": "text",
                "env_var": "SLACK_WORKSPACE_ID",
            },
        ],
    },
    "telegram": {
        "label": "Telegram",
        "description": "Telegram bot with commands and webhooks",
        "icon": "telegram",
        "category": "messaging",
        "fields": [
            {
                "name": "bot_token",
                "label": "Bot Token",
                "type": "password",
                "env_var": "TELEGRAM_BOT_TOKEN",
            },
        ],
    },
    "whatsapp": {
        "label": "WhatsApp",
        "description": "WhatsApp Business API via Twilio",
        "icon": "whatsapp",
        "category": "messaging",
        "fields": [
            {
                "name": "account_sid",
                "label": "Account SID",
                "type": "text",
                "env_var": "TWILIO_ACCOUNT_SID",
            },
            {
                "name": "auth_token",
                "label": "Auth Token",
                "type": "password",
                "env_var": "TWILIO_AUTH_TOKEN",
            },
            {
                "name": "phone_number",
                "label": "WhatsApp Number",
                "type": "text",
                "env_var": "TWILIO_WHATSAPP_NUMBER",
            },
        ],
    },
    "signal": {
        "label": "Signal",
        "description": "Signal messenger bot",
        "icon": "signal",
        "category": "messaging",
        "fields": [
            {
                "name": "phone_number",
                "label": "Signal Number",
                "type": "text",
                "env_var": "SIGNAL_PHONE_NUMBER",
            },
            {
                "name": "signal_cli_path",
                "label": "signal-cli Path",
                "type": "text",
                "env_var": "SIGNAL_CLI_PATH",
            },
        ],
    },
    "teams": {
        "label": "Microsoft Teams",
        "description": "Teams bot via Azure Bot Framework",
        "icon": "teams",
        "category": "messaging",
        "fields": [
            {
                "name": "app_id",
                "label": "Application ID",
                "type": "text",
                "env_var": "TEAMS_APP_ID",
            },
            {
                "name": "app_password",
                "label": "App Password",
                "type": "password",
                "env_var": "TEAMS_APP_PASSWORD",
            },
            {
                "name": "tenant_id",
                "label": "Tenant ID",
                "type": "text",
                "env_var": "TEAMS_TENANT_ID",
            },
        ],
    },
    "googlechat": {
        "label": "Google Chat",
        "description": "Google Chat bot via webhook",
        "icon": "googlechat",
        "category": "messaging",
        "fields": [
            {
                "name": "webhook_url",
                "label": "Webhook URL",
                "type": "password",
                "env_var": "GOOGLE_CHAT_WEBHOOK_URL",
            },
        ],
    },
    "imessage": {
        "label": "iMessage",
        "description": "iMessage via Mac junction tool",
        "icon": "imessage",
        "category": "messaging",
        "fields": [
            {
                "name": "junction_token",
                "label": "Junction Token",
                "type": "password",
                "env_var": "JUNCTION_TOKEN",
            },
        ],
    },
    "matrix": {
        "label": "Matrix",
        "description": "Matrix/Element protocol client",
        "icon": "matrix",
        "category": "messaging",
        "fields": [
            {
                "name": "homeserver",
                "label": "Homeserver URL",
                "type": "text",
                "env_var": "MATRIX_HOMESERVER",
            },
            {
                "name": "user_id",
                "label": "User ID",
                "type": "text",
                "env_var": "MATRIX_USER_ID",
            },
            {
                "name": "access_token",
                "label": "Access Token",
                "type": "password",
                "env_var": "MATRIX_ACCESS_TOKEN",
            },
        ],
    },
    "mattermost": {
        "label": "Mattermost",
        "description": "Mattermost team communication",
        "icon": "mattermost",
        "category": "messaging",
        "fields": [
            {
                "name": "server_url",
                "label": "Server URL",
                "type": "text",
                "env_var": "MATTERMOST_SERVER_URL",
            },
            {
                "name": "api_key",
                "label": "API Key",
                "type": "password",
                "env_var": "MATTERMOST_API_KEY",
            },
            {
                "name": "team",
                "label": "Team Name",
                "type": "text",
                "env_var": "MATTERMOST_TEAM",
            },
        ],
    },
    "irc": {
        "label": "IRC",
        "description": "Internet Relay Chat",
        "icon": "irc",
        "category": "messaging",
        "fields": [
            {
                "name": "server",
                "label": "Server",
                "type": "text",
                "env_var": "IRC_SERVER",
            },
            {
                "name": "port",
                "label": "Port",
                "type": "number",
                "default": 6667,
                "env_var": "IRC_PORT",
            },
            {
                "name": "channel",
                "label": "Channel",
                "type": "text",
                "env_var": "IRC_CHANNEL",
            },
            {
                "name": "nickname",
                "label": "Nickname",
                "type": "text",
                "default": "qubot",
                "env_var": "IRC_NICKNAME",
            },
        ],
    },
    "line": {
        "label": "LINE",
        "description": "LINE messaging platform",
        "icon": "line",
        "category": "messaging",
        "fields": [
            {
                "name": "channel_id",
                "label": "Channel ID",
                "type": "text",
                "env_var": "LINE_CHANNEL_ID",
            },
            {
                "name": "channel_secret",
                "label": "Channel Secret",
                "type": "password",
                "env_var": "LINE_CHANNEL_SECRET",
            },
            {
                "name": "access_token",
                "label": "Access Token",
                "type": "password",
                "env_var": "LINE_ACCESS_TOKEN",
            },
        ],
    },
    "feishu": {
        "label": "Feishu (Lark)",
        "description": "Feishu/Lark enterprise messaging",
        "icon": "feishu",
        "category": "messaging",
        "fields": [
            {
                "name": "app_id",
                "label": "App ID",
                "type": "text",
                "env_var": "FEISHU_APP_ID",
            },
            {
                "name": "app_secret",
                "label": "App Secret",
                "type": "password",
                "env_var": "FEISHU_APP_SECRET",
            },
        ],
    },
    "twitch": {
        "label": "Twitch",
        "description": "Twitch chat bot",
        "icon": "twitch",
        "category": "streaming",
        "fields": [
            {
                "name": "client_id",
                "label": "Client ID",
                "type": "text",
                "env_var": "TWITCH_CLIENT_ID",
            },
            {
                "name": "client_secret",
                "label": "Client Secret",
                "type": "password",
                "env_var": "TWITCH_CLIENT_SECRET",
            },
            {
                "name": "channel",
                "label": "Channel",
                "type": "text",
                "env_var": "TWITCH_CHANNEL",
            },
        ],
    },
    "nostr": {
        "label": "Nostr",
        "description": "Nostr decentralized protocol",
        "icon": "nostr",
        "category": "messaging",
        "fields": [
            {
                "name": "relays",
                "label": "Relays (comma-separated)",
                "type": "text",
                "default": "wss://relay.damus.io",
                "env_var": "NOSTR_RELAYS",
            },
            {
                "name": "private_key",
                "label": "Private Key (nsec...)",
                "type": "password",
                "env_var": "NOSTR_PRIVATE_KEY",
            },
            {
                "name": "public_key",
                "label": "Public Key (npub...)",
                "type": "password",
                "env_var": "NOSTR_PUBLIC_KEY",
            },
        ],
    },
    "synology_chat": {
        "label": "Synology Chat",
        "description": "Synology Chat Server",
        "icon": "synology",
        "category": "messaging",
        "fields": [
            {
                "name": "server_url",
                "label": "Server URL",
                "type": "text",
                "env_var": "SYNOLOGY_SERVER_URL",
            },
            {
                "name": "plugin_token",
                "label": "Plugin Token",
                "type": "password",
                "env_var": "SYNOLOGY_PLUGIN_TOKEN",
            },
        ],
    },
    "zalo": {
        "label": "Zalo",
        "description": "Zalo messaging platform",
        "icon": "zalo",
        "category": "messaging",
        "fields": [
            {
                "name": "app_id",
                "label": "App ID",
                "type": "text",
                "env_var": "ZALO_APP_ID",
            },
            {
                "name": "app_secret",
                "label": "App Secret",
                "type": "password",
                "env_var": "ZALO_APP_SECRET",
            },
            {
                "name": "access_token",
                "label": "Access Token",
                "type": "password",
                "env_var": "ZALO_ACCESS_TOKEN",
            },
        ],
    },
}


def _env_defaults_channel(channel_name: str) -> dict:
    defaults: dict = {}
    for f in CHANNEL_CONFIG_SCHEMAS.get(channel_name, {}).get("fields", []):
        ev = f.get("env_var")
        if ev:
            val = os.getenv(ev, "")
            if val:
                defaults[f["name"]] = val
    return defaults


def _is_password_field_channel(channel_name: str, field_name: str) -> bool:
    schema = CHANNEL_CONFIG_SCHEMAS.get(channel_name, {})
    for f in schema.get("fields", []):
        if f["name"] == field_name and f.get("type") == "password":
            return True
    return False


def _mask_channel_config(config: dict, channel_name: str) -> dict:
    return {
        k: ("••••••••" if _is_password_field_channel(channel_name, k) and v else v)
        for k, v in config.items()
    }


def _build_channel_response(channel_name: str, config: dict) -> dict:
    schema = CHANNEL_CONFIG_SCHEMAS.get(channel_name, {})
    env_cfg = _env_defaults_channel(channel_name)
    merged = {**env_cfg, **config}

    required_fields = [f["name"] for f in schema.get("fields", []) if f.get("required")]
    optional_fields = [f for f in schema.get("fields", []) if not f.get("required")]

    if required_fields and all(merged.get(n) for n in required_fields):
        status = "configured"
    elif required_fields:
        status = "unconfigured"
    elif any(merged.get(f["name"]) for f in optional_fields):
        status = "configured"
    else:
        status = "optional"

    return {
        "channel_name": channel_name,
        "enabled": True,
        "config": _mask_channel_config(merged, channel_name),
        "schema": schema,
        "status": status,
    }


# ============================================================================
# CHANNEL ENDPOINTS
# ============================================================================


@router.get("/channel-schemas")
async def get_channel_schemas(
    _: User = Depends(get_current_user),
):
    return {"data": CHANNEL_CONFIG_SCHEMAS}


@router.get("/channels")
async def list_channels(
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    channels = []
    for channel_name in CHANNEL_CONFIG_SCHEMAS:
        channels.append(_build_channel_response(channel_name, {}))
    return {"data": channels}


@router.get("/channels/{channel_name}")
async def get_channel(
    channel_name: str,
    _: User = Depends(get_current_user),
):
    if channel_name not in CHANNEL_CONFIG_SCHEMAS:
        raise HTTPException(404, f"Unknown channel: {channel_name}")
    return {"data": _build_channel_response(channel_name, {})}


@router.post("/channels/{channel_name}/test")
async def test_channel(
    channel_name: str,
    _: User = Depends(get_current_user),
):
    if channel_name not in CHANNEL_CONFIG_SCHEMAS:
        raise HTTPException(404, f"Unknown channel: {channel_name}")

    config = _env_defaults_channel(channel_name)
    if config:
        return {
            "data": {
                "success": True,
                "message": f"{channel_name} configured via env vars",
            }
        }

    return {"data": {"success": False, "message": f"{channel_name} not configured"}}
