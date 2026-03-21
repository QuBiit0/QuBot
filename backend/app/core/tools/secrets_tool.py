"""
Secrets Tool - Secure secret management for agents.
Gives agents the ability to store and retrieve sensitive data.
"""

import time
import re

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel
from app.services.secrets import secrets_vault


class SecretsTool(BaseTool):
    """
    Secure secret storage and retrieval.
    Agents can store API keys, tokens, and other sensitive data.
    Secrets are encrypted and can be referenced in other tools.

    Operations:
    - store: Store a new secret
    - retrieve: Retrieve a secret value
    - list: List all stored secrets (names only)
    - delete: Delete a secret
    - reference: Get a template reference for a secret

    Security:
    - Secrets are encrypted at rest
    - Values are never exposed in logs
    - Access requires appropriate permissions
    """

    name = "secrets"
    description = (
        "Securely store and retrieve sensitive data like API keys, tokens, and credentials. "
        "Use 'store' to save a new secret. "
        "Use 'retrieve' to get a secret value. "
        "Use 'list' to see all stored secrets. "
        "Use 'reference' to get a template for using secrets in other tools. "
        "Secrets are encrypted and access is logged for security."
    )
    category = ToolCategory.SYSTEM
    risk_level = ToolRiskLevel.DANGEROUS

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "operation": ToolParameter(
                name="operation",
                type="string",
                description="Operation: 'store', 'retrieve', 'list', 'delete', 'reference'",
                required=True,
                enum=["store", "retrieve", "list", "delete", "reference"],
            ),
            "name": ToolParameter(
                name="name",
                type="string",
                description="Unique name for the secret (e.g., 'openai_key', 'slack_token')",
                required=False,
                default=None,
            ),
            "value": ToolParameter(
                name="value",
                type="string",
                description="Secret value to store (for 'store' operation)",
                required=False,
                default=None,
            ),
            "category": ToolParameter(
                name="category",
                type="string",
                description="Category: 'api_key', 'credentials', 'token', 'certificate', 'password', 'secret_key', 'other'",
                required=False,
                default="api_key",
            ),
            "description": ToolParameter(
                name="description",
                type="string",
                description="Optional description of what this secret is for",
                required=False,
                default=None,
            ),
            "tags": ToolParameter(
                name="tags",
                type="string",
                description="Comma-separated tags for organization",
                required=False,
                default=None,
            ),
        }

    def _validate_config(self) -> None:
        self.require_auth = self.config.get("require_auth", True)

    def _validate_name(self, name: str) -> bool:
        """Validate secret name format"""
        if not name:
            return False
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
            return False
        if len(name) > 64:
            return False
        return True

    def _mask_value(self, value: str, visible: int = 4) -> str:
        """Mask a secret value"""
        if not value:
            return "****"
        if len(value) <= visible:
            return "*" * len(value)
        return value[:visible] + "*" * (len(value) - visible)

    async def _store(
        self,
        name: str,
        value: str,
        category: str,
        description: str | None,
        tags: str | None,
    ) -> ToolResult:
        """Store a new secret"""
        if not self._validate_name(name):
            return ToolResult(
                success=False,
                error="Invalid secret name. Use lowercase letters, numbers, hyphens, and underscores. Must start with a letter.",
            )

        if not value:
            return ToolResult(success=False, error="Secret value is required")

        if secrets_vault.exists(name):
            return ToolResult(
                success=False,
                error=f"Secret '{name}' already exists. Use 'update' or choose a different name.",
            )

        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        secrets_vault.set(
            name,
            value,
            metadata={
                "category": category,
                "description": description,
                "tags": tag_list,
            },
        )

        return ToolResult(
            success=True,
            data={
                "name": name,
                "category": category,
                "masked_value": self._mask_value(value),
            },
            stdout=f"Secret '{name}' stored successfully. Use reference: {{{{'secrets.{name}'}}}}",
        )

    async def _retrieve(self, name: str) -> ToolResult:
        """Retrieve a secret value"""
        if not name:
            return ToolResult(success=False, error="Secret name is required")

        value = secrets_vault.get(name)
        if value is None:
            return ToolResult(success=False, error=f"Secret '{name}' not found")

        metadata = secrets_vault.get_metadata(name) or {}

        return ToolResult(
            success=True,
            data={
                "name": name,
                "value": value,
                "category": metadata.get("category", "other"),
                "description": metadata.get("description"),
            },
            stdout=f"Retrieved secret '{name}'",
        )

    async def _list_secrets(self) -> ToolResult:
        """List all stored secrets"""
        keys = secrets_vault.list_keys()

        if not keys:
            return ToolResult(
                success=True,
                data={"secrets": [], "count": 0},
                stdout="No secrets stored",
            )

        secrets = []
        lines = ["Stored Secrets:\n"]

        for key in sorted(keys):
            metadata = secrets_vault.get_metadata(key) or {}
            value = secrets_vault.get(key) or ""
            category = metadata.get("category", "other")

            secrets.append(
                {
                    "name": key,
                    "category": category,
                    "description": metadata.get("description"),
                    "masked_value": self._mask_value(value),
                }
            )

            lines.append(f"- {key} [{category}]")
            if metadata.get("description"):
                lines.append(f"  {metadata['description']}")

        return ToolResult(
            success=True,
            data={"secrets": secrets, "count": len(secrets)},
            stdout="\n".join(lines),
        )

    async def _delete(self, name: str) -> ToolResult:
        """Delete a secret"""
        if not name:
            return ToolResult(success=False, error="Secret name is required")

        if not secrets_vault.exists(name):
            return ToolResult(success=False, error=f"Secret '{name}' not found")

        secrets_vault.delete(name)

        return ToolResult(
            success=True,
            data={"name": name},
            stdout=f"Secret '{name}' deleted",
        )

    async def _reference(self, name: str) -> ToolResult:
        """Get a template reference for a secret"""
        if not name:
            return ToolResult(success=False, error="Secret name is required")

        if not secrets_vault.exists(name):
            return ToolResult(success=False, error=f"Secret '{name}' not found")

        reference = f"{{{{ secrets.{name} }}}}"

        return ToolResult(
            success=True,
            data={
                "name": name,
                "reference": reference,
                "usage": f"Use {reference} in tool configurations to inject the secret value",
            },
            stdout=f"Reference for '{name}': {reference}",
        )

    async def execute(
        self,
        operation: str,
        name: str | None = None,
        value: str | None = None,
        category: str = "api_key",
        description: str | None = None,
        tags: str | None = None,
    ) -> ToolResult:
        start_time = time.time()

        try:
            match operation:
                case "store":
                    if not name:
                        return ToolResult(
                            success=False, error="name is required for store operation"
                        )
                    if not value:
                        return ToolResult(
                            success=False, error="value is required for store operation"
                        )
                    result = await self._store(name, value, category, description, tags)

                case "retrieve":
                    if not name:
                        return ToolResult(
                            success=False,
                            error="name is required for retrieve operation",
                        )
                    result = await self._retrieve(name)

                case "list":
                    result = await self._list_secrets()

                case "delete":
                    if not name:
                        return ToolResult(
                            success=False, error="name is required for delete operation"
                        )
                    result = await self._delete(name)

                case "reference":
                    if not name:
                        return ToolResult(
                            success=False,
                            error="name is required for reference operation",
                        )
                    result = await self._reference(name)

                case _:
                    result = ToolResult(
                        success=False, error=f"Unknown operation: {operation}"
                    )

            result.execution_time_ms = int((time.time() - start_time) * 1000)
            return result

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Secrets operation failed: {e}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
