"""
Database Query Tool - Execute SQL queries directly against PostgreSQL.
Gives agents structured data access without going through the REST API.
"""

import re
import time
from typing import Any

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


class DatabaseQueryTool(BaseTool):
    """
    Execute SQL queries against PostgreSQL databases.
    Read-only by default (SELECT, WITH, EXPLAIN). Write mode must be explicitly enabled.
    Use for reporting, analytics, data exploration, and structured queries.

    Returns results as list of dicts with column names as keys.
    """

    name = "database_query"
    description = (
        "Execute SQL queries against the PostgreSQL database. "
        "Read-only by default: SELECT, WITH, EXPLAIN queries. "
        "Returns results as structured data (list of rows with named columns). "
        "Use for reporting, analytics, finding records, and data exploration."
    )
    category = ToolCategory.DATA
    risk_level = ToolRiskLevel.NORMAL

    MAX_ROWS = 1000

    # SQL patterns that are write operations
    _WRITE_PATTERNS = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|REPLACE|UPSERT|MERGE|GRANT|REVOKE)\b",
        re.IGNORECASE,
    )

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "query": ToolParameter(
                name="query",
                type="string",
                description="SQL query to execute. Use parameterized queries with $1, $2 for safety.",
                required=True,
            ),
            "params": ToolParameter(
                name="params",
                type="array",
                description="Query parameters as array (for parameterized queries)",
                required=False,
                default=None,
            ),
            "limit": ToolParameter(
                name="limit",
                type="integer",
                description=f"Max rows to return (default 100, max {MAX_ROWS})",
                required=False,
                default=100,
            ),
            "database_url": ToolParameter(
                name="database_url",
                type="string",
                description="Override database URL (optional, uses app database by default)",
                required=False,
                default=None,
            ),
            "allow_write": ToolParameter(
                name="allow_write",
                type="boolean",
                description="Allow INSERT/UPDATE/DELETE operations (disabled by default)",
                required=False,
                default=False,
            ),
        }

    def _validate_config(self) -> None:
        from app.config import settings

        self.default_database_url = self.config.get("database_url", None) or settings.DATABASE_URL
        # Convert asyncpg URL to standard asyncpg format
        self.default_database_url = self.default_database_url.replace(
            "postgresql+asyncpg://", "postgresql://"
        )
        self.write_enabled = self.config.get("write_enabled", False)

    def _check_write_operations(self, query: str) -> bool:
        """Returns True if query contains write operations."""
        return bool(self._WRITE_PATTERNS.search(query))

    def _add_row_limit(self, query: str, limit: int) -> str:
        """Append LIMIT clause to SELECT queries if not already present."""
        query_stripped = query.strip().rstrip(";")
        q_upper = query_stripped.upper()
        if q_upper.startswith("SELECT") and "LIMIT" not in q_upper:
            return f"{query_stripped} LIMIT {limit}"
        return query_stripped

    async def execute(
        self,
        query: str,
        params: list[Any] | None = None,
        limit: int = 100,
        database_url: str | None = None,
        allow_write: bool = False,
    ) -> ToolResult:
        start_time = time.time()

        if not query or not query.strip():
            return ToolResult(success=False, error="Query cannot be empty")

        # Security: block write operations unless explicitly allowed
        is_write = self._check_write_operations(query)
        if is_write and not (allow_write and self.write_enabled):
            return ToolResult(
                success=False,
                error=(
                    "Write operations (INSERT/UPDATE/DELETE/DROP) are disabled by default. "
                    "Set allow_write=true and enable write_enabled in tool config to proceed."
                ),
            )

        limit = min(max(1, limit), self.MAX_ROWS)
        if not is_write:
            query = self._add_row_limit(query, limit)

        db_url = database_url or self.default_database_url
        if database_url:
            db_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

        try:
            import asyncpg
        except ImportError:
            return ToolResult(success=False, error="asyncpg not installed: pip install asyncpg")

        conn = None
        try:
            conn = await asyncpg.connect(db_url, timeout=30)

            if params:
                records = await conn.fetch(query, *params, timeout=60)
            else:
                records = await conn.fetch(query, timeout=60)

            rows = [dict(r) for r in records]

            # Convert non-serializable types
            for row in rows:
                for k, v in row.items():
                    if hasattr(v, "isoformat"):
                        row[k] = v.isoformat()
                    elif hasattr(v, "__class__") and v.__class__.__name__ in ("UUID", "Decimal"):
                        row[k] = str(v)

            # Build text summary
            if rows:
                headers = list(rows[0].keys())
                col_widths = {h: max(len(h), max(len(str(r.get(h, ""))) for r in rows[:20])) for h in headers}
                header_line = " | ".join(h.ljust(col_widths[h]) for h in headers)
                sep_line = "-+-".join("-" * col_widths[h] for h in headers)
                data_lines = [
                    " | ".join(str(r.get(h, "")).ljust(col_widths[h]) for h in headers)
                    for r in rows[:50]
                ]
                summary = f"{header_line}\n{sep_line}\n" + "\n".join(data_lines)
                if len(rows) > 50:
                    summary += f"\n... ({len(rows)} rows total, showing 50)"
            else:
                summary = "(no rows returned)"

            exec_ms = int((time.time() - start_time) * 1000)
            return ToolResult(
                success=True,
                data={"rows": rows, "count": len(rows), "columns": list(rows[0].keys()) if rows else []},
                stdout=summary,
                execution_time_ms=exec_ms,
                metadata={"row_count": len(rows), "query_preview": query[:200]},
            )

        except asyncpg.PostgresError as e:
            return ToolResult(
                success=False,
                error=f"PostgreSQL error: {e}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Database query failed: {e}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
        finally:
            if conn:
                await conn.close()
