"""
Web Search Tool - DuckDuckGo-powered web search (no API key required)
"""

import time

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


class WebSearchTool(BaseTool):
    """
    Tool for searching the web using DuckDuckGo.
    No API key required. Returns titles, snippets, and URLs.
    Use this to find current information, news, documentation, or any topic.
    """

    name = "web_search"
    description = (
        "Search the web using DuckDuckGo. "
        "Returns titles, URLs, and text snippets for relevant results. "
        "Use this to find current information, research topics, locate documentation, "
        "or answer questions that require up-to-date knowledge."
    )
    category = ToolCategory.WEB
    risk_level = ToolRiskLevel.SAFE

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "query": ToolParameter(
                name="query",
                type="string",
                description="Search query string",
                required=True,
            ),
            "max_results": ToolParameter(
                name="max_results",
                type="integer",
                description="Maximum number of results to return (default 10, max 30)",
                required=False,
                default=10,
            ),
            "region": ToolParameter(
                name="region",
                type="string",
                description="Region code for localized results (e.g. 'wt-wt' for global, 'us-en', 'es-es')",
                required=False,
                default="wt-wt",
            ),
            "time_range": ToolParameter(
                name="time_range",
                type="string",
                description="Time filter: 'd' (day), 'w' (week), 'm' (month), 'y' (year), or None for all time",
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

    async def execute(
        self,
        query: str,
        max_results: int = 10,
        region: str = "wt-wt",
        time_range: str | None = None,
        safe_search: str = "moderate",
    ) -> ToolResult:
        """
        Search the web using DuckDuckGo.

        Args:
            query: Search query string
            max_results: Number of results to return (capped at 30)
            region: Region code for results
            time_range: Time filter
            safe_search: Safe search level

        Returns:
            ToolResult with list of search results
        """
        start_time = time.time()

        if not query or not query.strip():
            return ToolResult(success=False, error="Search query cannot be empty")

        max_results = min(max(1, max_results), 30)

        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return ToolResult(
                success=False,
                error=(
                    "duckduckgo-search package not installed. "
                    "Install with: pip install duckduckgo-search"
                ),
            )

        try:
            results = []
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    keywords=query,
                    region=region,
                    safesearch=safe_search,
                    timelimit=time_range,
                    max_results=max_results,
                )
                if search_results:
                    for r in search_results:
                        results.append(
                            {
                                "title": r.get("title", ""),
                                "url": r.get("href", ""),
                                "snippet": r.get("body", ""),
                            }
                        )

            if not results:
                return ToolResult(
                    success=True,
                    data={"query": query, "results": [], "total": 0},
                    stdout=f"No results found for: {query}",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )

            # Build readable summary for the LLM
            lines = [f"Search results for: {query}\n"]
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. {r['title']}")
                lines.append(f"   URL: {r['url']}")
                lines.append(f"   {r['snippet']}\n")
            summary = "\n".join(lines)

            return ToolResult(
                success=True,
                data={"query": query, "results": results, "total": len(results)},
                stdout=summary,
                execution_time_ms=int((time.time() - start_time) * 1000),
                metadata={
                    "region": region,
                    "time_range": time_range,
                    "safe_search": safe_search,
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
