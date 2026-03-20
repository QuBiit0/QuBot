"""
Token Counter - Accurate token counting for context budget management.

Supports tiktoken (OpenAI / cl100k_base models) and character-based
estimation for other providers. Also provides model context window lookup.
"""

import math
from functools import lru_cache

# ---------------------------------------------------------------------------
# Context window sizes by model family (prefix matching, longest wins)
# ---------------------------------------------------------------------------
CONTEXT_WINDOWS: dict[str, int] = {
    # OpenAI
    "gpt-4o": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4": 8_192,
    "gpt-3.5-turbo": 16_385,
    "o1": 200_000,
    "o3": 200_000,
    # Anthropic
    "claude-opus-4": 200_000,
    "claude-sonnet-4": 200_000,
    "claude-haiku-4": 200_000,
    "claude-3-5-sonnet": 200_000,
    "claude-3-5-haiku": 200_000,
    "claude-3-opus": 200_000,
    "claude-3-sonnet": 200_000,
    "claude-3-haiku": 200_000,
    # Google
    "gemini-2.0": 1_000_000,
    "gemini-1.5-pro": 1_000_000,
    "gemini-1.5-flash": 1_000_000,
    "gemini-1.0-pro": 32_768,
    # Groq / Meta
    "llama-3.3-70b": 128_000,
    "llama-3.1": 128_000,
    "llama3.2": 128_000,
    "llama3": 8_192,
    "mixtral": 32_768,
    "gemma": 8_192,
    # DeepSeek
    "deepseek-chat": 128_000,
    "deepseek-coder": 128_000,
    # Mistral
    "mistral": 32_768,
    # Qwen
    "qwen": 32_768,
    # Default fallback
    "default": 32_768,
}

# ---------------------------------------------------------------------------
# Token budget fractions by context section (must sum to ≤ 0.80;
# the remaining 20% is reserved for output tokens)
# ---------------------------------------------------------------------------
BUDGET_FRACTIONS: dict[str, float] = {
    "system":  0.15,  # System prompt + agent identity
    "tools":   0.10,  # Tool definition JSON schemas
    "memory":  0.30,  # Retrieved memory context (L1 + L2 + L3)
    "history": 0.25,  # Conversation history (sliding window)
    # Implicit reserve: 0.20 for output tokens
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_context_window(model_name: str) -> int:
    """
    Return the context window size for *model_name*.
    Matches by substring (longest matching key wins).
    """
    model_lower = model_name.lower()
    best_key = ""
    best_size = CONTEXT_WINDOWS["default"]

    for pattern, size in CONTEXT_WINDOWS.items():
        if pattern == "default":
            continue
        if pattern in model_lower and len(pattern) > len(best_key):
            best_key = pattern
            best_size = size

    return best_size


@lru_cache(maxsize=4)
def _get_tiktoken_encoding(model: str):
    """Return a cached tiktoken encoding (None if tiktoken not installed)."""
    try:
        import tiktoken
        try:
            return tiktoken.encoding_for_model(model)
        except KeyError:
            return tiktoken.get_encoding("cl100k_base")
    except ImportError:
        return None


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Count tokens in *text*.

    Uses tiktoken for OpenAI-compatible models; falls back to a conservative
    character-based estimate (1 token ≈ 3.5 chars) for all others.
    """
    if not text:
        return 0

    enc = _get_tiktoken_encoding(model)
    if enc:
        try:
            return len(enc.encode(text))
        except Exception:
            pass

    return math.ceil(len(text) / 3.5)


def count_messages_tokens(messages: list[dict], model: str = "gpt-4o") -> int:
    """
    Count tokens for a list of chat messages.
    Adds ~4 tokens per-message overhead for role/formatting.
    """
    total = 0
    for msg in messages:
        total += 4  # per-message overhead
        for value in msg.values():
            if isinstance(value, str):
                total += count_tokens(value, model)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        total += count_tokens(item.get("text", ""), model)
    return total


# ---------------------------------------------------------------------------
# TokenBudget
# ---------------------------------------------------------------------------

class TokenBudget:
    """
    Token budget allocator for a single LLM call.

    Divides the usable input window into named sections so that each
    piece of context is explicitly limited before the call is made.

    Example::

        budget = TokenBudget("gpt-4o", max_output_tokens=4096)
        if budget.is_over_budget("memory", token_count):
            # trim memory before building the prompt
    """

    def __init__(self, model_name: str, max_output_tokens: int = 4096):
        self.model_name = model_name
        self.context_window = get_context_window(model_name)
        self.max_output_tokens = max_output_tokens

        # Usable input budget: context_window × 75% − output reserve
        self.total_input_budget = max(
            1_000,
            int(self.context_window * 0.75) - max_output_tokens,
        )

        # Per-section allocations
        self.budgets: dict[str, int] = {
            section: int(self.total_input_budget * fraction)
            for section, fraction in BUDGET_FRACTIONS.items()
        }

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_budget(self, section: str) -> int:
        """Return the token budget for *section*."""
        return self.budgets.get(section, 0)

    def is_over_budget(self, section: str, token_count: int) -> bool:
        """True if *token_count* exceeds the budget for *section*."""
        return token_count > self.budgets.get(section, 0)

    def total_used(self, used: dict[str, int]) -> int:
        """Sum of all used tokens."""
        return sum(used.values())

    def is_context_full(
        self, used: dict[str, int], threshold: float = 0.80
    ) -> bool:
        """True when total context usage exceeds *threshold*."""
        return self.total_used(used) >= int(self.total_input_budget * threshold)

    def get_utilization(self, used: dict[str, int]) -> dict[str, float]:
        """Return utilization fraction (0.0 – 1.0) per section."""
        return {
            section: min(1.0, used.get(section, 0) / max(1, budget))
            for section, budget in self.budgets.items()
        }

    def summary(self, used: dict[str, int] | None = None) -> str:
        """Human-readable budget summary for logging / debugging."""
        lines = [
            f"TokenBudget  model={self.model_name}"
            f"  window={self.context_window:,}"
            f"  input_budget={self.total_input_budget:,}"
        ]
        for section, budget in self.budgets.items():
            tokens_used = used.get(section, 0) if used else 0
            pct = int(tokens_used / max(1, budget) * 100)
            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
            lines.append(
                f"  {section:10s} [{bar}] {tokens_used:5d}/{budget:5d} ({pct}%)"
            )
        return "\n".join(lines)
