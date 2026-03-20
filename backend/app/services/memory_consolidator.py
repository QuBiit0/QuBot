"""
Memory Consolidator - Chunking, deduplication, and cleanup of agent memories.

Phase 5 implementation:

1. Chunking   : Splits long memory content into ~400-token chunks with 80-token
                overlap, storing each chunk as an independent AgentMemory entry.
                Inspired by OpenClaw's 400-token / 80-overlap chunking strategy.

2. Dedup      : Detects and merges near-duplicate memories using SHA-256 hash
                (exact dedup) and cosine similarity > SIMILARITY_THRESHOLD
                (semantic dedup).  The higher-importance version is kept.

3. Cleanup    : Removes stale low-importance memories that haven't been accessed
                in STALE_DAYS_THRESHOLD days.

4. Consolidation run  : Call ``consolidate_agent(agent_id)`` to run all three
                        steps for a single agent.  Can be called from a
                        background task or a scheduled job.
"""

import hashlib
import logging
import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, select

from ..models.memory import AgentMemory

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CHUNK_SIZE_TOKENS    = 400   # Target tokens per chunk
CHUNK_OVERLAP_TOKENS =  80   # Overlap between consecutive chunks
CHARS_PER_TOKEN      = 3.5   # Conservative estimate (1 token ≈ 3.5 chars)

CHUNK_SIZE_CHARS     = int(CHUNK_SIZE_TOKENS    * CHARS_PER_TOKEN)   # ≈ 1 400
CHUNK_OVERLAP_CHARS  = int(CHUNK_OVERLAP_TOKENS * CHARS_PER_TOKEN)   # ≈  280

SIMILARITY_THRESHOLD = 0.92  # Cosine similarity above which memories are merged
STALE_DAYS_THRESHOLD = 90    # Days without access before low-importance pruning
STALE_MIN_IMPORTANCE = 2     # Only prune memories with importance ≤ this value


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(text: str) -> str:
    return hashlib.sha256(text.strip().encode()).hexdigest()[:64]


def _cosine(a: list[float], b: list[float]) -> float:
    dot  = sum(x * y for x, y in zip(a, b))
    na   = math.sqrt(sum(x * x for x in a))
    nb   = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def chunk_text(text: str) -> list[str]:
    """
    Split *text* into overlapping chunks of approximately CHUNK_SIZE_CHARS.

    Strategy: split on sentence boundaries (". ") when possible; fall back to
    hard character splits.  Each chunk overlaps the previous by CHUNK_OVERLAP_CHARS.
    """
    if len(text) <= CHUNK_SIZE_CHARS:
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE_CHARS

        if end < len(text):
            # Try to break at a sentence boundary within the last 200 chars
            boundary = text.rfind(". ", start + CHUNK_SIZE_CHARS - 200, end)
            if boundary != -1:
                end = boundary + 2  # Include the period and space

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Advance with overlap
        start = end - CHUNK_OVERLAP_CHARS
        if start <= 0:
            break

    return chunks if chunks else [text]


# ---------------------------------------------------------------------------
# MemoryConsolidator
# ---------------------------------------------------------------------------

class MemoryConsolidator:
    """
    Consolidates agent memories: chunking, deduplication, and stale cleanup.

    Usage (from a background task)::

        consolidator = MemoryConsolidator(session)
        stats = await consolidator.consolidate_agent(agent_id)
        logger.info("Consolidation done: %s", stats)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Public entry point ────────────────────────────────────────────────────

    async def consolidate_agent(self, agent_id: UUID) -> dict:
        """
        Run full consolidation pipeline for *agent_id*.

        Returns a stats dict with counts of actions taken.
        """
        stats = {
            "chunked": 0,
            "duplicates_removed": 0,
            "stale_removed": 0,
        }

        stats["chunked"]            = await self._chunk_long_memories(agent_id)
        stats["duplicates_removed"] = await self._deduplicate(agent_id)
        stats["stale_removed"]      = await self._prune_stale(agent_id)

        logger.info(
            "Consolidation for agent %s: chunked=%d dedup=%d stale=%d",
            agent_id,
            stats["chunked"],
            stats["duplicates_removed"],
            stats["stale_removed"],
        )
        return stats

    # ── Step 1: Chunking ──────────────────────────────────────────────────────

    async def _chunk_long_memories(self, agent_id: UUID) -> int:
        """
        Split memories longer than CHUNK_SIZE_CHARS into smaller overlapping
        chunks.  The original memory is replaced by the first chunk; subsequent
        chunks are added as new entries with the same key + a sequence suffix.
        """
        result = await self.session.execute(
            select(AgentMemory)
            .where(AgentMemory.agent_id == agent_id)
            .where(AgentMemory.content != "")
        )
        all_memories = list(result.scalars().all())

        created_count = 0

        for mem in all_memories:
            if len(mem.content) <= CHUNK_SIZE_CHARS:
                continue

            chunks = chunk_text(mem.content)
            if len(chunks) <= 1:
                continue

            # Update original memory with first chunk
            mem.content      = chunks[0]
            mem.content_hash = _sha256(chunks[0])
            mem.updated_at   = datetime.utcnow()

            # Create new memories for remaining chunks
            for i, chunk in enumerate(chunks[1:], start=2):
                chunk_mem = AgentMemory(
                    agent_id   = agent_id,
                    key        = f"{mem.key}__chunk{i}",
                    content    = chunk,
                    importance = max(1, mem.importance - 1),  # slightly lower
                    content_hash = _sha256(chunk),
                )
                self.session.add(chunk_mem)
                created_count += 1

        if created_count or any(len(m.content) <= CHUNK_SIZE_CHARS for m in all_memories):
            await self.session.commit()

        return created_count

    # ── Step 2: Deduplication ─────────────────────────────────────────────────

    async def _deduplicate(self, agent_id: UUID) -> int:
        """
        Remove near-duplicate memories.

        Pass 1 (exact): group by content_hash and keep highest-importance entry.
        Pass 2 (semantic): for entries without embeddings, fall back to
                           normalised text overlap (Jaccard on tokens).
        """
        result = await self.session.execute(
            select(AgentMemory)
            .where(AgentMemory.agent_id == agent_id)
            .order_by(desc(AgentMemory.importance), desc(AgentMemory.last_accessed))
        )
        memories = list(result.scalars().all())
        if not memories:
            return 0

        to_delete: set[UUID] = set()

        # ── Pass 1: exact hash dedup ──────────────────────────────────────────
        seen_hashes: dict[str, AgentMemory] = {}
        for mem in memories:
            h = mem.content_hash or _sha256(mem.content)
            if h in seen_hashes:
                # Keep the one with higher importance; delete the other
                existing = seen_hashes[h]
                if mem.importance > existing.importance:
                    to_delete.add(existing.id)
                    seen_hashes[h] = mem
                else:
                    to_delete.add(mem.id)
            else:
                seen_hashes[h] = mem

        # ── Pass 2: semantic (vector or Jaccard) dedup ────────────────────────
        survivors = [m for m in memories if m.id not in to_delete]

        for i, mem_a in enumerate(survivors):
            if mem_a.id in to_delete:
                continue
            for mem_b in survivors[i + 1:]:
                if mem_b.id in to_delete:
                    continue

                sim = self._similarity(mem_a, mem_b)
                if sim >= SIMILARITY_THRESHOLD:
                    # Keep higher importance; delete other
                    if mem_a.importance >= mem_b.importance:
                        to_delete.add(mem_b.id)
                    else:
                        to_delete.add(mem_a.id)

        if not to_delete:
            return 0

        # Delete in bulk
        for mid in to_delete:
            result_m = await self.session.execute(
                select(AgentMemory).where(AgentMemory.id == mid)
            )
            mem_obj = result_m.scalar_one_or_none()
            if mem_obj:
                await self.session.delete(mem_obj)

        await self.session.commit()
        return len(to_delete)

    def _similarity(self, a: AgentMemory, b: AgentMemory) -> float:
        """Compute similarity between two memories (vector if available, Jaccard otherwise)."""
        if a.embedding and b.embedding:
            try:
                return _cosine(a.embedding, b.embedding)
            except Exception:
                pass
        # Jaccard on token sets
        tokens_a = set(a.content.lower().split())
        tokens_b = set(b.content.lower().split())
        if not tokens_a and not tokens_b:
            return 1.0
        return len(tokens_a & tokens_b) / max(1, len(tokens_a | tokens_b))

    # ── Step 3: Stale pruning ─────────────────────────────────────────────────

    async def _prune_stale(self, agent_id: UUID) -> int:
        """
        Remove low-importance memories not accessed for STALE_DAYS_THRESHOLD days.

        Only memories with importance ≤ STALE_MIN_IMPORTANCE are eligible.
        """
        cutoff = datetime.utcnow() - timedelta(days=STALE_DAYS_THRESHOLD)

        result = await self.session.execute(
            select(AgentMemory)
            .where(AgentMemory.agent_id == agent_id)
            .where(AgentMemory.importance <= STALE_MIN_IMPORTANCE)
            .where(AgentMemory.last_accessed <= cutoff)
        )
        stale = list(result.scalars().all())

        for mem in stale:
            await self.session.delete(mem)

        if stale:
            await self.session.commit()

        return len(stale)
