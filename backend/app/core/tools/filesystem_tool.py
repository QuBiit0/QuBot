"""
Filesystem Tool - File operations with sandboxing
"""

import shutil
import time
from pathlib import Path

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


class FilesystemTool(BaseTool):
    """
    Tool for file system operations with sandboxing.

    All operations are restricted to a base directory (sandbox).
    Attempts to access files outside the sandbox will be blocked.
    """

    name = "filesystem"
    description = (
        "Read, write, and manage files in a sandboxed directory. "
        "Supports creating, reading, updating, deleting files and directories. "
        "All operations are restricted to a safe workspace directory."
    )
    category = ToolCategory.FILE
    risk_level = ToolRiskLevel.DANGEROUS

    # File size limits
    MAX_READ_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_WRITE_SIZE = 50 * 1024 * 1024  # 50MB

    # Allowed file extensions for write
    ALLOWED_EXTENSIONS = [
        # Text files
        ".txt",
        ".md",
        ".rst",
        ".json",
        ".yaml",
        ".yml",
        ".xml",
        ".csv",
        # Code files
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".html",
        ".css",
        ".scss",
        ".java",
        ".kt",
        ".swift",
        ".go",
        ".rs",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".rb",
        ".php",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        # Config files
        ".toml",
        ".ini",
        ".conf",
        ".cfg",
        ".properties",
        # Data files
        ".sql",
        ".graphql",
        ".proto",
        # Web
        ".vue",
        ".svelte",
        ".astro",
        # Documentation
        ".mdx",
        ".ipynb",
    ]

    # Blocked file patterns
    BLOCKED_PATTERNS = [
        ".env",
        ".env.",
        ".ssh",
        ".aws",
        ".docker",
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        ".htpasswd",
        ".netrc",
        ".pgpass",
        "credentials",
        "secrets",
        "password",
    ]

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "action": ToolParameter(
                name="action",
                type="string",
                description="File operation to perform",
                required=True,
                enum=[
                    "read",
                    "write",
                    "append",
                    "delete",
                    "list",
                    "mkdir",
                    "rmdir",
                    "exists",
                    "info",
                ],
            ),
            "path": ToolParameter(
                name="path",
                type="string",
                description="File or directory path (relative to workspace)",
                required=True,
            ),
            "content": ToolParameter(
                name="content",
                type="string",
                description="Content to write (for write/append actions)",
                required=False,
            ),
            "encoding": ToolParameter(
                name="encoding",
                type="string",
                description="File encoding",
                required=False,
                default="utf-8",
            ),
            "recursive": ToolParameter(
                name="recursive",
                type="boolean",
                description="Recursively list or delete directories",
                required=False,
                default=False,
            ),
        }

    def _validate_config(self) -> None:
        """Validate tool configuration"""
        # Base directory (sandbox root)
        self.base_dir = self.config.get("base_dir", "/tmp/qubot_workspace")

        # Ensure base directory exists
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)

        # Resolve to absolute path
        self.base_dir = str(Path(self.base_dir).resolve())

    def _resolve_path(self, path: str) -> tuple[Path | None, str | None]:
        """
        Resolve path within sandbox.

        Returns:
            Tuple of (resolved_path, error_message)
        """
        # Normalize path
        path = path.strip()

        # Block absolute paths
        if path.startswith("/") and not path.startswith(self.base_dir):
            path = path.lstrip("/")

        # Resolve to absolute path
        try:
            full_path = Path(self.base_dir) / path
            resolved = full_path.resolve()

            # Security check: ensure path is within base_dir
            if not str(resolved).startswith(self.base_dir):
                return None, "Access denied: path outside workspace"

            return resolved, None

        except Exception as e:
            return None, f"Invalid path: {str(e)}"

    def _is_blocked_file(self, path: Path) -> bool:
        """Check if file is in blocked patterns"""
        name = path.name.lower()

        for pattern in self.BLOCKED_PATTERNS:
            if pattern in name:
                return True

        return False

    def _validate_write_extension(self, path: Path) -> bool:
        """Check if file extension is allowed for writing"""
        ext = path.suffix.lower()
        return ext in self.ALLOWED_EXTENSIONS

    async def execute(
        self,
        action: str,
        path: str,
        content: str | None = None,
        encoding: str = "utf-8",
        recursive: bool = False,
    ) -> ToolResult:
        """
        Execute filesystem operation.

        Args:
            action: Operation type (read, write, append, delete, list, mkdir, rmdir, exists, info)
            path: File or directory path
            content: Content for write/append
            encoding: File encoding
            recursive: Recursive operations

        Returns:
            ToolResult with operation outcome
        """
        start_time = time.time()

        # Resolve path
        resolved_path, error = self._resolve_path(path)
        if error:
            return ToolResult(success=False, error=error)

        # Check blocked files
        if self._is_blocked_file(resolved_path):
            return ToolResult(
                success=False,
                error=f"Access denied: file '{resolved_path.name}' is in blocked list",
            )

        try:
            if action == "read":
                return await self._action_read(resolved_path, encoding)
            elif action == "write":
                return await self._action_write(resolved_path, content, encoding)
            elif action == "append":
                return await self._action_append(resolved_path, content, encoding)
            elif action == "delete":
                return await self._action_delete(resolved_path)
            elif action == "list":
                return await self._action_list(resolved_path, recursive)
            elif action == "mkdir":
                return await self._action_mkdir(resolved_path)
            elif action == "rmdir":
                return await self._action_rmdir(resolved_path, recursive)
            elif action == "exists":
                return await self._action_exists(resolved_path)
            elif action == "info":
                return await self._action_info(resolved_path)
            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Filesystem error: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

    async def _action_read(self, path: Path, encoding: str) -> ToolResult:
        """Read file content"""
        if not path.exists():
            return ToolResult(success=False, error=f"File not found: {path.name}")

        if path.is_dir():
            return ToolResult(success=False, error=f"Path is a directory: {path.name}")

        # Check size
        size = path.stat().st_size
        if size > self.MAX_READ_SIZE:
            return ToolResult(
                success=False,
                error=f"File too large ({size} bytes, max {self.MAX_READ_SIZE})",
            )

        try:
            content = path.read_text(encoding=encoding)
            return ToolResult(
                success=True,
                data={
                    "path": str(path),
                    "size": size,
                    "lines": len(content.splitlines()),
                },
                stdout=content,
                execution_time_ms=0,
            )
        except UnicodeDecodeError:
            # Try binary read
            content = path.read_bytes()
            return ToolResult(
                success=True,
                data={
                    "path": str(path),
                    "size": size,
                    "binary": True,
                },
                stdout=f"[Binary file: {size} bytes]",
                execution_time_ms=0,
            )

    async def _action_write(
        self, path: Path, content: str | None, encoding: str
    ) -> ToolResult:
        """Write file content"""
        if content is None:
            return ToolResult(success=False, error="Content required for write action")

        # Check extension
        if not self._validate_write_extension(path):
            return ToolResult(
                success=False,
                error=f"File extension not allowed for writing. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}",
            )

        # Check size
        if len(content.encode(encoding)) > self.MAX_WRITE_SIZE:
            return ToolResult(
                success=False,
                error=f"Content too large (max {self.MAX_WRITE_SIZE} bytes)",
            )

        # Create parent directories
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        path.write_text(content, encoding=encoding)

        return ToolResult(
            success=True,
            data={
                "path": str(path),
                "size": len(content),
                "lines": len(content.splitlines()),
                "action": "write",
            },
            execution_time_ms=0,
        )

    async def _action_append(
        self, path: Path, content: str | None, encoding: str
    ) -> ToolResult:
        """Append to file"""
        if content is None:
            return ToolResult(success=False, error="Content required for append action")

        # Check if file exists
        if path.exists() and not self._validate_write_extension(path):
            return ToolResult(
                success=False,
                error="File extension not allowed",
            )

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Append
        with open(path, "a", encoding=encoding) as f:
            f.write(content)

        new_size = path.stat().st_size

        return ToolResult(
            success=True,
            data={
                "path": str(path),
                "size": new_size,
                "action": "append",
            },
            execution_time_ms=0,
        )

    async def _action_delete(self, path: Path) -> ToolResult:
        """Delete file"""
        if not path.exists():
            return ToolResult(success=False, error=f"File not found: {path.name}")

        if path.is_dir():
            return ToolResult(
                success=False, error="Use rmdir action to delete directories"
            )

        path.unlink()

        return ToolResult(
            success=True,
            data={"path": str(path), "action": "delete"},
            execution_time_ms=0,
        )

    async def _action_list(self, path: Path, recursive: bool) -> ToolResult:
        """List directory contents"""
        if not path.exists():
            return ToolResult(success=False, error=f"Directory not found: {path.name}")

        if not path.is_dir():
            return ToolResult(
                success=False, error=f"Path is not a directory: {path.name}"
            )

        items = []

        if recursive:
            for item in path.rglob("*"):
                rel_path = item.relative_to(self.base_dir)
                items.append(
                    {
                        "path": str(rel_path),
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    }
                )
        else:
            for item in path.iterdir():
                rel_path = item.relative_to(self.base_dir)
                items.append(
                    {
                        "path": str(rel_path),
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    }
                )

        return ToolResult(
            success=True,
            data={
                "path": str(path),
                "items": items,
                "count": len(items),
            },
            execution_time_ms=0,
        )

    async def _action_mkdir(self, path: Path) -> ToolResult:
        """Create directory"""
        path.mkdir(parents=True, exist_ok=True)

        return ToolResult(
            success=True,
            data={"path": str(path), "action": "mkdir"},
            execution_time_ms=0,
        )

    async def _action_rmdir(self, path: Path, recursive: bool) -> ToolResult:
        """Remove directory"""
        if not path.exists():
            return ToolResult(success=False, error=f"Directory not found: {path.name}")

        if not path.is_dir():
            return ToolResult(
                success=False, error=f"Path is not a directory: {path.name}"
            )

        if recursive:
            shutil.rmtree(path)
        else:
            path.rmdir()

        return ToolResult(
            success=True,
            data={"path": str(path), "action": "rmdir", "recursive": recursive},
            execution_time_ms=0,
        )

    async def _action_exists(self, path: Path) -> ToolResult:
        """Check if path exists"""
        exists = path.exists()

        return ToolResult(
            success=True,
            data={
                "path": str(path),
                "exists": exists,
                "type": "directory"
                if exists and path.is_dir()
                else ("file" if exists else None),
            },
            execution_time_ms=0,
        )

    async def _action_info(self, path: Path) -> ToolResult:
        """Get file/directory info"""
        if not path.exists():
            return ToolResult(success=False, error=f"Path not found: {path.name}")

        stat = path.stat()

        return ToolResult(
            success=True,
            data={
                "path": str(path),
                "type": "directory" if path.is_dir() else "file",
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "permissions": oct(stat.st_mode)[-3:],
            },
            execution_time_ms=0,
        )
