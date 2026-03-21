"""
Web Search Tool - DuckDuckGo-powered web search (no API key required)

Fixes:
- DDGS is a synchronous library; calls are wrapped with asyncio.to_thread()
  so they don't block the FastAPI event loop.
- Added 'news' search_type for finding latest news/current events.
- Graceful retry on RateLimit errors with exponential back-off.
"""

from __future__ import annotations

import asyncio
import time

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


def _ddg_text(
    query: str, region: str, safesearch: str, timelimit: str | None, max_results: int
) -> list[dict]:
    """Synchronous DuckDuckGo text search — must be called via to_thread()."""
    from duckduckgo_search import DDGS

    with DDGS() as ddgs:
        raw = ddgs.text(
            keywords=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
        )
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in (raw or [])
        ]


def _ddg_news(
    query: str, region: str, safesearch: str, timelimit: str | None, max_results: int
) -> list[dict]:
    """Synchronous DuckDuckGo news search — must be called via to_thread()."""
    from duckduckgo_search import DDGS

    with DDGS() as ddgs:
        raw = ddgs.news(
            keywords=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
        )
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("body", ""),
                "date": r.get("date", ""),
                "source": r.get("source", ""),
            }
            for r in (raw or [])
        ]


class WebSearchTool(BaseTool):
    """
    Search the web using DuckDuckGo. No API key required.

    - search_type='web'  → general web results (titles, URLs, snippets)
    - search_type='news' → latest news articles (with date + source)

    DuckDuckGo calls are executed in a thread pool so they never block the
    async event loop.
    """

    name = "web_search"
    description = (
        "Search the web using DuckDuckGo — no API key required. "
        "Returns titles, URLs, and text snippets. "
        "Set search_type='news' to find latest news and current events. "
        "Use time_range='d' or 'w' to restrict to recent results. "
        "Great for finding up-to-date information, documentation, tutorials, and news."
    )
    category = ToolCategory.WEB
    risk_level = ToolRiskLevel.SAFE

    MAX_RESULTS = 30
    MAX_RETRIES = 2

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "query": ToolParameter(
                name="query",
                type="string",
                description="Search query string",
                required=True,
            ),
            "search_type": ToolParameter(
                name="search_type",
                type="string",
                description="'web' for general results, 'news' for latest news articles",
                required=False,
                default="web",
                enum=["web", "news"],
            ),
            "max_results": ToolParameter(
                name="max_results",
                type="integer",
                description="Maximum results to return (default 10, max 30)",
                required=False,
                default=10,
            ),
            "region": ToolParameter(
                name="region",
                type="string",
                description="Region code: 'wt-wt' (global), 'us-en', 'es-es', etc.",
                required=False,
                default="wt-wt",
            ),
            "time_range": ToolParameter(
                name="time_range",
                type="string",
                description="Time filter: 'd' (last day), 'w' (week), 'm' (month), 'y' (year)",
                required=False,
                default=None,
                enum=["d", "w", "m", "y"],
            ),
            "safe_search": ToolParameter(
                name="safe_search",
                type="string",
                description="Safe search level: 'on', 'moderate', or 'off'",
                required=False,
                default="moderate",
                enum=["on", "moderate", "off"],
            ),
        }

    def _validate_config(self) -> None:
        self.default_max_results = self.config.get("max_results", 10)
        self.default_region = self.config.get("region", "wt-wt")
        self.default_safe = self.config.get("safe_search", "moderate")

    async def execute(
        self,
        query: str,
        search_type: str = "web",
        max_results: int = 10,
        region: str = "wt-wt",
        time_range: str | None = None,
        safe_search: str = "moderate",
    ) -> ToolResult:
        start_time = time.time()

        if not query or not query.strip():
            return ToolResult(success=False, error="Search query cannot be empty.")

        max_results = min(max(1, max_results), self.MAX_RESULTS)
        fn = _ddg_news if search_type == "news" else _ddg_text

        try:
            from duckduckgo_search import DDGS  # noqa: F401
        except ImportError:
            return ToolResult(
                success=False,
                error="duckduckgo-search not installed. Run: pip install duckduckgo-search",
            )

        # Retry loop — DuckDuckGo occasionally rate-limits
        results: list[dict] = []
        last_error: str = ""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                results = await asyncio.to_thread(
                    fn, query, region, safe_search, time_range, max_results
                )
                break
            except Exception as exc:
                last_error = str(exc)
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(1.5 * (attempt + 1))
                else:
                    return ToolResult(
                        success=False,
                        error=f"Web search failed after {self.MAX_RETRIES + 1} attempts: {last_error}",
                        execution_time_ms=int((time.time() - start_time) * 1000),
                    )

        if not results:
            return ToolResult(
                success=True,
                data={"query": query, "results": [], "total": 0},
                stdout=f"No results found for: {query}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        # Build readable summary for LLM
        label = "News" if search_type == "news" else "Web search"
        lines = [f"{label} results for: {query}\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']}")
            if r.get("date"):
                lines.append(f"   Date: {r['date']} | Source: {r.get('source', '')}")
            lines.append(f"   URL: {r['url']}")
            lines.append(f"   {r['snippet']}\n")

        return ToolResult(
            success=True,
            data={"query": query, "results": results, "total": len(results)},
            stdout="\n".join(lines),
            execution_time_ms=int((time.time() - start_time) * 1000),
            metadata={
                "region": region,
                "time_range": time_range,
                "search_type": search_type,
            },
        )
