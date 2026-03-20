"""
Context Compactor - Summarizes old conversation history when context fills up.

Inspired by OpenClaw's compaction mechanism:
1. Detect context > COMPACTION_THRESHOLD
2. Memory flush: extract durable facts via LLM (silent agentic turn)
3. Summarize older messages into a compact summary (keep recent N turns intact)
4. Inject summary as synthetic context at conversation start

Pruning (separate from compaction):
- Soft-trim large tool results in-memory without touching history
- Hard-clear extremely large results
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ContextCompactor:
    """
    Compacts conversation history when context window approaches capacity.

    Designed to be called from inside the agent execution loop after every
    LLM response when ``budget.is_context_full(used)`` returns True.
    """

    COMPACTION_THRESHOLD = 0.80   # Trigger at 80% context usage
    KEEP_RECENT_TURNS = 3          # Always keep last N turns intact
    SUMMARY_MAX_WORDS = 600        # Rough limit for compaction summaries

    def __init__(self, llm_provider: Any | None = None):
        """
        Args:
            llm_provider: Optional provider instance used for LLM-based
                          summarization and fact extraction.  Falls back to
                          a heuristic summary when None.
        """
        self.llm = llm_provider

    # ── Entry point ───────────────────────────────────────────────────────────

    def should_compact(self, used_tokens: int, context_window: int) -> bool:
        """Return True when compaction should be triggered."""
        return used_tokens >= int(context_window * self.COMPACTION_THRESHOLD)

    async def compact(
        self,
        messages: list[dict],
        existing_summary: str | None = None,
    ) -> tuple[list[dict], str]:
        """
        Compact conversation history.

        Splits messages into:
        - *to_summarize*: everything older than KEEP_RECENT_TURNS × 2
        - *to_keep*: most recent messages (always preserved verbatim)

        Returns:
            (kept_messages, new_compaction_summary)
        """
        min_messages = self.KEEP_RECENT_TURNS * 2
        if len(messages) <= min_messages:
            return messages, existing_summary or ""

        split_point = len(messages) - min_messages
        to_summarize = messages[:split_point]
        to_keep = messages[split_point:]

        new_summary = await self._summarize(to_summarize, existing_summary)
        logger.debug(
            "compact: summarized %d messages → %d chars summary, kept %d messages",
            len(to_summarize),
            len(new_summary),
            len(to_keep),
        )
        return to_keep, new_summary

    # ── Memory flush ─────────────────────────────────────────────────────────

    async def extract_key_facts(self, messages: list[dict]) -> list[str]:
        """
        Extract durable facts from a conversation before compaction (memory flush).

        This is the "silent agentic turn" that runs just before compaction so
        important information is preserved in the agent's long-term memory.

        Returns:
            List of fact strings (max 10).
        """
        if not self.llm or not messages:
            return []

        conversation_text = self._messages_to_text(messages[-20:])

        extraction_prompt = [
            {
                "role": "user",
                "content": (
                    "Extract the most important facts, decisions, and learned "
                    "information from this conversation that should be remembered "
                    "long-term.\n"
                    "Return ONLY a JSON array of strings — no explanation.\n"
                    "Maximum 10 items, each under 150 words.\n\n"
                    f"Conversation:\n{conversation_text}"
                ),
            }
        ]

        try:
            response = await self.llm.complete(messages=extraction_prompt)
            content = (response.content or "").strip()

            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                facts = json.loads(content[start:end])
                return [str(f).strip() for f in facts if f][:10]
        except Exception as exc:
            logger.warning("extract_key_facts failed: %s", exc)

        return []

    # ── Summary injection ─────────────────────────────────────────────────────

    def inject_summary(
        self,
        messages: list[dict],
        summary: str,
    ) -> list[dict]:
        """
        Prepend a compaction summary to *messages* as a synthetic
        user/assistant exchange so the model has prior-conversation context.
        """
        if not summary:
            return messages

        return [
            {
                "role": "user",
                "content": (
                    "[Context from earlier in this conversation]\n" + summary
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "Understood. I have the context from our earlier conversation."
                ),
            },
        ] + messages

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _summarize(
        self,
        messages: list[dict],
        existing_summary: str | None = None,
    ) -> str:
        """Generate a compact summary with LLM (falls back to heuristic)."""
        if self.llm:
            return await self._llm_summarize(messages, existing_summary)
        return self._heuristic_summary(messages, existing_summary)

    async def _llm_summarize(
        self,
        messages: list[dict],
        existing_summary: str | None,
    ) -> str:
        parts: list[str] = []
        if existing_summary:
            parts.append(f"Previous summary:\n{existing_summary}\n")
        parts.append("Messages to summarize:")
        parts.append(self._messages_to_text(messages))

        prompt = [
            {
                "role": "user",
                "content": (
                    "Create a concise summary of this conversation history.\n"
                    "Focus on: decisions made, tasks completed, key findings, "
                    "open questions, and important context.\n"
                    f"Be dense but comprehensive. Maximum {self.SUMMARY_MAX_WORDS} words.\n\n"
                    + "\n".join(parts)
                ),
            }
        ]

        try:
            response = await self.llm.complete(messages=prompt)
            text = (response.content or "").strip()
            if text:
                return "[Conversation Summary]\n" + text
        except Exception as exc:
            logger.warning("LLM compaction failed: %s", exc)

        return self._heuristic_summary(messages, existing_summary)

    def _heuristic_summary(
        self,
        messages: list[dict],
        existing_summary: str | None,
    ) -> str:
        """Fallback summary without LLM."""
        user_msgs = [m for m in messages if m.get("role") == "user"]
        asst_msgs = [m for m in messages if m.get("role") == "assistant"]

        parts: list[str] = []
        if existing_summary:
            parts.append(existing_summary)

        parts.append(
            f"[Compacted: {len(messages)} messages — "
            f"{len(user_msgs)} user / {len(asst_msgs)} assistant]"
        )

        if user_msgs:
            first = user_msgs[0].get("content", "")
            if isinstance(first, str):
                parts.append(f"Original request: {first[:300]}")

        if asst_msgs:
            last = asst_msgs[-1].get("content", "")
            if isinstance(last, str) and last:
                parts.append(f"Last result: {last[:400]}")

        return "\n".join(parts)

    def _messages_to_text(self, messages: list[dict]) -> str:
        parts: list[str] = []
        for msg in messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    item.get("text", "") for item in content
                    if isinstance(item, dict)
                )
            if isinstance(content, str) and content:
                parts.append(f"{role}: {content[:500]}")
        return "\n".join(parts)
