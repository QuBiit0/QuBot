"""
Memory Service — Business logic for memory management.

Phase 1 updates:  build_agent_context() returns structured sections for
                  ContextAssembler instead of raw markdown strings.

Phase 3 updates:  Hybrid search (BM25 + vector cosine + temporal decay + MMR)
                  replaces simple importance-sorted DB queries.
                  Embeddings are generated on write and stored in the JSON
                  embedding column; pgvector column is populated when available.

Phase 5 updates:  content_hash stored on write for deduplication support.
"""

import hashlib
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, select

from ..models.enums import DomainEnum
from ..models.memory import AgentMemory, GlobalMemory, TaskMemory
from ..core.hybrid_search import HybridSearchEngine

logger = logging.getLogger(__name__)


def _sha256_prefix(text: str) -> str:
    """Return first 64 hex chars of SHA-256 digest of *text*."""
    return hashlib.sha256(text.encode()).hexdigest()[:64]


class MemoryService:
    def __init__(self, session: AsyncSession, openai_api_key: str | None = None):
        self.session = session
        self.openai_api_key = openai_api_key
        self._search_engine = HybridSearchEngine(
            enable_temporal_decay=True,
            enable_mmr=True,
        )

    # ── Embedding helpers ─────────────────────────────────────────────────────

    async def _get_embedding(self, text: str) -> list[float] | None:
        """Generate embedding for *text* (OpenAI text-embedding-3-small)."""
        return await self._search_engine.get_query_embedding(
            text, self.openai_api_key
        )

    # ── Global Memory ─────────────────────────────────────────────────────────

    async def create_global_memory(
        self,
        key: str,
        content: str,
        content_type: str = "text",
        tags: list[str] | None = None,
    ) -> GlobalMemory:
        """Create global memory entry with embedding."""
        embedding = await self._get_embedding(content)
        memory = GlobalMemory(
            key=key,
            content=content,
            content_type=content_type,
            tags=tags or [],
            embedding=embedding,
        )
        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)
        return memory

    async def get_global_memory(self, memory_id: UUID) -> GlobalMemory | None:
        result = await self.session.execute(
            select(GlobalMemory).where(GlobalMemory.id == memory_id)
        )
        return result.scalar_one_or_none()

    async def get_global_memories(
        self,
        tags: list[str] | None = None,
        search_query: str | None = None,
        limit: int = 20,
    ) -> list[GlobalMemory]:
        """Fetch global memories for hybrid re-ranking downstream."""
        query = select(GlobalMemory).order_by(desc(GlobalMemory.updated_at))

        if tags:
            query = query.where(GlobalMemory.tags.cast(JSONB).op("?|")(tags))

        if search_query:
            query = query.where(GlobalMemory.content.ilike(f"%{search_query}%"))

        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_global_memory(
        self, memory_id: UUID, **updates
    ) -> GlobalMemory | None:
        memory = await self.get_global_memory(memory_id)
        if not memory:
            return None

        for key, value in updates.items():
            if hasattr(memory, key):
                setattr(memory, key, value)

        # Regenerate embedding when content changes
        if "content" in updates and updates["content"]:
            memory.embedding = await self._get_embedding(updates["content"])

        memory.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(memory)
        return memory

    async def delete_global_memory(self, memory_id: UUID) -> bool:
        memory = await self.get_global_memory(memory_id)
        if not memory:
            return False
        await self.session.delete(memory)
        await self.session.commit()
        return True

    # ── Agent Memory ──────────────────────────────────────────────────────────

    async def create_agent_memory(
        self,
        agent_id: UUID,
        key: str,
        content: str,
        importance: int = 3,
    ) -> AgentMemory:
        """Create or update agent memory with embedding + content_hash."""
        content_hash = _sha256_prefix(content)

        # Check for existing entry by key
        result = await self.session.execute(
            select(AgentMemory).where(
                AgentMemory.agent_id == agent_id,
                AgentMemory.key == key,
            )
        )
        existing = result.scalar_one_or_none()

        embedding = await self._get_embedding(content)

        if existing:
            existing.content = content
            existing.importance = importance
            existing.content_hash = content_hash
            existing.embedding = embedding
            existing.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        memory = AgentMemory(
            agent_id=agent_id,
            key=key,
            content=content,
            importance=importance,
            content_hash=content_hash,
            embedding=embedding,
        )
        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)
        return memory

    async def get_agent_memories_raw(
        self,
        agent_id: UUID,
        limit: int = 50,
        min_importance: int = 1,
    ) -> list[AgentMemory]:
        """Fetch raw agent memories for hybrid search (larger pool)."""
        result = await self.session.execute(
            select(AgentMemory)
            .where(AgentMemory.agent_id == agent_id)
            .where(AgentMemory.importance >= min_importance)
            .order_by(desc(AgentMemory.importance), desc(AgentMemory.last_accessed))
            .limit(limit)
        )
        memories = list(result.scalars().all())

        # Update last_accessed in bulk
        now = datetime.utcnow()
        for mem in memories:
            mem.last_accessed = now
        if memories:
            await self.session.commit()

        return memories

    async def get_agent_memories(
        self,
        agent_id: UUID,
        query: str = "",
        top_k: int = 8,
        min_importance: int = 1,
    ) -> list[dict]:
        """
        Retrieve agent memories using hybrid search.

        Returns a list of dicts (not ORM objects) enriched with final_score.
        """
        raw = await self.get_agent_memories_raw(agent_id, limit=50, min_importance=min_importance)
        if not raw:
            return []

        query_embedding: list[float] | None = None
        if query:
            query_embedding = await self._get_embedding(query)

        mem_dicts = [
            {
                "id": str(m.id),
                "key": m.key,
                "content": m.content,
                "importance": m.importance,
                "embedding": m.embedding,
                "created_at": m.created_at,
                "last_accessed": m.last_accessed,
            }
            for m in raw
        ]

        if query:
            ranked = self._search_engine.search(
                query=query,
                memories=mem_dicts,
                query_embedding=query_embedding,
                top_k=top_k,
            )
            return ranked

        # No query → sort by importance + recency, respect top_k
        return sorted(
            mem_dicts,
            key=lambda m: (m["importance"], m.get("last_accessed") or datetime.min),
            reverse=True,
        )[:top_k]

    async def delete_agent_memory(self, memory_id: UUID) -> bool:
        result = await self.session.execute(
            select(AgentMemory).where(AgentMemory.id == memory_id)
        )
        memory = result.scalar_one_or_none()
        if not memory:
            return False
        await self.session.delete(memory)
        await self.session.commit()
        return True

    # ── Task Memory ───────────────────────────────────────────────────────────

    async def create_task_memory(
        self,
        task_id: UUID,
        summary: str,
        key_facts: list[str] | None = None,
    ) -> TaskMemory:
        memory = TaskMemory(
            task_id=task_id,
            summary=summary,
            key_facts=key_facts or [],
        )
        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)
        return memory

    async def get_task_memory(self, task_id: UUID) -> TaskMemory | None:
        result = await self.session.execute(
            select(TaskMemory).where(TaskMemory.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_recent_task_memories(
        self,
        domain: DomainEnum | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Get recent task memories, optionally filtered by domain."""
        from ..models.task import Task

        query = (
            select(TaskMemory, Task.title, Task.domain_hint)
            .join(Task, TaskMemory.task_id == Task.id)
            .order_by(desc(TaskMemory.created_at))
        )

        if domain:
            query = query.where(Task.domain_hint == domain)

        query = query.limit(limit)
        result = await self.session.execute(query)

        return [
            {
                "task_title": row[1],
                "domain": row[2],
                "summary": row[0].summary,
                "key_facts": row[0].key_facts,
                "created_at": row[0].created_at,
            }
            for row in result.all()
        ]

    # ── Context building ──────────────────────────────────────────────────────

    async def build_agent_context_sections(
        self,
        agent_id: UUID,
        task_title: str = "",
        task_domain: DomainEnum | None = None,
        query: str = "",
    ) -> list[dict]:
        """
        Build structured memory sections for ContextAssembler.

        Returns a list of section dicts::

            [
                {
                    "header": "### Shared Knowledge",
                    "items": [{"content": "...", "score": 0.9}, ...]
                },
                ...
            ]

        The ContextAssembler uses these sections to fit content within the
        memory token budget — dropping items from the end when space runs out.
        """
        sections: list[dict] = []
        effective_query = query or task_title

        # 1. Global memories (domain-filtered, hybrid-ranked)
        domain_tag = task_domain.value.lower() if task_domain else None
        global_mems = await self.get_global_memories(
            tags=[domain_tag] if domain_tag else None,
            search_query=effective_query or None,
            limit=20,
        )
        if global_mems:
            query_emb: list[float] | None = None
            if effective_query:
                query_emb = await self._get_embedding(effective_query)

            global_dicts = [
                {
                    "content": m.content,
                    "importance": 3,
                    "embedding": m.embedding,
                    "created_at": m.created_at,
                    "key": m.key,
                }
                for m in global_mems
            ]
            ranked_global = self._search_engine.search(
                query=effective_query or "knowledge",
                memories=global_dicts,
                query_embedding=query_emb,
                top_k=3,
            )
            if ranked_global:
                sections.append(
                    {
                        "header": "### Shared Knowledge",
                        "items": [
                            {"content": f"**{m.get('key', '')}**:\n{m['content']}"}
                            for m in ranked_global
                        ],
                    }
                )

        # 2. Agent-specific memories (hybrid-ranked)
        agent_mems = await self.get_agent_memories(
            agent_id=agent_id,
            query=effective_query,
            top_k=8,
            min_importance=2,
        )
        if agent_mems:
            sections.append(
                {
                    "header": "### Your Memory",
                    "items": [
                        {
                            "content": (
                                ("⚠️ " if m["importance"] >= 4 else "ℹ️ ")
                                + f"**{m['key']}**: {m['content']}"
                            ),
                            "score": m.get("final_score", 0.5),
                        }
                        for m in agent_mems
                    ],
                }
            )

        # 3. Recent similar task summaries
        recent_tasks = await self.get_recent_task_memories(
            domain=task_domain, limit=5
        )
        if recent_tasks and effective_query:
            task_dicts = [
                {
                    "content": f"{t['task_title']}: {t['summary']}",
                    "importance": 2,
                    "embedding": None,
                    "created_at": t.get("created_at"),
                }
                for t in recent_tasks
            ]
            ranked_tasks = self._search_engine.search(
                query=effective_query,
                memories=task_dicts,
                query_embedding=None,
                top_k=2,
            )
            if ranked_tasks:
                sections.append(
                    {
                        "header": "### Recent Similar Work",
                        "items": [{"content": t["content"]} for t in ranked_tasks],
                    }
                )

        return sections

    async def build_agent_context(
        self,
        agent_id: UUID,
        task_domain: DomainEnum | None = None,
        query: str = "",
        task_title: str = "",
    ) -> str:
        """
        Build memory context block as plain markdown (legacy compatibility).

        For new code prefer ``build_agent_context_sections()`` + ContextAssembler.
        """
        sections = await self.build_agent_context_sections(
            agent_id=agent_id,
            task_title=task_title,
            task_domain=task_domain,
            query=query,
        )
        if not sections:
            return ""

        parts: list[str] = []
        for section in sections:
            parts.append(section.get("header", ""))
            for item in section.get("items", []):
                parts.append(item.get("content", ""))

        return "\n\n".join(p for p in parts if p)
