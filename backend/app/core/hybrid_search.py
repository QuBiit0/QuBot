"""
Hybrid Search Engine - BM25 + vector similarity + temporal decay + MMR.

Implements the same retrieval stack as OpenClaw's memory search:
- BM25 keyword scoring   (textWeight  = 0.30)
- Vector cosine scoring  (vectorWeight = 0.70)
- Temporal decay         score × e^(−λ × age_days),  halfLife = 30 days
- MMR diversity          lambda = 0.70 (relevance vs. diversity balance)

Works with or without the pgvector PostgreSQL extension:
- WITH    pgvector : uses native `<=>` operator + IVFFlat index (fast)
- WITHOUT pgvector : computes cosine similarity in Python from JSONB column
"""

import logging
import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Weights and hyper-parameters
# ---------------------------------------------------------------------------

VECTOR_WEIGHT = 0.70
TEXT_WEIGHT   = 0.30
CANDIDATE_MULTIPLIER = 4        # fetch N × top_k candidates before re-ranking

# Temporal decay: score × e^(−lambda × age_days)
# halfLife=30 → lambda = ln(2)/30
TEMPORAL_DECAY_HALF_LIFE_DAYS = 30.0
TEMPORAL_DECAY_LAMBDA = math.log(2) / TEMPORAL_DECAY_HALF_LIFE_DAYS

# MMR diversity: 0 = max diversity, 1 = max relevance
MMR_LAMBDA = 0.70

# Minimum similarity threshold to include a result
MIN_SCORE_THRESHOLD = 0.10


# ---------------------------------------------------------------------------
# Pure-Python BM25 scorer
# ---------------------------------------------------------------------------

class BM25Scorer:
    """
    Lightweight BM25 implementation that works on a fixed corpus.

    Suitable for small-to-medium in-memory ranking (up to a few thousand
    documents).  For large corpora prefer a dedicated BM25 library.
    """

    K1 = 1.5
    B  = 0.75

    def __init__(self, corpus: list[str]):
        self.corpus = corpus
        self.n = len(corpus)
        self.avgdl = sum(len(d.split()) for d in corpus) / max(1, self.n)
        self.doc_freqs: list[Counter] = [Counter(d.lower().split()) for d in corpus]
        self.idf: dict[str, float] = self._compute_idf()

    def _compute_idf(self) -> dict[str, float]:
        df: dict[str, int] = {}
        for freq in self.doc_freqs:
            for term in freq:
                df[term] = df.get(term, 0) + 1

        idf: dict[str, float] = {}
        for term, n_docs in df.items():
            idf[term] = math.log(1 + (self.n - n_docs + 0.5) / (n_docs + 0.5))
        return idf

    def score(self, query: str, doc_idx: int) -> float:
        query_terms = query.lower().split()
        freq = self.doc_freqs[doc_idx]
        dl = sum(freq.values())
        score = 0.0
        for term in query_terms:
            tf = freq.get(term, 0)
            if tf == 0:
                continue
            idf = self.idf.get(term, 0.0)
            num = tf * (self.K1 + 1)
            den = tf + self.K1 * (1 - self.B + self.B * dl / max(1, self.avgdl))
            score += idf * (num / max(den, 1e-9))
        return score


# ---------------------------------------------------------------------------
# Cosine similarity (pure Python, fallback)
# ---------------------------------------------------------------------------

def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _jaccard(a: str, b: str) -> float:
    """Token-level Jaccard similarity for MMR diversity."""
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    if not set_a and not set_b:
        return 1.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / max(1, len(union))


# ---------------------------------------------------------------------------
# Temporal decay
# ---------------------------------------------------------------------------

def apply_temporal_decay(score: float, created_at: datetime | None) -> float:
    """
    Reduce *score* based on how old the memory is.

    Evergreen formula: score × e^(−lambda × age_days)
    A memory 30 days old retains ~50% of its score.
    """
    if created_at is None:
        return score

    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    age_days = max(0.0, (now - created_at).total_seconds() / 86_400)
    decay = math.exp(-TEMPORAL_DECAY_LAMBDA * age_days)
    return score * decay


# ---------------------------------------------------------------------------
# MMR re-ranking
# ---------------------------------------------------------------------------

def mmr_rerank(
    candidates: list[dict],
    top_k: int,
    lmbda: float = MMR_LAMBDA,
) -> list[dict]:
    """
    Maximal Marginal Relevance re-ranking.

    Selects iteratively: item = argmax [ λ·rel(i) − (1−λ)·max_sim(i, selected) ]

    Args:
        candidates : list of dicts with keys ``content`` and ``final_score``
        top_k      : number of results to return
        lmbda      : 0 = max diversity, 1 = max relevance
    """
    if len(candidates) <= top_k:
        return candidates

    selected: list[dict] = []
    remaining = list(candidates)

    while remaining and len(selected) < top_k:
        best_idx = -1
        best_val = float("-inf")

        for idx, candidate in enumerate(remaining):
            relevance = candidate.get("final_score", 0.0)

            if not selected:
                diversity = 0.0
            else:
                diversity = max(
                    _jaccard(
                        candidate.get("content", ""),
                        s.get("content", ""),
                    )
                    for s in selected
                )

            mmr_val = lmbda * relevance - (1 - lmbda) * diversity
            if mmr_val > best_val:
                best_val = mmr_val
                best_idx = idx

        if best_idx < 0:
            break

        selected.append(remaining.pop(best_idx))

    return selected


# ---------------------------------------------------------------------------
# HybridSearchEngine
# ---------------------------------------------------------------------------

class HybridSearchEngine:
    """
    Full retrieval pipeline: BM25 + vector cosine + temporal decay + MMR.

    Designed to work with the ``agent_memory`` and ``global_memory`` tables.
    Accepts a list of *memory dicts* (already loaded from the DB) so the
    engine itself stays stateless and testable without a DB connection.
    """

    def __init__(
        self,
        vector_weight: float = VECTOR_WEIGHT,
        text_weight: float = TEXT_WEIGHT,
        enable_temporal_decay: bool = True,
        enable_mmr: bool = True,
    ):
        self.vector_weight = vector_weight
        self.text_weight = text_weight
        self.enable_temporal_decay = enable_temporal_decay
        self.enable_mmr = enable_mmr

    def search(
        self,
        query: str,
        memories: list[dict],
        query_embedding: list[float] | None,
        top_k: int = 8,
    ) -> list[dict]:
        """
        Rank *memories* against *query* and return the top_k best.

        Each memory dict is expected to have at minimum:
        - ``content``    : str
        - ``embedding``  : list[float] | None
        - ``importance`` : int | float (1–5)
        - ``created_at`` : datetime | None

        Returns the ranked list with an added ``final_score`` key.
        """
        if not memories:
            return []

        top_k = max(1, top_k)
        # Fetch more candidates for MMR re-ranking
        fetch_k = min(len(memories), top_k * CANDIDATE_MULTIPLIER)

        # --- BM25 scoring -------------------------------------------------
        corpus = [m.get("content", "") for m in memories]
        bm25 = BM25Scorer(corpus)
        bm25_scores = [bm25.score(query, i) for i in range(len(corpus))]

        # Normalize BM25 to [0, 1]
        max_bm25 = max(bm25_scores) if bm25_scores else 1.0
        if max_bm25 > 0:
            bm25_scores = [s / max_bm25 for s in bm25_scores]

        # --- Vector scoring -----------------------------------------------
        vec_scores: list[float] = []
        for mem in memories:
            emb = mem.get("embedding")
            if query_embedding and emb:
                try:
                    if isinstance(emb, str):
                        import json as _json
                        emb = _json.loads(emb)
                    vec_scores.append(_cosine(query_embedding, emb))
                except Exception:
                    vec_scores.append(0.0)
            else:
                vec_scores.append(0.0)

        # --- Hybrid fusion ------------------------------------------------
        candidates: list[dict] = []
        for i, mem in enumerate(memories):
            importance_boost = (mem.get("importance", 3) - 1) / 4.0 * 0.15
            hybrid_score = (
                self.vector_weight * vec_scores[i]
                + self.text_weight  * bm25_scores[i]
                + importance_boost
            )

            # Apply temporal decay
            if self.enable_temporal_decay:
                hybrid_score = apply_temporal_decay(
                    hybrid_score,
                    mem.get("created_at"),
                )

            if hybrid_score >= MIN_SCORE_THRESHOLD:
                candidates.append({**mem, "final_score": round(hybrid_score, 4)})

        # Sort descending by score
        candidates.sort(key=lambda x: x["final_score"], reverse=True)
        candidates = candidates[:fetch_k]

        # --- MMR re-ranking -----------------------------------------------
        if self.enable_mmr and len(candidates) > top_k:
            candidates = mmr_rerank(candidates, top_k)
        else:
            candidates = candidates[:top_k]

        return candidates

    async def get_query_embedding(
        self, query: str, openai_api_key: str | None
    ) -> list[float] | None:
        """
        Generate an embedding for *query* using OpenAI text-embedding-3-small.
        Returns None on any failure so BM25-only fallback is used.
        """
        if not openai_api_key:
            return None
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=openai_api_key)
            resp = await client.embeddings.create(
                model="text-embedding-3-small",
                input=query[:8_000],
            )
            return resp.data[0].embedding
        except Exception as exc:
            logger.debug("Embedding fetch failed (using BM25 only): %s", exc)
            return None
