"""
Loop Detection Service - Prevents agents from getting stuck in tool-call loops.

Detects patterns like:
- Generic repeat: same tool + same params
- Known poll no-progress: repeating poll-like tools
- Ping-pong: alternating A/B patterns
"""

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


class LoopType(str, Enum):
    """Types of loop patterns detected."""

    GENERIC_REPEAT = "genericRepeat"
    KNOWN_POLL_NO_PROGRESS = "knownPollNoProgress"
    PING_PONG = "pingPong"
    UNKNOWN = "unknown"


@dataclass
class LoopEvent:
    """A tool call event for loop detection."""

    tool_name: str
    parameters: dict[str, Any]
    output_hash: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class LoopDetectionResult:
    """Result of loop detection analysis."""

    is_loop: bool
    loop_type: LoopType | None
    confidence: float  # 0.0 - 1.0
    message: str
    recommendation: str | None = None


class LoopDetectionService:
    """
    Detects and prevents tool-call loops in agent execution.

    Uses a sliding window of recent tool calls to identify:
    1. Generic repeat: same tool + same params
    2. Known poll no-progress: poll-like tools returning same result
    3. Ping-pong: alternating between two tools
    """

    def __init__(
        self,
        enabled: bool = True,
        warning_threshold: int = 8,
        critical_threshold: int = 12,
        history_size: int = 30,
        detectors: dict[str, bool] | None = None,
    ):
        self.enabled = enabled
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.history_size = history_size
        self.detectors = detectors or {
            "genericRepeat": True,
            "knownPollNoProgress": True,
            "pingPong": True,
        }

        self._history: dict[UUID, deque[LoopEvent]] = {}

        self._poll_like_tools = {
            "process",
            "browser_automation",
            "web_browser",
            "agent_memory",
            "scheduler",
            "delegate_task",
        }

    def _get_hash(self, tool_name: str, params: dict, output: str | None = None) -> str:
        """Generate a hash for tool call identification."""
        import hashlib

        content = f"{tool_name}:{sorted(params.items())}:{output or ''}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def record_tool_call(
        self,
        session_id: UUID,
        tool_name: str,
        parameters: dict[str, Any],
        output: str | None = None,
    ) -> None:
        """Record a tool call for loop detection."""
        if not self.enabled:
            return

        if session_id not in self._history:
            self._history[session_id] = deque(maxlen=self.history_size)

        event = LoopEvent(
            tool_name=tool_name,
            parameters=parameters,
            output_hash=self._get_hash(tool_name, parameters, output),
        )
        self._history[session_id].append(event)

    def analyze(self, session_id: UUID) -> LoopDetectionResult | None:
        """Analyze recent tool calls for loop patterns."""
        if not self.enabled or session_id not in self._history:
            return None

        history = list(self._history[session_id])
        if len(history) < 3:
            return None

        if self.detectors.get("genericRepeat", True):
            result = self._check_generic_repeat(history)
            if result.is_loop:
                return result

        if self.detectors.get("knownPollNoProgress", True):
            result = self._check_poll_no_progress(history)
            if result.is_loop:
                return result

        if self.detectors.get("pingPong", True):
            result = self._check_ping_pong(history)
            if result.is_loop:
                return result

        return None

    def _check_generic_repeat(self, history: list[LoopEvent]) -> LoopDetectionResult:
        """Check for repeated same tool + params pattern."""
        if len(history) < 3:
            return LoopDetectionResult(False, None, 0.0, "")

        last = history[-1]
        count = 1

        for i in range(len(history) - 2, -1, -1):
            event = history[i]
            if (
                event.tool_name == last.tool_name
                and event.output_hash == last.output_hash
            ):
                count += 1
            else:
                break

        if count >= self.critical_threshold:
            return LoopDetectionResult(
                is_loop=True,
                loop_type=LoopType.GENERIC_REPEAT,
                confidence=1.0,
                message=f"CRITICAL: Same tool '{last.tool_name}' called {count} times with identical output",
                recommendation="Stop and ask user for clarification. The agent is stuck in a repetitive pattern.",
            )
        elif count >= self.warning_threshold:
            return LoopDetectionResult(
                is_loop=True,
                loop_type=LoopType.GENERIC_REPEAT,
                confidence=0.8,
                message=f"WARNING: Tool '{last.tool_name}' repeated {count} times - possible loop",
                recommendation="Consider a different approach or ask the user for guidance.",
            )

        return LoopDetectionResult(False, None, 0.0, "")

    def _check_poll_no_progress(self, history: list[LoopEvent]) -> LoopDetectionResult:
        """Check for poll-like tools returning same result repeatedly."""
        if len(history) < 4:
            return LoopDetectionResult(False, None, 0.0, "")

        recent = history[-4:]
        if not all(e.tool_name in self._poll_like_tools for e in recent):
            return LoopDetectionResult(False, None, 0.0, "")

        output_hashes = [e.output_hash for e in recent]
        if len(set(output_hashes)) == 1:
            tool = recent[-1].tool_name
            return LoopDetectionResult(
                is_loop=True,
                loop_type=LoopType.KNOWN_POLL_NO_PROGRESS,
                confidence=0.9,
                message=f"CRITICAL: '{tool}' polling with no progress ({len(recent)} identical results)",
                recommendation=f"The '{tool}' operation is not making progress. Consider different parameters or alternative approach.",
            )

        return LoopDetectionResult(False, None, 0.0, "")

    def _check_ping_pong(self, history: list[LoopEvent]) -> LoopDetectionResult:
        """Check for alternating A/B pattern (ping-pong)."""
        if len(history) < 6:
            return LoopDetectionResult(False, None, 0.0, "")

        recent = history[-6:]

        if len(recent) >= 6:
            tools = [e.tool_name for e in recent[-6:]]
            if tools[0] == tools[2] == tools[4] and tools[1] == tools[3]:
                tool_a, tool_b = tools[0], tools[1]
                return LoopDetectionResult(
                    is_loop=True,
                    loop_type=LoopType.PING_PONG,
                    confidence=0.85,
                    message=f"PING-PONG detected: alternating between '{tool_a}' and '{tool_b}'",
                    recommendation="The agent is alternating between two tools without progress. Stop and analyze the situation manually.",
                )

        return LoopDetectionResult(False, None, 0.0, "")

    def get_stats(self, session_id: UUID) -> dict[str, Any]:
        """Get loop detection statistics for a session."""
        if session_id not in self._history:
            return {"enabled": self.enabled, "events": 0, "status": "no_data"}

        history = list(self._history[session_id])
        tool_counts: dict[str, int] = {}

        for event in history:
            tool_counts[event.tool_name] = tool_counts.get(event.tool_name, 0) + 1

        return {
            "enabled": self.enabled,
            "events": len(history),
            "tool_counts": tool_counts,
            "most_used": max(tool_counts.items(), key=lambda x: x[1])
            if tool_counts
            else None,
            "thresholds": {
                "warning": self.warning_threshold,
                "critical": self.critical_threshold,
            },
        }

    def reset(self, session_id: UUID) -> None:
        """Reset loop detection history for a session."""
        if session_id in self._history:
            self._history[session_id].clear()

    def cleanup(self) -> None:
        """Clean up old session histories."""
        now = time.time()
        timeout = 3600

        for session_id in list(self._history.keys()):
            history = self._history[session_id]
            if history and (now - history[-1].timestamp) > timeout:
                del self._history[session_id]


_loop_detection_service: LoopDetectionService | None = None


def get_loop_detection_service() -> LoopDetectionService:
    """Get or create the global loop detection service instance."""
    global _loop_detection_service
    if _loop_detection_service is None:
        _loop_detection_service = LoopDetectionService()
    return _loop_detection_service
