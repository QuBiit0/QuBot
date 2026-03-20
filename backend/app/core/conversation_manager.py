"""
Conversation Manager - Redis-backed working memory with sliding window.

Implements L1 (Working Memory) from the memory architecture:
- Stores per-session conversation history in Redis
- Sliding window: keeps last MAX_MESSAGES messages
- TTL: sessions expire after SESSION_TTL_HOURS (default 24h)
- Compaction summaries stored alongside messages
- Falls back gracefully when Redis is unavailable

Key design:
  session_id → Redis key prefix
  Messages stored as JSON in a Redis List (RPUSH / LRANGE)
  Compaction summary stored as a Redis String
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_MESSAGES = 50           # Maximum messages to store per session
SESSION_TTL_HOURS = 24      # Session TTL in hours
SESSION_TTL_SECONDS = SESSION_TTL_HOURS * 3_600

# Redis key prefixes
_MSG_KEY   = "conv:msgs:"   # → JSON list of messages
_SUM_KEY   = "conv:sum:"    # → compaction summary string
_META_KEY  = "conv:meta:"   # → session metadata JSON


class ConversationManager:
    """
    Redis-backed conversation history manager.

    Each *session_id* maps to an independent conversation context.
    Use ``load_session`` before processing a request and
    ``save_session`` after to persist the updated history.

    Example::

        mgr = ConversationManager(redis_client)
        history, summary = await mgr.load_session(session_id)

        # ... run LLM, collect new messages ...

        await mgr.save_session(session_id, history, summary)
    """

    def __init__(self, redis_client: Any | None = None):
        """
        Args:
            redis_client: An async redis client (e.g. ``redis.asyncio.Redis``).
                          Pass None to disable persistence (in-memory fallback).
        """
        self._redis = redis_client
        # In-memory fallback when Redis is unavailable
        self._local: dict[str, dict] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    async def load_session(
        self, session_id: str
    ) -> tuple[list[dict], str | None]:
        """
        Load conversation history and compaction summary for *session_id*.

        Returns:
            (messages, compaction_summary_or_None)
        """
        if self._redis:
            return await self._redis_load(session_id)
        return self._local_load(session_id)

    async def save_session(
        self,
        session_id: str,
        messages: list[dict],
        compaction_summary: str | None = None,
    ) -> None:
        """
        Persist conversation history and compaction summary for *session_id*.

        Applies sliding window: keeps only the last MAX_MESSAGES messages.
        """
        # Sliding window — trim oldest messages
        if len(messages) > MAX_MESSAGES:
            messages = messages[-MAX_MESSAGES:]

        if self._redis:
            await self._redis_save(session_id, messages, compaction_summary)
        else:
            self._local_save(session_id, messages, compaction_summary)

    async def append_messages(
        self,
        session_id: str,
        new_messages: list[dict],
    ) -> list[dict]:
        """
        Load session, append *new_messages*, save, and return the full history.
        """
        messages, summary = await self.load_session(session_id)
        messages.extend(new_messages)
        await self.save_session(session_id, messages, summary)
        return messages

    async def set_compaction_summary(
        self, session_id: str, summary: str
    ) -> None:
        """Update the compaction summary for *session_id*."""
        messages, _ = await self.load_session(session_id)
        await self.save_session(session_id, messages, summary)

    async def delete_session(self, session_id: str) -> None:
        """Delete all data for *session_id*."""
        if self._redis:
            try:
                await self._redis.delete(
                    _MSG_KEY + session_id,
                    _SUM_KEY + session_id,
                    _META_KEY + session_id,
                )
            except Exception as exc:
                logger.warning("Redis delete failed for %s: %s", session_id, exc)
        else:
            self._local.pop(session_id, None)

    async def get_session_info(self, session_id: str) -> dict:
        """Return metadata about a session (message count, last updated)."""
        messages, summary = await self.load_session(session_id)
        return {
            "session_id": session_id,
            "message_count": len(messages),
            "has_summary": bool(summary),
            "summary_preview": (summary or "")[:120],
        }

    # ── Redis backend ─────────────────────────────────────────────────────────

    async def _redis_load(
        self, session_id: str
    ) -> tuple[list[dict], str | None]:
        try:
            raw_msgs = await self._redis.get(_MSG_KEY + session_id)
            raw_sum  = await self._redis.get(_SUM_KEY + session_id)

            messages: list[dict] = json.loads(raw_msgs) if raw_msgs else []
            summary: str | None  = raw_sum.decode() if raw_sum else None
            return messages, summary
        except Exception as exc:
            logger.warning("Redis load failed for %s: %s", session_id, exc)
            return [], None

    async def _redis_save(
        self,
        session_id: str,
        messages: list[dict],
        summary: str | None,
    ) -> None:
        try:
            pipe = self._redis.pipeline()
            pipe.set(
                _MSG_KEY + session_id,
                json.dumps(messages, default=str),
                ex=SESSION_TTL_SECONDS,
            )
            if summary is not None:
                pipe.set(
                    _SUM_KEY + session_id,
                    summary,
                    ex=SESSION_TTL_SECONDS,
                )
            # Update metadata
            pipe.set(
                _META_KEY + session_id,
                json.dumps({
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "message_count": len(messages),
                }),
                ex=SESSION_TTL_SECONDS,
            )
            await pipe.execute()
        except Exception as exc:
            logger.warning("Redis save failed for %s: %s", session_id, exc)

    # ── In-memory fallback ────────────────────────────────────────────────────

    def _local_load(self, session_id: str) -> tuple[list[dict], str | None]:
        data = self._local.get(session_id, {})
        return data.get("messages", []), data.get("summary")

    def _local_save(
        self,
        session_id: str,
        messages: list[dict],
        summary: str | None,
    ) -> None:
        self._local[session_id] = {
            "messages": messages,
            "summary": summary,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Singleton factory (initialized once during app startup)
# ---------------------------------------------------------------------------

_manager: ConversationManager | None = None


def get_conversation_manager() -> ConversationManager:
    """Return the application-wide ConversationManager instance."""
    global _manager
    if _manager is None:
        _manager = ConversationManager(redis_client=None)
        logger.warning(
            "ConversationManager: Redis not initialized — using in-memory fallback. "
            "Call init_conversation_manager(redis_client) at startup."
        )
    return _manager


def init_conversation_manager(redis_client: Any) -> ConversationManager:
    """Initialize the global ConversationManager with a Redis client."""
    global _manager
    _manager = ConversationManager(redis_client=redis_client)
    logger.info("ConversationManager initialized with Redis client.")
    return _manager
