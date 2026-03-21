"""
Memory Tool - Persistent semantic memory for agents.
Store, search, and retrieve knowledge across sessions using embeddings.
Uses OpenAI embeddings stored in PostgreSQL with cosine similarity search.
"""

import json
import math
import time
import uuid
from typing import Any

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class AgentMemoryTool(BaseTool):
    """
    Persistent semantic memory for agents.
    Agents can store knowledge, decisions, and context that persists across sessions.
    Search uses OpenAI embeddings for semantic similarity (falls back to keyword search).

    Operations:
    - store: Save a memory with content and optional tags/metadata
    - search: Find memories semantically similar to a query
    - list: List recent or tagged memories
    - delete: Remove a specific memory
    - clear: Remove all memories for a session/agent
    """

    name = "agent_memory"
    description = (
        "Persistent memory for storing and retrieving knowledge across sessions. "
        "Use 'store' to save important information, decisions, or learned facts. "
        "Use 'search' to find relevant past memories semantically. "
        "Use 'list' to see recent memories. "
        "This lets agents remember context between conversations."
    )
    category = ToolCategory.DATA
    risk_level = ToolRiskLevel.NORMAL

    TABLE_NAME = "agent_memories"
    GLOBAL_TABLE_NAME = "global_memories"

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "operation": ToolParameter(
                name="operation",
                type="string",
                description="Operation: 'store', 'search', 'list', 'delete', 'clear'",
                required=True,
                enum=["store", "search", "list", "delete", "clear"],
            ),
            "scope": ToolParameter(
                name="scope",
                type="string",
                description="Memory scope: 'agent' (own memories, default) or 'global' (shared by all agents)",
                required=False,
                default="agent",
                enum=["agent", "global"],
            ),
            "content": ToolParameter(
                name="content",
                type="string",
                description="Memory content to store (for 'store' operation)",
                required=False,
                default=None,
            ),
            "query": ToolParameter(
                name="query",
                type="string",
                description="Search query (for 'search' operation)",
                required=False,
                default=None,
            ),
            "memory_id": ToolParameter(
                name="memory_id",
                type="string",
                description="Memory ID to delete (for 'delete' operation)",
                required=False,
                default=None,
            ),
            "agent_id": ToolParameter(
                name="agent_id",
                type="string",
                description="Agent ID to scope agent-scope memories (optional, uses current agent)",
                required=False,
                default=None,
            ),
            "tags": ToolParameter(
                name="tags",
                type="array",
                description="Tags to associate with memory (for 'store') or filter by (for 'list')",
                required=False,
                default=None,
            ),
            "top_k": ToolParameter(
                name="top_k",
                type="integer",
                description="Number of results to return for search/list (default 5, max 20)",
                required=False,
                default=5,
            ),
            "importance": ToolParameter(
                name="importance",
                type="number",
                description="Importance score 0.0-1.0 (default 0.5, use 1.0 for critical facts)",
                required=False,
                default=0.5,
            ),
        }

    def _validate_config(self) -> None:
        from app.config import settings

        self.db_url = settings.DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql://"
        )
        self.openai_key = settings.OPENAI_API_KEY

    async def _ensure_table(self, conn) -> None:
        """Create memories tables if they don't exist."""
        # Agent memories table
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id TEXT,
                content TEXT NOT NULL,
                embedding JSONB,
                tags JSONB DEFAULT '[]',
                importance FLOAT DEFAULT 0.5,
                metadata JSONB DEFAULT '{{}}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_agent_memories_agent_id
            ON {self.TABLE_NAME}(agent_id)
        """)
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_agent_memories_created_at
            ON {self.TABLE_NAME}(created_at DESC)
        """)

        # Global memories table (shared by all agents)
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.GLOBAL_TABLE_NAME} (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                key TEXT UNIQUE,
                content TEXT NOT NULL,
                content_type TEXT DEFAULT 'text',
                tags JSONB DEFAULT '[]',
                embedding JSONB,
                embedding_ref TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_global_memories_key
            ON {self.GLOBAL_TABLE_NAME}(key)
        """)
        await conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_global_memories_created_at
            ON {self.GLOBAL_TABLE_NAME}(created_at DESC)
        """)

    async def _get_embedding(self, text: str) -> list[float] | None:
        """Get embedding vector for text. Returns None if unavailable."""
        if not self.openai_key:
            return None
        try:
            import openai

            client = openai.AsyncOpenAI(api_key=self.openai_key)
            resp = await client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8000],
            )
            return resp.data[0].embedding
        except Exception:
            return None

    async def _store(
        self,
        conn,
        content: str,
        agent_id: str | None,
        tags: list | None,
        importance: float,
        embedding: list | None,
    ) -> dict:
        mem_id = str(uuid.uuid4())
        await conn.execute(
            f"""INSERT INTO {self.TABLE_NAME}
                (id, agent_id, content, embedding, tags, importance)
                VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6)""",
            mem_id,
            agent_id,
            content,
            json.dumps(embedding) if embedding else None,
            json.dumps(tags or []),
            importance,
        )
        return {"id": mem_id, "content": content[:100], "stored": True}

    async def _search(
        self,
        conn,
        query: str,
        agent_id: str | None,
        top_k: int,
        query_embedding: list | None,
    ) -> list[dict]:
        """Search memories — semantic if embeddings available, else keyword."""
        where = "WHERE agent_id = $1" if agent_id else ""
        params: list[Any] = [agent_id] if agent_id else []

        # Fetch candidates (keyword pre-filter)
        keyword_filter = ""
        if query:
            keyword_lower = query.lower()
            kw_param_idx = len(params) + 1
            params.append(f"%{keyword_lower}%")
            if where:
                keyword_filter = f" AND LOWER(content) LIKE ${kw_param_idx}"
            else:
                keyword_filter = f"WHERE LOWER(content) LIKE ${kw_param_idx}"

        rows = await conn.fetch(
            f"SELECT id, content, embedding, tags, importance, created_at "
            f"FROM {self.TABLE_NAME} "
            f"{where}{keyword_filter} "
            f"ORDER BY importance DESC, created_at DESC LIMIT 100",
            *params,
        )

        results = []
        for row in rows:
            score = 0.5
            if query_embedding and row["embedding"]:
                try:
                    stored_emb = json.loads(row["embedding"])
                    score = _cosine_similarity(query_embedding, stored_emb)
                except Exception:
                    pass
            results.append(
                {
                    "id": str(row["id"]),
                    "content": row["content"],
                    "score": round(score, 4),
                    "tags": json.loads(row["tags"] or "[]"),
                    "importance": row["importance"],
                    "created_at": row["created_at"].isoformat()
                    if row["created_at"]
                    else None,
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    async def _list(
        self, conn, agent_id: str | None, tags: list | None, top_k: int
    ) -> list[dict]:
        where_parts = []
        params: list[Any] = []

        if agent_id:
            params.append(agent_id)
            where_parts.append(f"agent_id = ${len(params)}")

        if tags:
            for tag in tags:
                params.append(tag)
                where_parts.append(f"tags @> ${len(params)}::jsonb")

        where = "WHERE " + " AND ".join(where_parts) if where_parts else ""
        rows = await conn.fetch(
            f"SELECT id, content, tags, importance, created_at "
            f"FROM {self.TABLE_NAME} {where} "
            f"ORDER BY created_at DESC LIMIT ${len(params) + 1}",
            *params,
            top_k,
        )
        return [
            {
                "id": str(r["id"]),
                "content": r["content"][:200],
                "tags": json.loads(r["tags"] or "[]"),
                "importance": r["importance"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]

    async def execute(
        self,
        operation: str,
        scope: str = "agent",
        content: str | None = None,
        query: str | None = None,
        memory_id: str | None = None,
        agent_id: str | None = None,
        tags: list | None = None,
        top_k: int = 5,
        importance: float = 0.5,
    ) -> ToolResult:
        start_time = time.time()
        top_k = min(max(1, top_k), 20)
        is_global = scope == "global"
        table = self.GLOBAL_TABLE_NAME if is_global else self.TABLE_NAME

        try:
            import asyncpg
        except ImportError:
            return ToolResult(success=False, error="asyncpg not installed")

        conn = None
        try:
            conn = await asyncpg.connect(self.db_url, timeout=10)
            await self._ensure_table(conn)

            if operation == "store":
                if not content:
                    return ToolResult(
                        success=False, error="'content' is required for store operation"
                    )
                embedding = await self._get_embedding(content)

                if is_global:
                    mem_id = str(uuid.uuid4())
                    key = content[:50].lower().replace(" ", "-")[:50]
                    await conn.execute(
                        f"""INSERT INTO {table} (id, key, content, tags, embedding, content_type)
                            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, 'text')
                            ON CONFLICT (key) DO UPDATE SET content = $3, tags = $4::jsonb, embedding = $5::jsonb, updated_at = NOW()""",
                        mem_id,
                        key,
                        content,
                        json.dumps(tags or []),
                        json.dumps(embedding) if embedding else None,
                    )
                    result = {
                        "id": mem_id,
                        "key": key,
                        "content": content[:100],
                        "stored": True,
                        "scope": "global",
                    }
                else:
                    mem_id = str(uuid.uuid4())
                    await conn.execute(
                        f"""INSERT INTO {table} (id, agent_id, content, tags, embedding, importance)
                            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6)""",
                        mem_id,
                        agent_id,
                        content,
                        json.dumps(tags or []),
                        json.dumps(embedding) if embedding else None,
                        importance,
                    )
                    result = {
                        "id": mem_id,
                        "agent_id": agent_id,
                        "content": content[:100],
                        "stored": True,
                        "scope": "agent",
                    }

                scope_label = "Global" if is_global else "Agent"
                return ToolResult(
                    success=True,
                    data=result,
                    stdout=f"{scope_label} memory stored: {content[:100]}",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )

            elif operation == "search":
                if not query:
                    return ToolResult(
                        success=False, error="'query' is required for search operation"
                    )
                query_embedding = await self._get_embedding(query)

                where_clause = (
                    "" if is_global else f"WHERE agent_id = '${agent_id or ''}'"
                )

                rows = await conn.fetch(
                    f"""SELECT id, content, tags, embedding, created_at 
                        FROM {table} {where_clause}
                        ORDER BY created_at DESC LIMIT 100"""
                )

                results = []
                for row in rows:
                    score = 0.5
                    if query_embedding and row["embedding"]:
                        try:
                            stored_emb = json.loads(row["embedding"])
                            score = _cosine_similarity(query_embedding, stored_emb)
                        except Exception:
                            pass
                    results.append(
                        {
                            "id": str(row["id"]),
                            "content": row["content"],
                            "score": round(score, 4),
                            "tags": json.loads(row["tags"] or "[]"),
                            "created_at": row["created_at"].isoformat()
                            if row["created_at"]
                            else None,
                        }
                    )

                results.sort(key=lambda x: x["score"], reverse=True)
                memories = results[:top_k]

                scope_label = "global" if is_global else "agent"
                lines = [f"Found {len(memories)} {scope_label} memories for: {query}\n"]
                for i, m in enumerate(memories, 1):
                    lines.append(f"{i}. [{m['score']:.2f}] {m['content'][:150]}")
                    if m["tags"]:
                        lines.append(f"   Tags: {', '.join(m['tags'])}")
                return ToolResult(
                    success=True,
                    data={
                        "memories": memories,
                        "count": len(memories),
                        "query": query,
                        "scope": scope,
                    },
                    stdout="\n".join(lines),
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )

            elif operation == "list":
                if is_global:
                    where_parts = []
                    params = []
                    if tags:
                        for tag in tags:
                            params.append(tag)
                            where_parts.append(f"tags @> ${len(params)}::jsonb")
                    where = "WHERE " + " AND ".join(where_parts) if where_parts else ""
                    rows = await conn.fetch(
                        f"SELECT id, content, tags, created_at FROM {table} {where} ORDER BY created_at DESC LIMIT $1",
                        *([top_k] if not params else params + [top_k]),
                    )
                    memories = [
                        {
                            "id": str(r["id"]),
                            "content": r["content"][:200],
                            "tags": json.loads(r["tags"] or "[]"),
                            "created_at": r["created_at"].isoformat()
                            if r["created_at"]
                            else None,
                        }
                        for r in rows
                    ]
                else:
                    memories = await self._list(conn, agent_id, tags, top_k)

                scope_label = "Global" if is_global else "Agent"
                lines = [f"Recent {scope_label.lower()} memories ({len(memories)}):\n"]
                for i, m in enumerate(memories, 1):
                    lines.append(f"{i}. {m['content'][:150]}")
                    if "importance" in m:
                        lines.append(
                            f"   Tags: {m['tags']} | Importance: {m['importance']} | {m['created_at']}"
                        )
                    else:
                        lines.append(f"   Tags: {m['tags']} | {m['created_at']}")
                return ToolResult(
                    success=True,
                    data={"memories": memories, "count": len(memories), "scope": scope},
                    stdout="\n".join(lines),
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )

            elif operation == "delete":
                if not memory_id:
                    return ToolResult(
                        success=False, error="'memory_id' required for delete"
                    )
                result = await conn.execute(
                    f"DELETE FROM {table} WHERE id = $1", memory_id
                )
                deleted = "1" in result
                scope_label = "Global" if is_global else "Agent"
                return ToolResult(
                    success=True,
                    data={"deleted": deleted, "id": memory_id, "scope": scope},
                    stdout=f"{scope_label} memory {memory_id} {'deleted' if deleted else 'not found'}",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )

            elif operation == "clear":
                if is_global:
                    result = await conn.execute(f"DELETE FROM {table}")
                    scope_label = "Global"
                else:
                    where = "WHERE agent_id = $1" if agent_id else ""
                    params = [agent_id] if agent_id else []
                    result = await conn.execute(f"DELETE FROM {table} {where}", *params)
                    scope_label = f"Agent {agent_id}" if agent_id else "All agent"

                return ToolResult(
                    success=True,
                    data={"cleared": True, "scope": scope},
                    stdout=f"Cleared {scope_label.lower()} memories",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )

            else:
                return ToolResult(
                    success=False, error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Memory operation failed: {e}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
        finally:
            if conn:
                await conn.close()
