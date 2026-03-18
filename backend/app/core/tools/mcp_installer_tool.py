"""
MCP Installer Tool - Autonomous MCP server management for agents.

Allows agents to:
- Browse a curated catalog of popular MCP servers
- Register new MCP servers (SSE or stdio) in the platform DB
- Unregister servers they no longer need
- List currently registered servers and their status

After registering a server, it becomes available for syncing (fetching tool list)
and will appear in future task execution loops automatically.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


# ---------------------------------------------------------------------------
# Curated catalog of popular MCP servers
# ---------------------------------------------------------------------------
POPULAR_MCP_SERVERS: list[dict[str, Any]] = [
    {
        "name": "filesystem",
        "description": "Read/write files via MCP — exposes your filesystem to agents",
        "server_type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
        "env_required": [],
    },
    {
        "name": "fetch",
        "description": "Fetch any URL and convert HTML to Markdown — great for web research",
        "server_type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-fetch"],
        "env_required": [],
    },
    {
        "name": "sequential-thinking",
        "description": "Structured multi-step reasoning — improves agent decision quality",
        "server_type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
        "env_required": [],
    },
    {
        "name": "memory",
        "description": "Knowledge graph persistent memory — agents remember across sessions",
        "server_type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "env_required": [],
    },
    {
        "name": "github",
        "description": "GitHub repos, issues, PRs, code search via MCP",
        "server_type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env_required": ["GITHUB_TOKEN"],
    },
    {
        "name": "brave-search",
        "description": "Web search via Brave Search API — privacy-focused, no Google dependency",
        "server_type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env_required": ["BRAVE_API_KEY"],
    },
    {
        "name": "slack",
        "description": "Send and read Slack messages — connect agents to your workspace",
        "server_type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env_required": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
    },
    {
        "name": "postgres",
        "description": "Direct PostgreSQL read access via MCP",
        "server_type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres"],
        "env_required": ["POSTGRES_CONNECTION_STRING"],
    },
    {
        "name": "sqlite",
        "description": "SQLite database access — good for local data analysis",
        "server_type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "/workspace/data.db"],
        "env_required": [],
    },
    {
        "name": "puppeteer",
        "description": "Browser automation via Puppeteer — screenshot, click, fill forms",
        "server_type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        "env_required": [],
    },
    {
        "name": "google-maps",
        "description": "Google Maps API — geocoding, directions, place search",
        "server_type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-google-maps"],
        "env_required": ["GOOGLE_MAPS_API_KEY"],
    },
    {
        "name": "context7",
        "description": "Real-time library documentation (Context7) — always up-to-date docs",
        "server_type": "sse",
        "url": "https://mcp.context7.com/mcp",
        "args": [],
        "env_required": [],
    },
    {
        "name": "exa-search",
        "description": "Exa semantic search — finds content by meaning, not just keywords",
        "server_type": "stdio",
        "command": "npx",
        "args": ["-y", "exa-mcp-server"],
        "env_required": ["EXA_API_KEY"],
    },
    {
        "name": "tavily-search",
        "description": "Tavily AI-powered web search — optimized for LLM agents",
        "server_type": "stdio",
        "command": "npx",
        "args": ["-y", "tavily-mcp@0.1.2"],
        "env_required": ["TAVILY_API_KEY"],
    },
]


class MCPInstallerTool(BaseTool):
    """
    Autonomous MCP server manager.

    Use this tool to extend your capabilities by discovering and registering
    MCP (Model Context Protocol) servers. Once registered, their tools become
    available in your execution loop automatically.

    Operations:
    - list_popular: Browse curated catalog of popular MCP servers
    - list_registered: See what MCP servers are currently installed
    - register: Add a new MCP server (SSE or stdio) to the platform
    - unregister: Remove an MCP server by name
    """

    name = "mcp_installer"
    description = (
        "Manage MCP (Model Context Protocol) servers to extend agent capabilities. "
        "Use 'list_popular' to discover available servers. "
        "Use 'register' to add a server (SSE URL or stdio command). "
        "Use 'list_registered' to see currently installed servers. "
        "Use 'unregister' to remove a server by name. "
        "After registering, the server's tools appear in your next task automatically."
    )
    category = ToolCategory.MISC
    risk_level = ToolRiskLevel.NORMAL

    def _validate_config(self) -> None:
        from app.config import settings

        self.db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "operation": ToolParameter(
                name="operation",
                type="string",
                description="Operation: 'list_popular', 'list_registered', 'register', 'unregister'",
                required=True,
                enum=["list_popular", "list_registered", "register", "unregister"],
            ),
            "name": ToolParameter(
                name="name",
                type="string",
                description="Server name (required for register/unregister)",
                required=False,
                default=None,
            ),
            "description": ToolParameter(
                name="description",
                type="string",
                description="Human-readable description of the server",
                required=False,
                default=None,
            ),
            "server_type": ToolParameter(
                name="server_type",
                type="string",
                description="Transport: 'sse' (HTTP URL) or 'stdio' (local process)",
                required=False,
                enum=["sse", "stdio"],
                default="stdio",
            ),
            "url": ToolParameter(
                name="url",
                type="string",
                description="Full URL for SSE servers (e.g., https://mcp.example.com/sse)",
                required=False,
                default=None,
            ),
            "command": ToolParameter(
                name="command",
                type="string",
                description="Executable for stdio servers (e.g., 'npx', 'python', 'uvx')",
                required=False,
                default=None,
            ),
            "args": ToolParameter(
                name="args",
                type="array",
                description="Arguments for stdio command (e.g., ['-y', '@modelcontextprotocol/server-fetch'])",
                required=False,
                default=None,
            ),
            "env_vars": ToolParameter(
                name="env_vars",
                type="object",
                description="Environment variables for the server (e.g., {'GITHUB_TOKEN': 'ghp_...'})",
                required=False,
                default=None,
            ),
        }

    async def execute(
        self,
        operation: str,
        name: str | None = None,
        description: str | None = None,
        server_type: str = "stdio",
        url: str | None = None,
        command: str | None = None,
        args: list[str] | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> ToolResult:
        start = time.time()

        if operation == "list_popular":
            return self._list_popular()

        try:
            import asyncpg
        except ImportError:
            return ToolResult(success=False, error="asyncpg not installed")

        conn = None
        try:
            conn = await asyncpg.connect(self.db_url, timeout=10)

            if operation == "list_registered":
                return await self._list_registered(conn, start)

            elif operation == "register":
                return await self._register(conn, name, description, server_type, url, command, args, env_vars, start)

            elif operation == "unregister":
                return await self._unregister(conn, name, start)

            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"MCP installer failed: {e}",
                execution_time_ms=int((time.time() - start) * 1000),
            )
        finally:
            if conn:
                await conn.close()

    # -------------------------------------------------------------------------
    # Operation implementations
    # -------------------------------------------------------------------------

    def _list_popular(self) -> ToolResult:
        lines = [f"📦 Popular MCP Servers ({len(POPULAR_MCP_SERVERS)} available)\n"]
        for s in POPULAR_MCP_SERVERS:
            env_note = ""
            if s.get("env_required"):
                env_note = f" ⚠️ Requires: {', '.join(s['env_required'])}"
            install_info = s.get("url", "") if s["server_type"] == "sse" else (
                f"{s.get('command', '')} {' '.join(s.get('args', []))}"
            )
            lines.append(f"• [{s['server_type'].upper()}] {s['name']}{env_note}")
            lines.append(f"  {s['description']}")
            lines.append(f"  Install: {install_info}")
            lines.append("")

        lines.append("💡 To install one: mcp_installer.register(name='fetch', server_type='stdio', command='npx', args=['-y', '@modelcontextprotocol/server-fetch'])")

        return ToolResult(
            success=True,
            data=POPULAR_MCP_SERVERS,
            stdout="\n".join(lines),
        )

    async def _list_registered(self, conn, start: float) -> ToolResult:
        rows = await conn.fetch(
            """
            SELECT name, description, server_type, url, command, args,
                   enabled, status, error_msg,
                   jsonb_array_length(tools_cache) AS tool_count,
                   last_connected, created_at
            FROM mcp_server
            ORDER BY created_at DESC
            """
        )
        if not rows:
            return ToolResult(
                success=True,
                data=[],
                stdout="No MCP servers registered yet. Use 'list_popular' to discover available servers.",
                execution_time_ms=int((time.time() - start) * 1000),
            )

        servers = []
        lines = [f"🔌 Registered MCP Servers ({len(rows)})\n"]
        for r in rows:
            status_icon = "✅" if (r["enabled"] and r["status"] == "connected") else ("⚠️" if r["enabled"] else "⛔")
            tool_count = r["tool_count"] or 0
            entry = {
                "name": r["name"],
                "server_type": r["server_type"],
                "enabled": r["enabled"],
                "status": r["status"],
                "tool_count": tool_count,
                "last_connected": r["last_connected"].isoformat() if r["last_connected"] else None,
            }
            servers.append(entry)
            lines.append(f"{status_icon} {r['name']} ({r['server_type']}) — {tool_count} tools — {r['status']}")
            if r["error_msg"]:
                lines.append(f"   Error: {r['error_msg'][:100]}")

        lines.append("")
        lines.append("💡 Sync a server in Settings → Integrations → MCP Servers to fetch its tool list.")

        return ToolResult(
            success=True,
            data=servers,
            stdout="\n".join(lines),
            execution_time_ms=int((time.time() - start) * 1000),
        )

    async def _register(
        self, conn,
        name: str | None,
        description: str | None,
        server_type: str,
        url: str | None,
        command: str | None,
        args: list | None,
        env_vars: dict | None,
        start: float,
    ) -> ToolResult:
        if not name:
            return ToolResult(success=False, error="'name' is required for register operation.")

        # Auto-detect server_type
        if not server_type:
            server_type = "sse" if url else "stdio"

        if server_type == "sse" and not url:
            return ToolResult(success=False, error="'url' is required for SSE servers.")
        if server_type == "stdio" and not command:
            return ToolResult(success=False, error="'command' is required for stdio servers.")

        server_id = str(uuid.uuid4())
        try:
            await conn.execute(
                """
                INSERT INTO mcp_server
                    (id, name, description, server_type, url, command, args,
                     env_vars, headers, enabled, tools_cache, status, error_msg,
                     created_at, updated_at)
                VALUES
                    ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, '{}'::jsonb,
                     true, '[]'::jsonb, 'disconnected', '', NOW(), NOW())
                ON CONFLICT (name) DO UPDATE SET
                    description  = EXCLUDED.description,
                    server_type  = EXCLUDED.server_type,
                    url          = EXCLUDED.url,
                    command      = EXCLUDED.command,
                    args         = EXCLUDED.args,
                    env_vars     = EXCLUDED.env_vars,
                    updated_at   = NOW()
                """,
                server_id,
                name,
                description or "",
                server_type,
                url or "",
                command or "",
                json.dumps(args or []),
                json.dumps(env_vars or {}),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to save MCP server: {e}",
                execution_time_ms=int((time.time() - start) * 1000),
            )

        msg_lines = [
            f"✅ MCP server '{name}' registered successfully!",
            "",
            f"  Type: {server_type}",
        ]
        if server_type == "sse":
            msg_lines.append(f"  URL: {url}")
        else:
            msg_lines.append(f"  Command: {command} {' '.join(args or [])}")
        msg_lines.extend([
            "",
            "Next steps:",
            "  1. Go to Settings → Integrations → MCP Servers",
            "  2. Click 'Sync' on the new server to fetch its tool list",
            "  3. The tools will be available in your next task automatically",
            "",
            "Or ask me to verify the connection and I'll use the integration API.",
        ])

        return ToolResult(
            success=True,
            data={"id": server_id, "name": name, "server_type": server_type},
            stdout="\n".join(msg_lines),
            execution_time_ms=int((time.time() - start) * 1000),
        )

    async def _unregister(self, conn, name: str | None, start: float) -> ToolResult:
        if not name:
            return ToolResult(success=False, error="'name' is required for unregister operation.")

        result = await conn.execute("DELETE FROM mcp_server WHERE name = $1", name)
        deleted = result != "DELETE 0"

        return ToolResult(
            success=True,
            data={"name": name, "deleted": deleted},
            stdout=(
                f"✅ MCP server '{name}' removed."
                if deleted
                else f"⚠️ MCP server '{name}' not found (already removed?)."
            ),
            execution_time_ms=int((time.time() - start) * 1000),
        )
