"""
Docs Search Tool - Real-time library documentation lookup via Context7.
Agents always have access to the latest API docs, tutorials, and code examples
for any library without relying on potentially stale training data.

Uses Context7 API (context7.com) to fetch up-to-date documentation.
Falls back to PyPI + GitHub README if Context7 is unavailable.
"""

import time

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


class DocsSearchTool(BaseTool):
    """
    Look up current documentation for any library or framework.
    Uses Context7 to always return up-to-date docs, not potentially stale training data.

    Operations:
    - lookup: Find and return documentation for a library
    - search: Search docs for a specific topic within a library

    Examples:
    - lookup("fastapi") → FastAPI latest docs
    - search("react", "useEffect hook") → React useEffect documentation
    - lookup("pandas") → pandas API reference
    """

    name = "docs_search"
    description = (
        "Look up real-time documentation for any library, framework, or API. "
        "Returns accurate, up-to-date docs including code examples. "
        "Use when you need current API references, function signatures, or usage examples. "
        "Prevents outdated answers from training data. "
        "Examples: docs_search('fastapi'), docs_search('pandas', 'DataFrame groupby')"
    )
    category = ToolCategory.WEB
    risk_level = ToolRiskLevel.SAFE

    CONTEXT7_BASE = "https://context7.com/api/v1"

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "library": ToolParameter(
                name="library",
                type="string",
                description="Library or framework name (e.g. 'fastapi', 'react', 'pandas', 'langchain')",
                required=True,
            ),
            "query": ToolParameter(
                name="query",
                type="string",
                description="Specific topic or function to look up within the library (optional)",
                required=False,
                default=None,
            ),
            "max_tokens": ToolParameter(
                name="max_tokens",
                type="integer",
                description="Max tokens of documentation to return (default 5000, max 20000)",
                required=False,
                default=5000,
            ),
            "version": ToolParameter(
                name="version",
                type="string",
                description="Specific library version (optional, defaults to latest)",
                required=False,
                default=None,
            ),
        }

    def _validate_config(self) -> None:
        import os
        self.context7_token = self.config.get("context7_token") or os.getenv("CONTEXT7_TOKEN", "")
        self.timeout = self.config.get("timeout", 20)

    async def _resolve_library_id(self, library: str) -> str | None:
        """Resolve library name to Context7 library ID."""
        try:
            import httpx
            headers = {}
            if self.context7_token:
                headers["Authorization"] = f"Bearer {self.context7_token}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.CONTEXT7_BASE}/resolve",
                    params={"libraryName": library},
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    # Context7 returns list of matches, pick best
                    if isinstance(data, list) and data:
                        return data[0].get("id") or data[0].get("library_id")
                    elif isinstance(data, dict):
                        return data.get("id") or data.get("library_id")
        except Exception:
            pass
        return None

    async def _fetch_context7_docs(self, library_id: str, query: str | None,
                                    max_tokens: int) -> str | None:
        """Fetch documentation from Context7."""
        try:
            import httpx
            headers = {}
            if self.context7_token:
                headers["Authorization"] = f"Bearer {self.context7_token}"

            params: dict = {"tokens": max_tokens}
            if query:
                params["query"] = query

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.CONTEXT7_BASE}/libraries/{library_id}",
                    params=params,
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    # Extract text content from Context7 response
                    if isinstance(data, dict):
                        return (
                            data.get("content")
                            or data.get("text")
                            or data.get("documentation")
                            or data.get("result")
                        )
                    elif isinstance(data, str):
                        return data
        except Exception:
            pass
        return None

    async def _pypi_fallback(self, library: str, query: str | None) -> dict:
        """Fallback: fetch library info from PyPI + GitHub README."""
        try:
            import httpx
            result_parts = []

            async with httpx.AsyncClient(timeout=15) as client:
                # PyPI info
                resp = await client.get(f"https://pypi.org/pypi/{library}/json")
                if resp.status_code == 200:
                    info = resp.json().get("info", {})
                    result_parts.append(f"# {info.get('name')} {info.get('version', '')}")
                    result_parts.append(f"**{info.get('summary', '')}**")
                    result_parts.append(f"Home: {info.get('home_page') or info.get('project_url', '')}")

                    description = info.get("description", "")
                    if description and description != "UNKNOWN":
                        # Truncate long READMEs
                        if query:
                            # Try to find relevant section
                            lower_desc = description.lower()
                            query_lower = query.lower()
                            idx = lower_desc.find(query_lower)
                            if idx != -1:
                                start = max(0, idx - 200)
                                end = min(len(description), idx + 2000)
                                description = f"[...]\n{description[start:end]}\n[...]"
                        result_parts.append(f"\n## Documentation\n\n{description[:8000]}")

                    return {
                        "source": "pypi",
                        "library": info.get("name"),
                        "version": info.get("version"),
                        "content": "\n\n".join(result_parts),
                    }
        except Exception:
            pass

        return {
            "source": "none",
            "library": library,
            "content": f"Documentation for '{library}' could not be fetched. Try searching on docs.{library}.io or github.com.",
        }

    async def _npm_fallback(self, library: str) -> dict | None:
        """Try npm registry for JS packages."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"https://registry.npmjs.org/{library}/latest")
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "source": "npm",
                        "library": data.get("name"),
                        "version": data.get("version"),
                        "content": f"# {data.get('name')} v{data.get('version')}\n\n{data.get('description', '')}\n\nHomepage: {data.get('homepage', '')}",
                    }
        except Exception:
            pass
        return None

    async def execute(
        self,
        library: str,
        query: str | None = None,
        max_tokens: int = 5000,
        version: str | None = None,
    ) -> ToolResult:
        start_time = time.time()

        if not library or not library.strip():
            return ToolResult(success=False, error="Library name cannot be empty")

        max_tokens = min(max(500, max_tokens), 20000)
        library = library.strip().lower()

        # 1. Try Context7 first
        library_id = await self._resolve_library_id(library)

        if library_id:
            content = await self._fetch_context7_docs(library_id, query, max_tokens)
            if content:
                summary = f"Documentation for '{library}'"
                if query:
                    summary += f" — topic: '{query}'"
                summary += f"\n(Source: Context7, library_id: {library_id})\n\n"
                summary += content

                return ToolResult(
                    success=True,
                    data={
                        "library": library,
                        "library_id": library_id,
                        "query": query,
                        "content": content,
                        "source": "context7",
                    },
                    stdout=summary,
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    metadata={"source": "context7", "library_id": library_id},
                )

        # 2. Fallback: PyPI
        pypi_result = await self._pypi_fallback(library, query)
        if pypi_result.get("source") == "pypi":
            content = pypi_result["content"]
            return ToolResult(
                success=True,
                data=pypi_result,
                stdout=content[:10000],
                execution_time_ms=int((time.time() - start_time) * 1000),
                metadata={"source": "pypi", "library": library},
            )

        # 3. Fallback: npm
        npm_result = await self._npm_fallback(library)
        if npm_result:
            return ToolResult(
                success=True,
                data=npm_result,
                stdout=npm_result["content"],
                execution_time_ms=int((time.time() - start_time) * 1000),
                metadata={"source": "npm", "library": library},
            )

        # 4. Nothing found
        return ToolResult(
            success=False,
            error=f"Documentation for '{library}' not found via Context7, PyPI, or npm. Try a more specific name.",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )
