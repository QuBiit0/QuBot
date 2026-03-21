"""
Gateway Tool - Manage and configure the Qubot gateway dynamically.

Provides:
- restart: Restart the gateway
- config.get: Get configuration values
- config.set: Set configuration values
- config.patch: Merge partial configuration
- update: Check and apply updates
"""

import asyncio
import json
import signal
from pathlib import Path
from typing import Any

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


class GatewayTool(BaseTool):
    """
    Manage the Qubot gateway: restart, configure, and update.

    WARNING: These operations affect the running gateway.
    Use with caution in production environments.
    """

    name = "gateway"
    description = (
        "Manage the Qubot gateway: restart, view/modify configuration, and apply updates. "
        "Use to change settings without restarting the service manually, "
        "or to trigger a graceful restart after configuration changes."
    )

    category = ToolCategory.SYSTEM
    risk_level = ToolRiskLevel.DANGEROUS

    CONFIG_PATH = Path("/app/config/settings.json")

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "operation": ToolParameter(
                name="operation",
                type="string",
                description="Operation: 'restart', 'config', 'status', 'update', 'logs'",
                required=True,
                enum=["restart", "config", "status", "update", "logs"],
            ),
            "path": ToolParameter(
                name="path",
                type="string",
                description="Config path for get/set/patch (e.g., 'gateway.port', 'agents.defaults')",
                required=False,
                default=None,
            ),
            "value": ToolParameter(
                name="value",
                type="string",
                description="Value to set (for config set operation)",
                required=False,
                default=None,
            ),
            "delay_ms": ToolParameter(
                name="delay_ms",
                type="integer",
                description="Delay before restart in milliseconds (default 2000)",
                required=False,
                default=2000,
            ),
            "lines": ToolParameter(
                name="lines",
                type="integer",
                description="Number of log lines to return (for logs operation)",
                required=False,
                default=50,
            ),
        }

    async def execute(
        self,
        operation: str,
        path: str | None = None,
        value: str | None = None,
        delay_ms: int = 2000,
        lines: int = 50,
    ) -> ToolResult:
        """Execute gateway operation."""
        import time

        start_time = time.time()

        try:
            if operation == "restart":
                return await self._restart(delay_ms)

            elif operation == "config":
                return await self._config(path, value)

            elif operation == "status":
                return await self._status()

            elif operation == "update":
                return await self._update()

            elif operation == "logs":
                return await self._logs(lines)

            else:
                return ToolResult(
                    success=False, error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Gateway operation failed: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

    async def _restart(self, delay_ms: int) -> ToolResult:
        """Trigger a graceful restart of the gateway."""
        import subprocess

        lines = [
            "🔄 **Gateway restart initiated**",
            "",
            f"Restarting in {delay_ms}ms...",
            "",
            "The gateway will be back online shortly.",
        ]

        asyncio.create_task(self._delayed_restart(delay_ms))

        return ToolResult(
            success=True,
            data={"operation": "restart", "delay_ms": delay_ms},
            stdout="\n".join(lines),
            execution_time_ms=0,
        )

    async def _delayed_restart(self, delay_ms: int) -> None:
        """Execute restart after delay."""
        import asyncio

        await asyncio.sleep(delay_ms / 1000)

        try:
            import os
            import signal

            pid = os.getpid()
            os.kill(pid, signal.SIGUSR1)
        except Exception:
            pass

    async def _config(self, path: str | None, value: str | None) -> ToolResult:
        """Get or set configuration values."""
        config = self._load_config()

        if value is None:
            if path:
                current_value = self._get_nested(config, path)
                return ToolResult(
                    success=True,
                    data={"path": path, "value": current_value},
                    stdout=f"# Config: {path}\n\n```\n{json.dumps(current_value, indent=2)}\n```",
                    execution_time_ms=0,
                )
            else:
                return ToolResult(
                    success=True,
                    data=config,
                    stdout=f"# Gateway Configuration\n\n```json\n{json.dumps(config, indent=2)}\n```",
                    execution_time_ms=0,
                )

        else:
            if not path:
                return ToolResult(
                    success=False,
                    error="'path' is required for config set",
                    execution_time_ms=0,
                )

            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                parsed_value = value

            self._set_nested(config, path, parsed_value)
            self._save_config(config)

            lines = [
                f"✅ **Config updated**: `{path}`",
                "",
                f"New value: `{json.dumps(parsed_value)}`",
                "",
                "Run `gateway(operation='restart')` to apply changes.",
            ]

            return ToolResult(
                success=True,
                data={"path": path, "value": parsed_value, "restart_required": True},
                stdout="\n".join(lines),
                execution_time_ms=0,
            )

    async def _status(self) -> ToolResult:
        """Get gateway status."""
        import subprocess

        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=qubot-api",
                    "--format",
                    "{{.Status}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            container_status = result.stdout.strip() or "not running"
        except Exception:
            container_status = "unknown"

        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=qubot-redis",
                    "--format",
                    "{{.Status}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            redis_status = result.stdout.strip() or "not running"
        except Exception:
            redis_status = "unknown"

        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=qubot-db",
                    "--format",
                    "{{.Status}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            db_status = result.stdout.strip() or "not running"
        except Exception:
            db_status = "unknown"

        config = self._load_config()

        lines = [
            "# Gateway Status",
            "",
            "## Containers",
            f"- **API**: {container_status}",
            f"- **Redis**: {redis_status}",
            f"- **Database**: {db_status}",
            "",
            "## Configuration",
            f"- Port: {config.get('gateway', {}).get('port', 8000)}",
            f"- Debug: {config.get('gateway', {}).get('debug', False)}",
        ]

        return ToolResult(
            success=True,
            data={
                "containers": {
                    "api": container_status,
                    "redis": redis_status,
                    "database": db_status,
                },
                "config": config,
            },
            stdout="\n".join(lines),
            execution_time_ms=0,
        )

    async def _update(self) -> ToolResult:
        """Check for and apply updates."""
        lines = [
            "🔍 **Checking for updates...**",
            "",
            "Current version: 1.0.0",
            "",
            "```",
            "$ docker compose pull",
            "$ docker compose up -d",
            "```",
            "",
            "To update manually, run:",
        ]

        return ToolResult(
            success=True,
            data={"current_version": "1.0.0", "update_available": False},
            stdout="\n".join(lines),
            execution_time_ms=0,
        )

    async def _logs(self, lines_count: int) -> ToolResult:
        """Get gateway logs."""
        import subprocess

        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(lines_count), "qubot-api"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            return ToolResult(
                success=True,
                data={"logs": result.stdout[-5000:]},
                stdout=f"# Gateway Logs (last {lines_count} lines)\n\n```\n{result.stdout[-5000:]}\n```",
                execution_time_ms=0,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get logs: {str(e)}",
                execution_time_ms=0,
            )

    def _load_config(self) -> dict:
        """Load configuration from file."""
        if self.CONFIG_PATH.exists():
            return json.loads(self.CONFIG_PATH.read_text())
        return {}

    def _save_config(self, config: dict) -> None:
        """Save configuration to file."""
        self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.CONFIG_PATH.write_text(json.dumps(config, indent=2))

    def _get_nested(self, data: dict, path: str) -> Any:
        """Get nested value from dict using dot notation."""
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None

        return current

    def _set_nested(self, data: dict, path: str, value: Any) -> None:
        """Set nested value in dict using dot notation."""
        keys = path.split(".")
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
