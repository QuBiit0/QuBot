"""
Context Budget Manager - Assembles context sections within token budgets.

Implements:
- Soft-trim   : keep head + tail of large text, insert size notice
- Hard-clear  : replace extremely large content with a placeholder
- System prompt truncation (from end)
- Memory section prioritization (drop lowest-score items first)
- Conversation history sliding window + tool-result pruning
- Tool definition prioritization by task relevance
"""

import json
import logging
from typing import Any

from .token_counter import TokenBudget, count_tokens, count_messages_tokens

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants (mirrors OpenClaw defaults)
# ---------------------------------------------------------------------------

SOFT_TRIM_MAX_CHARS = 4_000          # Start soft-trimming above this
SOFT_TRIM_HEAD_TAIL = 1_500          # Keep this many chars on each side
HARD_CLEAR_THRESHOLD_CHARS = 50_000  # Hard-clear above this
PROTECTED_ASSISTANT_TURNS = 3        # Never prune tool results near last N turns


# ---------------------------------------------------------------------------
# Text manipulation helpers
# ---------------------------------------------------------------------------

def soft_trim(text: str, max_chars: int = SOFT_TRIM_MAX_CHARS) -> str:
    """Trim long text keeping head and tail with a size notice in between."""
    if len(text) <= max_chars:
        return text
    trimmed = len(text) - 2 * SOFT_TRIM_HEAD_TAIL
    return (
        text[:SOFT_TRIM_HEAD_TAIL]
        + f"\n... [{trimmed:,} chars trimmed] ...\n"
        + text[-SOFT_TRIM_HEAD_TAIL:]
    )


def hard_clear(text: str, threshold: int = HARD_CLEAR_THRESHOLD_CHARS) -> str:
    """Replace oversized content with a lightweight placeholder."""
    if len(text) <= threshold:
        return text
    return f"[Content cleared — original size: {len(text):,} chars]"


# ---------------------------------------------------------------------------
# ContextAssembler
# ---------------------------------------------------------------------------

class ContextAssembler:
    """
    Assembles and trims context sections to stay within a TokenBudget.

    Call each ``fit_*`` method before adding the section to the prompt.
    The assembler never modifies the originals — all methods return new
    (potentially trimmed) objects.
    """

    def __init__(self, budget: TokenBudget):
        self.budget = budget

    # ── System prompt ─────────────────────────────────────────────────────────

    def fit_system_prompt(self, system_prompt: str) -> str:
        """Truncate system prompt to fit its section budget."""
        budget = self.budget.get_budget("system")
        tokens = count_tokens(system_prompt, self.budget.model_name)
        if tokens <= budget:
            return system_prompt

        keep_ratio = budget / max(1, tokens)
        target_chars = int(len(system_prompt) * keep_ratio)
        removed = tokens - budget
        logger.debug("fit_system_prompt: truncated %d tokens", removed)
        return (
            system_prompt[:target_chars]
            + f"\n[System prompt truncated — {removed} tokens removed]"
        )

    # ── Memory context ────────────────────────────────────────────────────────

    def fit_memory_context(
        self,
        sections: list[dict[str, Any]],
    ) -> str:
        """
        Fit memory sections within the memory budget.

        *sections* is a list of::

            {
                "header": str,           # e.g. "### Your Memory"
                "items": [
                    {"content": str, "score": float, ...},  # sorted best-first
                    ...
                ]
            }

        Items within a section are added until the budget is exhausted;
        individual items are soft-trimmed if they are very long.
        """
        budget = self.budget.get_budget("memory")
        used = 0
        result_parts: list[str] = []

        for section in sections:
            header = section.get("header", "")
            items = section.get("items", [])

            header_tokens = count_tokens(header, self.budget.model_name)
            if used + header_tokens > budget:
                break

            section_parts = [header]
            used += header_tokens

            for item in items:
                content = soft_trim(str(item.get("content", "")), max_chars=600)
                item_tokens = count_tokens(content, self.budget.model_name)
                if used + item_tokens > budget:
                    break
                section_parts.append(content)
                used += item_tokens

            if len(section_parts) > 1:
                result_parts.append("\n".join(section_parts))

        logger.debug(
            "fit_memory_context: %d / %d tokens used", used, budget
        )
        return "\n\n".join(result_parts)

    # ── Conversation history ───────────────────────────────────────────────────

    def fit_conversation_history(
        self,
        messages: list[dict],
        compaction_summary: str | None = None,
    ) -> tuple[list[dict], str | None]:
        """
        Fit conversation history within the history budget.

        Steps:
        1. Apply tool-result pruning (soft-trim / hard-clear old results).
        2. If still over budget, drop oldest messages, keeping most recent.

        Returns:
            (fitted_messages, compaction_summary)  — summary is passed
            through unchanged; the caller injects it if needed.
        """
        budget = self.budget.get_budget("history")

        pruned = self._prune_tool_results(messages)

        total_tokens = count_messages_tokens(pruned, self.budget.model_name)
        if total_tokens <= budget:
            return pruned, compaction_summary

        # Drop oldest messages until we fit
        kept: list[dict] = []
        kept_tokens = 0
        for msg in reversed(pruned):
            msg_tokens = count_messages_tokens([msg], self.budget.model_name)
            if kept_tokens + msg_tokens > budget and kept:
                break
            kept.insert(0, msg)
            kept_tokens += msg_tokens

        dropped = len(pruned) - len(kept)
        if dropped:
            logger.debug(
                "fit_conversation_history: dropped %d messages to fit %d budget",
                dropped,
                budget,
            )
        return kept, compaction_summary

    def _prune_tool_results(self, messages: list[dict]) -> list[dict]:
        """
        Prune old tool results in-place (returns a new list).

        Protection rules:
        - Tool results adjacent to the last PROTECTED_ASSISTANT_TURNS
          assistant messages are never pruned.
        - Oversized results get soft-trimmed or hard-cleared.
        """
        if not messages:
            return messages

        # Indices of assistant turns (we protect the last N)
        assistant_idxs = [
            i for i, m in enumerate(messages) if m.get("role") == "assistant"
        ]
        protected_assistants = set(assistant_idxs[-PROTECTED_ASSISTANT_TURNS:])

        # Protect tool results immediately preceding protected assistants
        protected_tools: set[int] = set()
        for idx in protected_assistants:
            for j in range(max(0, idx - 3), idx):
                if messages[j].get("role") == "tool":
                    protected_tools.add(j)

        result: list[dict] = []
        for i, msg in enumerate(messages):
            if msg.get("role") != "tool" or i in protected_tools:
                result.append(msg)
                continue

            content = msg.get("content", "")
            if isinstance(content, str):
                if len(content) > HARD_CLEAR_THRESHOLD_CHARS:
                    msg = {**msg, "content": hard_clear(content)}
                elif len(content) > SOFT_TRIM_MAX_CHARS:
                    msg = {**msg, "content": soft_trim(content)}

            result.append(msg)

        return result

    # ── Tools ─────────────────────────────────────────────────────────────────

    def fit_tools(
        self,
        tools: list[Any],
        task_hint: str = "",
    ) -> list[Any]:
        """
        Fit tool definitions within the tools budget.

        If all tools fit, they are returned unchanged.  Otherwise the tools
        most relevant to *task_hint* are kept (scored by name+description
        keyword overlap).
        """
        if not tools:
            return tools

        budget = self.budget.get_budget("tools")

        try:
            tools_json = json.dumps(
                [t if isinstance(t, dict) else vars(t) for t in tools],
                default=str,
            )
        except Exception:
            tools_json = str(tools)

        total_tokens = count_tokens(tools_json, self.budget.model_name)
        if total_tokens <= budget:
            return tools

        # Score tools by relevance to task hint
        hint_words = set(task_hint.lower().split()) if task_hint else set()
        scored: list[tuple[int, Any]] = []
        for tool in tools:
            name = (
                tool.get("name", "") if isinstance(tool, dict)
                else getattr(tool, "name", "")
            )
            desc = (
                tool.get("description", "") if isinstance(tool, dict)
                else getattr(tool, "description", "")
            )
            text = (name + " " + desc).lower()
            score = sum(1 for w in hint_words if w in text)
            scored.append((score, tool))

        scored.sort(key=lambda x: x[0], reverse=True)

        per_tool = max(1, total_tokens // len(tools))
        kept: list[Any] = []
        used = 0
        for _, tool in scored:
            if used + per_tool > budget and kept:
                break
            kept.append(tool)
            used += per_tool

        logger.debug(
            "fit_tools: keeping %d/%d tools within %d token budget",
            len(kept), len(tools), budget,
        )
        return kept
