"""
MCP Client - Connect to Model Context Protocol servers.

Supports three transports:
  - SSE  (HTTP/Server-Sent Events) — legacy hosted MCP servers (spec 2024-11-05)
  - HTTP (Streamable HTTP)          — modern hosted MCP servers (spec 2025-03-26)
  - stdio (local subprocess)        — npx/uvx/python MCP servers

Uses the official 'mcp' Python SDK when available.
Falls back to a lightweight httpx-based implementation for SSE servers.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _mcp_tool_to_dict(tool: Any) -> dict:
    """Convert an mcp.types.Tool to a plain dict."""
    schema: dict = {}
    if hasattr(tool, "inputSchema"):
        raw = tool.inputSchema
        if hasattr(raw, "model_dump"):
            schema = raw.model_dump()
        elif isinstance(raw, dict):
            schema = raw
    return {
        "name": str(tool.name),
        "description": str(getattr(tool, "description", "") or ""),
        "input_schema": schema,
    }


# ---------------------------------------------------------------------------
# Streamable HTTP transport (official mcp package — spec 2025-03-26)
# ---------------------------------------------------------------------------

async def list_tools_http(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> list[dict]:
    """List tools from a Streamable HTTP MCP server (modern hosted servers)."""
    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        async with streamablehttp_client(url, headers=headers or {}) as (read, write, _):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), timeout=timeout)
                result = await asyncio.wait_for(session.list_tools(), timeout=timeout)
                return [_mcp_tool_to_dict(t) for t in result.tools]

    except Exception as e:
        raise ConnectionError(f"HTTP MCP server '{url}': {e}") from e


async def call_tool_http(
    url: str,
    tool_name: str,
    args: dict,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> str:
    """Call a tool on a Streamable HTTP MCP server."""
    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        async with streamablehttp_client(url, headers=headers or {}) as (read, write, _):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), timeout=timeout)
                result = await asyncio.wait_for(
                    session.call_tool(tool_name, args), timeout=timeout
                )
                return _extract_content(result)

    except Exception as e:
        raise RuntimeError(f"HTTP MCP tool call '{tool_name}' on '{url}': {e}") from e


# ---------------------------------------------------------------------------
# SSE transport (official mcp package)
# ---------------------------------------------------------------------------

async def list_tools_sse(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> list[dict]:
    """List tools from an SSE/HTTP MCP server."""
    try:
        from mcp import ClientSession
        from mcp.client.sse import sse_client

        async with sse_client(url, headers=headers or {}) as (read, write):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), timeout=timeout)
                result = await asyncio.wait_for(session.list_tools(), timeout=timeout)
                return [_mcp_tool_to_dict(t) for t in result.tools]

    except ImportError:
        # Fallback to lightweight httpx SSE implementation
        return await _list_tools_sse_httpx(url, headers or {}, timeout)
    except Exception as e:
        raise ConnectionError(f"SSE MCP server '{url}': {e}") from e


async def call_tool_sse(
    url: str,
    tool_name: str,
    args: dict,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> str:
    """Call a tool on an SSE MCP server."""
    try:
        from mcp import ClientSession
        from mcp.client.sse import sse_client

        async with sse_client(url, headers=headers or {}) as (read, write):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), timeout=timeout)
                result = await asyncio.wait_for(
                    session.call_tool(tool_name, args), timeout=timeout
                )
                return _extract_content(result)

    except ImportError:
        return await _call_tool_sse_httpx(url, tool_name, args, headers or {}, timeout)
    except Exception as e:
        raise RuntimeError(f"MCP tool call '{tool_name}' on '{url}': {e}") from e


# ---------------------------------------------------------------------------
# stdio transport (official mcp package)
# ---------------------------------------------------------------------------

async def list_tools_stdio(
    command: str,
    args: list[str],
    env: dict[str, str] | None = None,
    timeout: int = 30,
) -> list[dict]:
    """List tools from a stdio MCP server (local process)."""
    try:
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        params = StdioServerParameters(
            command=command,
            args=args,
            env={**os.environ, **(env or {})},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), timeout=timeout)
                result = await asyncio.wait_for(session.list_tools(), timeout=timeout)
                return [_mcp_tool_to_dict(t) for t in result.tools]

    except ImportError as e:
        raise ImportError("mcp package is required for stdio transport: pip install mcp") from e
    except Exception as e:
        raise ConnectionError(f"stdio MCP server '{command}': {e}") from e


async def call_tool_stdio(
    command: str,
    args_list: list[str],
    tool_name: str,
    tool_args: dict,
    env: dict[str, str] | None = None,
    timeout: int = 30,
) -> str:
    """Call a tool on a stdio MCP server."""
    try:
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        params = StdioServerParameters(
            command=command,
            args=args_list,
            env={**os.environ, **(env or {})},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), timeout=timeout)
                result = await asyncio.wait_for(
                    session.call_tool(tool_name, tool_args), timeout=timeout
                )
                return _extract_content(result)

    except ImportError as e:
        raise ImportError("mcp package is required for stdio transport: pip install mcp") from e
    except Exception as e:
        raise RuntimeError(f"MCP tool call '{tool_name}' on stdio server '{command}': {e}") from e


# ---------------------------------------------------------------------------
# Lightweight httpx SSE fallback (no mcp package needed)
# ---------------------------------------------------------------------------

async def _list_tools_sse_httpx(
    url: str, headers: dict, timeout: int
) -> list[dict]:
    """
    Minimal MCP SSE implementation via httpx.
    Works with servers that follow the 2024-11-05 MCP spec.
    """
    import httpx

    sse_url = url if url.endswith("/sse") else url.rstrip("/") + "/sse"
    post_url: str | None = None
    pending: dict[int, asyncio.Future] = {}
    next_id = 1
    loop = asyncio.get_event_loop()

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        # ------------------------------------------------------------------
        # 1. Open SSE stream, discover posting endpoint
        # ------------------------------------------------------------------
        event_queue: asyncio.Queue[str] = asyncio.Queue()

        async def _stream():
            try:
                async with client.stream(
                    "GET", sse_url,
                    headers={**headers, "Accept": "text/event-stream"},
                ) as resp:
                    resp.raise_for_status()
                    async for raw in resp.aiter_lines():
                        await event_queue.put(raw)
            except Exception as exc:
                await event_queue.put(f"__ERR__:{exc}")

        stream_task = asyncio.create_task(_stream())

        try:
            # Collect lines until we get the endpoint event
            current_event: str | None = None
            data_buf: list[str] = []

            while post_url is None:
                line = await asyncio.wait_for(event_queue.get(), timeout=timeout)
                if line.startswith("__ERR__:"):
                    raise ConnectionError(line[8:])
                if line.startswith("event:"):
                    current_event = line[6:].strip()
                elif line.startswith("data:"):
                    data_buf.append(line[5:].strip())
                elif line == "":
                    data = "\n".join(data_buf)
                    data_buf = []
                    if current_event == "endpoint" or (data.startswith("/")):
                        if data.startswith("/"):
                            from urllib.parse import urlparse
                            p = urlparse(url)
                            post_url = f"{p.scheme}://{p.netloc}{data}"
                        else:
                            post_url = data
                    current_event = None

            # ------------------------------------------------------------------
            # 2. JSON-RPC helper
            # ------------------------------------------------------------------
            async def jsonrpc(method: str, params: dict | None = None) -> Any:
                nonlocal next_id
                req_id = next_id
                next_id += 1
                payload: dict = {"jsonrpc": "2.0", "id": req_id, "method": method}
                if params:
                    payload["params"] = params

                await client.post(
                    post_url,
                    json=payload,
                    headers={**headers, "Content-Type": "application/json"},
                )

                # Wait for matching response on SSE stream
                buf: list[str] = []
                while True:
                    raw = await asyncio.wait_for(event_queue.get(), timeout=timeout)
                    if raw.startswith("__ERR__:"):
                        raise RuntimeError(raw[8:])
                    buf.append(raw)
                    if raw == "":
                        d = "\n".join(l[5:].strip() for l in buf if l.startswith("data:"))
                        buf = []
                        if d:
                            msg = json.loads(d)
                            if msg.get("id") == req_id:
                                if "error" in msg:
                                    raise RuntimeError(msg["error"].get("message", str(msg["error"])))
                                return msg.get("result")

            # ------------------------------------------------------------------
            # 3. Initialize + list tools
            # ------------------------------------------------------------------
            await jsonrpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "qubot", "version": "1.0"},
            })
            result = await jsonrpc("tools/list")
            tools = (result or {}).get("tools", [])
            return [
                {
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "input_schema": t.get("inputSchema", {}),
                }
                for t in tools
            ]
        finally:
            stream_task.cancel()


async def _call_tool_sse_httpx(
    url: str, tool_name: str, args: dict, headers: dict, timeout: int
) -> str:
    """Call a tool using the lightweight httpx SSE client."""
    import httpx

    sse_url = url if url.endswith("/sse") else url.rstrip("/") + "/sse"
    post_url: str | None = None
    next_id = 1

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        event_queue: asyncio.Queue[str] = asyncio.Queue()

        async def _stream():
            try:
                async with client.stream(
                    "GET", sse_url,
                    headers={**headers, "Accept": "text/event-stream"},
                ) as resp:
                    resp.raise_for_status()
                    async for raw in resp.aiter_lines():
                        await event_queue.put(raw)
            except Exception as exc:
                await event_queue.put(f"__ERR__:{exc}")

        stream_task = asyncio.create_task(_stream())
        try:
            data_buf: list[str] = []
            while post_url is None:
                line = await asyncio.wait_for(event_queue.get(), timeout=timeout)
                if line.startswith("__ERR__:"):
                    raise ConnectionError(line[8:])
                if line.startswith("data:"):
                    data_buf.append(line[5:].strip())
                elif line == "":
                    data = "\n".join(data_buf)
                    data_buf = []
                    if data.startswith("/"):
                        from urllib.parse import urlparse
                        p = urlparse(url)
                        post_url = f"{p.scheme}://{p.netloc}{data}"

            async def jsonrpc(method: str, params: dict | None = None) -> Any:
                nonlocal next_id
                req_id = next_id
                next_id += 1
                payload: dict = {"jsonrpc": "2.0", "id": req_id, "method": method}
                if params:
                    payload["params"] = params
                await client.post(post_url, json=payload,
                                  headers={**headers, "Content-Type": "application/json"})
                buf: list[str] = []
                while True:
                    raw = await asyncio.wait_for(event_queue.get(), timeout=timeout)
                    if raw.startswith("__ERR__:"):
                        raise RuntimeError(raw[8:])
                    buf.append(raw)
                    if raw == "":
                        d = "\n".join(l[5:].strip() for l in buf if l.startswith("data:"))
                        buf = []
                        if d:
                            msg = json.loads(d)
                            if msg.get("id") == req_id:
                                if "error" in msg:
                                    raise RuntimeError(msg["error"].get("message"))
                                return msg.get("result")

            await jsonrpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "qubot", "version": "1.0"},
            })
            result = await jsonrpc("tools/call", {"name": tool_name, "arguments": args})
            content = (result or {}).get("content", [])
            parts = [c.get("text", "") for c in content if isinstance(c, dict)]
            return "\n".join(parts)
        finally:
            stream_task.cancel()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_content(result: Any) -> str:
    """Extract text from an MCP CallToolResult."""
    if not hasattr(result, "content") or not result.content:
        return ""
    parts = []
    for item in result.content:
        if hasattr(item, "text"):
            parts.append(str(item.text))
        elif hasattr(item, "data"):
            parts.append(str(item.data))
        elif isinstance(item, dict):
            parts.append(item.get("text", str(item)))
    return "\n".join(parts)
