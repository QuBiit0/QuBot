# Qubot — Tools System

> **Module**: `backend/app/tools_impl/`
> **Service**: `backend/app/services/tool_service.py`

---

## 1. Overview

The tools system allows agents to take real-world actions: call APIs, run shell commands, browse the web, read/write files, and schedule tasks. All tool execution goes through a unified interface with permission checking, timeouts, and logging.

```
AgentExecutionService
    │
    │ tool_call = LlmToolCall(id, name, arguments)
    │
    ▼
execute_tool(agent, tool, arguments)
    ├── Check: agent has this tool assigned (AgentTool record exists)
    ├── Check: permission level sufficient for dangerous tools
    ├── Resolve tool name → Tool DB record → BaseTool implementation
    ├── asyncio.wait_for(impl.execute(agent, **arguments), timeout=60s)
    ├── On success: return ToolResult(success=True, data=...)
    └── On error/timeout: return ToolResult(success=False, error=...)
```

---

## 2. Base Interface

```python
# backend/app/tools_impl/base.py
from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel


class ToolResult(BaseModel):
    """Standardized return value from all tool executions."""
    success: bool
    data: Optional[Any] = None      # Parsed response data
    error: Optional[str] = None     # Human-readable error if success=False
    metadata: dict = {}             # Extra info: duration_ms, status_code, etc.


class BaseTool(ABC):
    """Interface that all tool implementations must follow."""

    name: str           # Must match Tool.name in DB
    description: str    # Human-readable (not used at runtime, but for documentation)

    @abstractmethod
    async def execute(self, agent: "Agent", **kwargs) -> ToolResult:
        """
        Execute the tool with given arguments.

        Args:
            agent: The agent executing this tool (for permission context)
            **kwargs: Arguments matching the tool's input_schema

        Returns:
            ToolResult — always returns, never raises
        """
        ...

    def to_function_schema(self, tool_db: "Tool") -> dict:
        """
        Convert to OpenAI function_calling schema format.
        Uses tool_db.input_schema (JSON Schema) for parameters.
        """
        return {
            "type": "function",
            "function": {
                "name": tool_db.name.replace(" ", "_").lower(),
                "description": tool_db.description,
                "parameters": tool_db.input_schema or {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
```

---

## 3. Tool Registry

```python
# backend/app/tools_impl/registry.py
from ..models.enums import ToolTypeEnum
from ..models.tool import Tool
from .base import BaseTool
from .http_api import HttpApiTool
from .shell import SystemShellTool
from .browser import WebBrowserTool
from .filesystem import FilesystemTool
from .scheduler import SchedulerTool
from .custom import CustomTool

TOOL_REGISTRY: dict[ToolTypeEnum, type[BaseTool]] = {
    ToolTypeEnum.HTTP_API: HttpApiTool,
    ToolTypeEnum.SYSTEM_SHELL: SystemShellTool,
    ToolTypeEnum.WEB_BROWSER: WebBrowserTool,
    ToolTypeEnum.FILESYSTEM: FilesystemTool,
    ToolTypeEnum.SCHEDULER: SchedulerTool,
    ToolTypeEnum.CUSTOM: CustomTool,
}

def get_tool_impl(tool: Tool) -> BaseTool:
    """Factory: returns instantiated tool implementation for given Tool record."""
    impl_class = TOOL_REGISTRY.get(tool.type)
    if not impl_class:
        raise ValueError(f"No implementation for tool type: {tool.type}")
    return impl_class(tool_config=tool.config)
```

---

## 4. Permission Enforcement

```python
# backend/app/tools_impl/executor.py
import asyncio
import time
from ..models.agent import Agent, AgentTool
from ..models.tool import Tool
from ..models.enums import PermissionEnum
from .registry import get_tool_impl
from .base import ToolResult

TOOL_TIMEOUT_SECONDS = 60.0

async def execute_tool(
    agent: Agent,
    tool: Tool,
    arguments: dict,
) -> ToolResult:
    """
    Main entry point for tool execution.
    Checks permissions, resolves implementation, executes with timeout.
    """

    # Find the agent-tool association
    agent_tool = next(
        (at for at in agent.tools if at.tool_id == tool.id),
        None
    )

    if not agent_tool:
        return ToolResult(
            success=False,
            error=f"Tool '{tool.name}' is not assigned to agent '{agent.name}'"
        )

    # Dangerous tools require explicit DANGEROUS permission
    if tool.is_dangerous and agent_tool.permissions != PermissionEnum.DANGEROUS:
        return ToolResult(
            success=False,
            error=f"Tool '{tool.name}' is marked dangerous and requires DANGEROUS permission level"
        )

    # Read-only tools can't be called with write arguments (enforced by schema, but double-check)
    if agent_tool.permissions == PermissionEnum.READ_ONLY:
        method = arguments.get("method", "GET").upper()
        if method in ("POST", "PUT", "PATCH", "DELETE"):
            return ToolResult(
                success=False,
                error=f"Agent has READ_ONLY permission for '{tool.name}', cannot use {method} method"
            )

    # Resolve and execute implementation
    try:
        impl = get_tool_impl(tool)
        start_time = time.monotonic()

        result = await asyncio.wait_for(
            impl.execute(agent=agent, **arguments),
            timeout=TOOL_TIMEOUT_SECONDS
        )

        duration_ms = int((time.monotonic() - start_time) * 1000)
        result.metadata["duration_ms"] = duration_ms
        return result

    except asyncio.TimeoutError:
        return ToolResult(
            success=False,
            error=f"Tool execution timed out after {TOOL_TIMEOUT_SECONDS}s",
            metadata={"timeout": True}
        )
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Tool execution error: {str(e)}"
        )
```

---

## 5. HTTP API Tool

```python
# backend/app/tools_impl/http_api.py
import httpx
from .base import BaseTool, ToolResult
import os


class HttpApiTool(BaseTool):
    """
    Makes HTTP requests to external APIs.

    Config fields:
        base_url (str): Base URL for all requests
        default_headers (dict): Headers added to every request
        auth_type (str): "none" | "bearer" | "api_key" | "basic"
        auth_env_ref (str): ENV VAR NAME containing the credential
        auth_header (str): Header name for api_key auth (default: X-API-Key)
        timeout (int): Request timeout in seconds (default: 30)
        allowed_domains (list[str]): Whitelist of allowed domains (security)
    """

    name = "http_api"
    description = "Make HTTP requests to external APIs"

    def __init__(self, tool_config: dict):
        self.config = tool_config

    async def execute(self, agent, **kwargs) -> ToolResult:
        method = kwargs.get("method", "GET").upper()
        path = kwargs.get("path", "/")
        query_params = kwargs.get("query_params", {})
        body = kwargs.get("body")
        headers_override = kwargs.get("headers", {})

        base_url = self.config.get("base_url", "")
        if not base_url:
            return ToolResult(success=False, error="Tool has no base_url configured")

        # Security: check allowed domains
        allowed_domains = self.config.get("allowed_domains", [])
        if allowed_domains:
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            if parsed.hostname not in allowed_domains:
                return ToolResult(
                    success=False,
                    error=f"Domain '{parsed.hostname}' not in allowed list: {allowed_domains}"
                )

        url = base_url.rstrip("/") + "/" + path.lstrip("/")

        # Build headers
        headers = {**self.config.get("default_headers", {}), **headers_override}

        # Authentication
        auth_type = self.config.get("auth_type", "none")
        auth_env_ref = self.config.get("auth_env_ref", "")
        if auth_type != "none" and auth_env_ref:
            credential = os.getenv(auth_env_ref, "")
            if auth_type == "bearer":
                headers["Authorization"] = f"Bearer {credential}"
            elif auth_type == "api_key":
                header_name = self.config.get("auth_header", "X-API-Key")
                headers[header_name] = credential
            elif auth_type == "basic":
                import base64
                encoded = base64.b64encode(credential.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"

        timeout = self.config.get("timeout", 30)

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=query_params or None,
                    json=body if body else None,
                    headers=headers,
                )

            # Parse response body
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    response_body = response.json()
                except Exception:
                    response_body = response.text
            else:
                response_body = response.text[:10000]  # Truncate large non-JSON responses

            return ToolResult(
                success=response.is_success,
                data={
                    "status_code": response.status_code,
                    "body": response_body,
                    "headers": dict(response.headers),
                },
                error=None if response.is_success else f"HTTP {response.status_code}: {response.text[:200]}",
                metadata={"url": url, "method": method}
            )

        except httpx.TimeoutException:
            return ToolResult(success=False, error=f"Request timed out after {timeout}s")
        except httpx.ConnectError as e:
            return ToolResult(success=False, error=f"Connection failed: {str(e)}")
        except Exception as e:
            return ToolResult(success=False, error=f"Request failed: {str(e)}")
```

---

## 6. System Shell Tool

```python
# backend/app/tools_impl/shell.py
import asyncio
import shlex
from .base import BaseTool, ToolResult


class SystemShellTool(BaseTool):
    """
    Executes shell commands in a sandboxed environment.

    Config fields:
        allowed_commands (list[str]): Whitelist of allowed base commands
        working_directory (str): Base directory for execution (jail)
        timeout_seconds (int): Max execution time (default: 30)
        env_passthrough (list[str]): ENV vars to pass to subprocess
    """

    name = "system_shell"
    description = "Execute shell commands. Only whitelisted commands are allowed."

    DANGEROUS_PATTERNS = [
        "rm -rf", "mkfs", "dd if=", "> /dev/", "chmod 777",
        "; rm", "&& rm", "| rm", "eval ", "exec ", "$(", "`",
        "../", "~/"
    ]

    def __init__(self, tool_config: dict):
        self.config = tool_config

    async def execute(self, agent, **kwargs) -> ToolResult:
        command = kwargs.get("command", "")
        args = kwargs.get("args", [])
        working_dir = kwargs.get("working_directory", self.config.get("working_directory", "/tmp"))

        if not command:
            return ToolResult(success=False, error="No command provided")

        # Security: whitelist check
        allowed_commands = self.config.get("allowed_commands", [])
        if allowed_commands and command not in allowed_commands:
            return ToolResult(
                success=False,
                error=f"Command '{command}' not in allowed list: {allowed_commands}"
            )

        # Security: dangerous pattern check
        full_command = command + " " + " ".join(str(a) for a in args)
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in full_command.lower():
                return ToolResult(
                    success=False,
                    error=f"Command contains dangerous pattern: '{pattern}'"
                )

        # Security: prevent path traversal
        if ".." in working_dir or working_dir.startswith("~"):
            return ToolResult(success=False, error="Invalid working directory")

        timeout = self.config.get("timeout_seconds", 30)

        try:
            # Build command list
            cmd_list = [command] + [str(a) for a in args]

            proc = await asyncio.create_subprocess_exec(
                *cmd_list,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return ToolResult(
                    success=False,
                    error=f"Command timed out after {timeout}s"
                )

            stdout_text = stdout.decode("utf-8", errors="replace")[:50000]
            stderr_text = stderr.decode("utf-8", errors="replace")[:5000]

            return ToolResult(
                success=proc.returncode == 0,
                data={
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "exit_code": proc.returncode,
                },
                error=stderr_text if proc.returncode != 0 else None,
                metadata={"command": command, "working_directory": working_dir}
            )

        except FileNotFoundError:
            return ToolResult(success=False, error=f"Command not found: '{command}'")
        except PermissionError:
            return ToolResult(success=False, error=f"Permission denied executing '{command}'")
        except Exception as e:
            return ToolResult(success=False, error=f"Execution failed: {str(e)}")
```

---

## 7. Web Browser Tool

```python
# backend/app/tools_impl/browser.py
import httpx
from bs4 import BeautifulSoup
from .base import BaseTool, ToolResult


class WebBrowserTool(BaseTool):
    """
    Fetches and parses web pages. Does NOT execute JavaScript.
    Uses httpx + BeautifulSoup for static HTML.

    Config fields:
        timeout (int): Request timeout seconds (default: 15)
        user_agent (str): User-Agent header
        max_content_length (int): Max response bytes to process (default: 100000)
    """

    name = "web_browser"
    description = "Fetch web pages and extract text content, links, or structured data."

    def __init__(self, tool_config: dict):
        self.config = tool_config

    async def execute(self, agent, **kwargs) -> ToolResult:
        url = kwargs.get("url", "")
        extract_type = kwargs.get("extract_type", "text")  # text | html | links | title

        if not url:
            return ToolResult(success=False, error="No URL provided")

        # Basic URL validation
        if not url.startswith(("http://", "https://")):
            return ToolResult(success=False, error="URL must start with http:// or https://")

        timeout = self.config.get("timeout", 15)
        user_agent = self.config.get("user_agent", "Qubot/1.0 (AI Agent Browser)")
        max_length = self.config.get("max_content_length", 100000)

        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                headers=headers
            ) as client:
                response = await client.get(url)

            if not response.is_success:
                return ToolResult(
                    success=False,
                    error=f"HTTP {response.status_code}",
                    data={"status_code": response.status_code}
                )

            content = response.content[:max_length]
            soup = BeautifulSoup(content, "html.parser")

            # Remove scripts and styles
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            title = soup.title.string if soup.title else "No title"

            if extract_type == "text":
                text = soup.get_text(separator="\n", strip=True)
                # Collapse multiple blank lines
                import re
                text = re.sub(r'\n{3,}', '\n\n', text)[:10000]
                return ToolResult(
                    success=True,
                    data={"title": title, "text": text, "url": str(response.url)},
                    metadata={"status_code": response.status_code}
                )

            elif extract_type == "links":
                links = []
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    text = a.get_text(strip=True)
                    if href.startswith("http"):
                        links.append({"text": text[:100], "url": href})
                return ToolResult(
                    success=True,
                    data={"title": title, "links": links[:50], "url": str(response.url)}
                )

            elif extract_type == "html":
                return ToolResult(
                    success=True,
                    data={"title": title, "html": str(soup)[:10000], "url": str(response.url)}
                )

            else:
                text = soup.get_text(separator="\n", strip=True)[:10000]
                return ToolResult(
                    success=True,
                    data={"title": title, "text": text, "url": str(response.url)}
                )

        except httpx.TimeoutException:
            return ToolResult(success=False, error=f"Request timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to fetch URL: {str(e)}")
```

---

## 8. Filesystem Tool

```python
# backend/app/tools_impl/filesystem.py
import os
from pathlib import Path
from .base import BaseTool, ToolResult


class FilesystemTool(BaseTool):
    """
    Read/write files within a sandboxed directory.

    Config fields:
        base_directory (str): All operations are jailed to this path
        allowed_extensions (list[str]): Allowed file extensions
        max_file_size_bytes (int): Max file size for reads/writes (default: 1MB)
    """

    name = "filesystem"
    description = "Read, write, list, or delete files within the workspace directory."

    def __init__(self, tool_config: dict):
        self.config = tool_config

    def _safe_path(self, path: str) -> Path | None:
        """Resolve path and ensure it's within base_directory (jail)."""
        base_dir = Path(self.config.get("base_directory", "/workspace")).resolve()
        try:
            full_path = (base_dir / path.lstrip("/")).resolve()
            # Ensure the resolved path is within base_dir (prevents traversal)
            full_path.relative_to(base_dir)
            return full_path
        except (ValueError, RuntimeError):
            return None

    async def execute(self, agent, **kwargs) -> ToolResult:
        operation = kwargs.get("operation", "read")
        path = kwargs.get("path", "")
        content = kwargs.get("content")

        if not path:
            return ToolResult(success=False, error="No path provided")

        safe_path = self._safe_path(path)
        if not safe_path:
            return ToolResult(
                success=False,
                error=f"Path '{path}' is outside the allowed workspace directory"
            )

        # Extension check (for write/read)
        if operation in ("read", "write"):
            allowed_ext = self.config.get("allowed_extensions", [])
            if allowed_ext and safe_path.suffix not in allowed_ext:
                return ToolResult(
                    success=False,
                    error=f"File extension '{safe_path.suffix}' not allowed. Allowed: {allowed_ext}"
                )

        max_size = self.config.get("max_file_size_bytes", 1048576)

        if operation == "read":
            if not safe_path.exists():
                return ToolResult(success=False, error=f"File not found: {path}")
            if safe_path.stat().st_size > max_size:
                return ToolResult(success=False, error=f"File too large (max {max_size} bytes)")
            file_content = safe_path.read_text(encoding="utf-8", errors="replace")
            return ToolResult(
                success=True,
                data={"path": str(path), "content": file_content, "size_bytes": len(file_content)}
            )

        elif operation == "write":
            if content is None:
                return ToolResult(success=False, error="No content provided for write")
            if len(content) > max_size:
                return ToolResult(success=False, error=f"Content too large (max {max_size} bytes)")
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(str(content), encoding="utf-8")
            return ToolResult(
                success=True,
                data={"path": str(path), "bytes_written": len(content)}
            )

        elif operation == "list":
            target = safe_path if safe_path.is_dir() else safe_path.parent
            if not target.exists():
                return ToolResult(success=False, error=f"Directory not found: {path}")
            entries = []
            for entry in sorted(target.iterdir())[:100]:
                entries.append({
                    "name": entry.name,
                    "type": "dir" if entry.is_dir() else "file",
                    "size_bytes": entry.stat().st_size if entry.is_file() else 0
                })
            return ToolResult(success=True, data={"path": str(path), "entries": entries})

        elif operation == "delete":
            if not safe_path.exists():
                return ToolResult(success=False, error=f"File not found: {path}")
            if safe_path.is_dir():
                return ToolResult(success=False, error="Cannot delete directories (only files)")
            safe_path.unlink()
            return ToolResult(success=True, data={"deleted": str(path)})

        else:
            return ToolResult(success=False, error=f"Unknown operation: {operation}")
```

---

## 9. Scheduler Tool

```python
# backend/app/tools_impl/scheduler.py
from datetime import datetime, timedelta
from .base import BaseTool, ToolResult


class SchedulerTool(BaseTool):
    """
    Creates future tasks in the system.
    Tasks are picked up by the orchestrator when their scheduled_for time arrives.

    Config fields:
        max_delay_seconds (int): Maximum allowed scheduling delay
    """

    name = "scheduler"
    description = "Schedule a task to be executed in the future. Provide delay_seconds OR cron_expression."

    def __init__(self, tool_config: dict, session=None):
        self.config = tool_config
        self.session = session  # Injected at execution time

    async def execute(self, agent, **kwargs) -> ToolResult:
        task_title = kwargs.get("task_title", "")
        task_description = kwargs.get("task_description", "")
        delay_seconds = kwargs.get("delay_seconds")
        domain_hint = kwargs.get("domain_hint")
        priority = kwargs.get("priority", "MEDIUM")

        if not task_title:
            return ToolResult(success=False, error="task_title is required")

        max_delay = self.config.get("max_delay_seconds", 86400)

        if delay_seconds is not None:
            if delay_seconds > max_delay:
                return ToolResult(
                    success=False,
                    error=f"Delay {delay_seconds}s exceeds maximum allowed {max_delay}s"
                )
            scheduled_for = datetime.utcnow() + timedelta(seconds=delay_seconds)
        else:
            scheduled_for = datetime.utcnow() + timedelta(minutes=1)  # Default: 1 minute

        # Create the task in DB
        from ..models.task import Task
        from ..models.enums import TaskStatusEnum, PriorityEnum, DomainEnum

        task = Task(
            title=task_title,
            description=task_description or f"Scheduled task: {task_title}",
            status=TaskStatusEnum.BACKLOG,
            priority=PriorityEnum[priority.upper()] if priority else PriorityEnum.MEDIUM,
            domain_hint=DomainEnum[domain_hint.upper()] if domain_hint else None,
            created_by="scheduler_tool",
            scheduled_for=scheduled_for,
        )
        self.session.add(task)
        await self.session.flush()

        return ToolResult(
            success=True,
            data={
                "task_id": str(task.id),
                "task_title": task_title,
                "scheduled_for": scheduled_for.isoformat(),
                "delay_seconds": delay_seconds
            }
        )
```

---

## 10. Custom Tool

```python
# backend/app/tools_impl/custom.py
from .base import BaseTool, ToolResult
from .http_api import HttpApiTool


class CustomTool(BaseTool):
    """
    User-defined tools created via the UI.
    Currently dispatches to HTTP_API internally.
    Future: support webhook-based dispatch, code execution, etc.
    """

    name = "custom"
    description = "Custom tool defined by the user."

    def __init__(self, tool_config: dict):
        self.config = tool_config
        dispatch_to = tool_config.get("dispatch_to", "http_api")
        if dispatch_to == "http_api":
            self._impl = HttpApiTool(tool_config)
        else:
            self._impl = None

    async def execute(self, agent, **kwargs) -> ToolResult:
        if not self._impl:
            return ToolResult(
                success=False,
                error=f"Custom tool dispatch type not supported: {self.config.get('dispatch_to')}"
            )
        return await self._impl.execute(agent, **kwargs)
```

---

## 11. Tool Input Schemas (JSON Schema Examples)

### HTTP API Tool Input Schema
```json
{
  "type": "object",
  "properties": {
    "method": {
      "type": "string",
      "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
      "description": "HTTP method"
    },
    "path": {
      "type": "string",
      "description": "URL path relative to base_url (e.g., /users/123)"
    },
    "query_params": {
      "type": "object",
      "description": "Query string parameters as key-value pairs"
    },
    "body": {
      "type": "object",
      "description": "Request body for POST/PUT/PATCH"
    }
  },
  "required": ["method", "path"]
}
```

### Shell Tool Input Schema
```json
{
  "type": "object",
  "properties": {
    "command": {
      "type": "string",
      "description": "The command to execute (must be in allowed list)"
    },
    "args": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Command arguments"
    },
    "working_directory": {
      "type": "string",
      "description": "Directory to run command in (must be within workspace)"
    }
  },
  "required": ["command"]
}
```

### Web Browser Tool Input Schema
```json
{
  "type": "object",
  "properties": {
    "url": {
      "type": "string",
      "description": "Full URL to fetch (must start with http:// or https://)"
    },
    "extract_type": {
      "type": "string",
      "enum": ["text", "links", "html", "title"],
      "description": "What to extract: text (default), links, html, or title"
    }
  },
  "required": ["url"]
}
```

### Filesystem Tool Input Schema
```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["read", "write", "list", "delete"],
      "description": "File operation to perform"
    },
    "path": {
      "type": "string",
      "description": "File or directory path (relative to workspace)"
    },
    "content": {
      "type": "string",
      "description": "Content to write (only for write operation)"
    }
  },
  "required": ["operation", "path"]
}
```

---

## 12. Security Summary

| Tool | Security Measures |
|------|------------------|
| HTTP API | Domain whitelist, no localhost, bearer/key auth stored as env refs |
| Shell | Command whitelist, dangerous pattern blacklist, path restriction, timeout |
| Browser | Max content length limit, no JS execution, safe URL validation |
| Filesystem | Path traversal protection, directory jail, extension allowlist, size limit |
| Scheduler | Max delay limit, DB insertion only (no direct execution) |
| All | asyncio.wait_for timeout (60s), never raises (always returns ToolResult) |

---

## 13. Infrastructure Control Tools (VPS / Docker)

Qubot is designed to optionally act as a **full control plane for the infrastructure it runs on**. With the tools below, an agent can manage Docker containers, monitor system resources, deploy services, and administer the VPS — all through natural language requests from the user.

> **Security model**: These tools require `PermissionEnum.DANGEROUS` on `AgentTool`. Only agents explicitly granted this permission can use them. They should only be assigned to a trusted DevOps/SysAdmin agent.

---

### `DockerTool`

Manages Docker containers and images on the host via the Docker Unix socket or TCP API.

**`ToolTypeEnum.DOCKER`** — add to enum.

**Config:**
```json
{
  "socket_path": "/var/run/docker.sock",
  "allowed_operations": ["list", "start", "stop", "restart", "logs", "inspect", "pull"],
  "forbidden_container_names": ["qubot_postgres", "qubot_redis"]
}
```

**Input schema:**
```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["list_containers", "start", "stop", "restart", "logs", "inspect", "pull_image", "list_images"],
      "description": "Docker operation to perform"
    },
    "container_name": { "type": "string", "description": "Container name or ID" },
    "image": { "type": "string", "description": "Image name for pull operations" },
    "tail_lines": { "type": "integer", "default": 100, "description": "Number of log lines to return" }
  },
  "required": ["operation"]
}
```

**`tools_impl/docker_tool.py` (implementation sketch):**
```python
import docker
from app.tools_impl.base import BaseTool, ToolResult

class DockerTool(BaseTool):
    name = "docker"
    description = (
        "Manage Docker containers on this server. Can list, start, stop, restart containers, "
        "fetch logs, inspect container state, and pull new images."
    )

    async def execute(self, agent, **kwargs) -> ToolResult:
        operation = kwargs.get("operation")
        container_name = kwargs.get("container_name", "")
        config = self._get_config()

        # Security: block operations on forbidden containers
        if container_name in config.get("forbidden_container_names", []):
            return ToolResult(success=False, error=f"Operation on '{container_name}' is not allowed.")

        # Security: block operations not in allowlist
        if operation not in config.get("allowed_operations", []):
            return ToolResult(success=False, error=f"Operation '{operation}' is not permitted.")

        client = docker.from_env()
        try:
            if operation == "list_containers":
                containers = client.containers.list(all=True)
                return ToolResult(success=True, data=[
                    {"name": c.name, "status": c.status, "image": c.image.tags}
                    for c in containers
                ])
            elif operation == "start":
                client.containers.get(container_name).start()
                return ToolResult(success=True, data={"started": container_name})
            elif operation == "stop":
                client.containers.get(container_name).stop()
                return ToolResult(success=True, data={"stopped": container_name})
            elif operation == "restart":
                client.containers.get(container_name).restart()
                return ToolResult(success=True, data={"restarted": container_name})
            elif operation == "logs":
                logs = client.containers.get(container_name).logs(
                    tail=kwargs.get("tail_lines", 100)
                ).decode()
                return ToolResult(success=True, data={"logs": logs})
            elif operation == "pull_image":
                client.images.pull(kwargs.get("image", ""))
                return ToolResult(success=True, data={"pulled": kwargs.get("image")})
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")
        except docker.errors.NotFound:
            return ToolResult(success=False, error=f"Container '{container_name}' not found.")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**Requirement:** Add to `requirements.txt`:
```
docker>=7.0.0    # docker-py SDK
```

**docker-compose.yml** — mount socket for the api container:
```yaml
api:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro   # ro = read operations only unless write needed
```

---

### `SystemMonitorTool`

Reads CPU, RAM, disk, network, and running process metrics from the host system.

**`ToolTypeEnum.SYSTEM_MONITOR`** — add to enum.

**Config:** `{}` (no config needed — reads host metrics via psutil)

**Input schema:**
```json
{
  "type": "object",
  "properties": {
    "metric": {
      "type": "string",
      "enum": ["cpu", "memory", "disk", "network", "processes", "all"],
      "description": "Which system metric to retrieve"
    }
  },
  "required": ["metric"]
}
```

**`tools_impl/system_monitor.py`:**
```python
import psutil
from app.tools_impl.base import BaseTool, ToolResult

class SystemMonitorTool(BaseTool):
    name = "system_monitor"
    description = (
        "Read real-time system metrics: CPU usage, RAM, disk space, "
        "network I/O, and running processes. Use to monitor server health."
    )

    async def execute(self, agent, **kwargs) -> ToolResult:
        metric = kwargs.get("metric", "all")
        data = {}

        if metric in ("cpu", "all"):
            data["cpu"] = {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
            }
        if metric in ("memory", "all"):
            mem = psutil.virtual_memory()
            data["memory"] = {
                "total_gb": round(mem.total / 1e9, 2),
                "used_gb": round(mem.used / 1e9, 2),
                "percent": mem.percent,
            }
        if metric in ("disk", "all"):
            disk = psutil.disk_usage("/")
            data["disk"] = {
                "total_gb": round(disk.total / 1e9, 2),
                "used_gb": round(disk.used / 1e9, 2),
                "percent": disk.percent,
            }
        if metric in ("network", "all"):
            net = psutil.net_io_counters()
            data["network"] = {
                "bytes_sent_mb": round(net.bytes_sent / 1e6, 2),
                "bytes_recv_mb": round(net.bytes_recv / 1e6, 2),
            }
        if metric in ("processes", "all"):
            procs = [
                {"pid": p.pid, "name": p.name(), "cpu": p.cpu_percent(), "mem_mb": round(p.memory_info().rss / 1e6, 1)}
                for p in sorted(psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]),
                                key=lambda x: x.cpu_percent(), reverse=True)[:10]
            ]
            data["top_processes"] = procs

        return ToolResult(success=True, data=data)
```

**Requirement:** Add to `requirements.txt`:
```
psutil>=6.0.0
```

---

### What Agents Can Do With These Tools

With `DockerTool` + `SystemMonitorTool` + `SystemShellTool` + `HttpApiTool`, a DevOps agent configured with these permissions can:

| Task | Tools Used |
|------|-----------|
| "Show me server status" | SystemMonitorTool(all) |
| "Restart the API container" | DockerTool(restart, qubot_api) |
| "Show logs from the worker" | DockerTool(logs, qubot_worker) |
| "What containers are running?" | DockerTool(list_containers) |
| "Deploy latest version" | SystemShellTool(git pull) → DockerTool(pull_image) → DockerTool(restart) |
| "Is disk running low?" | SystemMonitorTool(disk) |
| "Kill runaway process" | SystemShellTool(kill PID) |
| "Update SSL certificate" | SystemShellTool(certbot renew) → SystemShellTool(nginx reload) |

This makes Qubot a **self-managing platform**: users can give infrastructure instructions in natural language, and the system carries them out with full audit trails in `TaskEvent` records.

---

### Security Rules for Infrastructure Tools

1. **Dedicated agent only**: Create a specific "DevOps Agent" with these tools. Never assign infrastructure tools to general-purpose agents.
2. **DANGEROUS permission required**: Both tools require `PermissionEnum.DANGEROUS` on `AgentTool`.
3. **Docker socket access**: Mount `/var/run/docker.sock` as `:ro` by default. Only mount read-write if the agent needs to create/delete containers.
4. **Forbidden containers list**: Always include `qubot_postgres` and `qubot_redis` in `forbidden_container_names` to prevent self-sabotage.
5. **Audit trail**: Every Docker and shell operation is logged as a `TaskEvent(TOOL_CALL)` — full history of who did what.

---

## 14. Adding a New Tool

1. Create `backend/app/tools_impl/{tool_name}.py` implementing `BaseTool`
2. Add to `TOOL_REGISTRY` in `registry.py`
3. Add to `ToolTypeEnum` in `models/enums.py`
4. Add Alembic migration for enum change
5. Document the `config` fields and `input_schema` JSON Schema
6. Add integration test in `tests/unit/test_tool_executor.py`

---

## 14. Requirements

```
# HTTP requests
httpx>=0.27.0

# HTML parsing
beautifulsoup4>=4.12.0
lxml>=5.0.0  # Optional faster parser for BeautifulSoup
```
