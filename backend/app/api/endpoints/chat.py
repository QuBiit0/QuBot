"""
Chat endpoint — receives user messages and orchestrates task creation + execution.
"""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.realtime import broadcast_activity, broadcast_metrics
from app.database import get_session
from app.models.enums import DomainEnum, PriorityEnum
from app.services.llm_service import LLMService
from app.services.orchestrator_service import OrchestratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# ── Domain keyword detection ──────────────────────────────────────────────────
_DOMAIN_KEYWORDS: dict[DomainEnum, list[str]] = {
    DomainEnum.TECH: [
        "code",
        "develop",
        "build",
        "fix",
        "bug",
        "feature",
        "api",
        "backend",
        "frontend",
        "deploy",
        "database",
        "test",
        "program",
        "software",
        "script",
        "function",
        "class",
        "module",
        "refactor",
    ],
    DomainEnum.BUSINESS: [
        "business",
        "strategy",
        "revenue",
        "profit",
        "sales",
        "client",
        "customer",
        "market",
        "product",
        "service",
        "contract",
        "deal",
    ],
    DomainEnum.FINANCE: [
        "finance",
        "budget",
        "cost",
        "expense",
        "revenue",
        "investment",
        "accounting",
        "tax",
        "invoice",
        "payment",
        "financial",
        "money",
    ],
    DomainEnum.HR: [
        "hire",
        "recruit",
        "employee",
        "team",
        "salary",
        "benefits",
        "onboarding",
        "training",
        "performance",
        "review",
        "hr",
        "human resources",
    ],
    DomainEnum.MARKETING: [
        "marketing",
        "campaign",
        "seo",
        "content",
        "social",
        "email",
        "ads",
        "brand",
        "audience",
        "analytics",
        "promotion",
        "advertising",
    ],
    DomainEnum.LEGAL: [
        "legal",
        "contract",
        "agreement",
        "compliance",
        "regulation",
        "law",
        "policy",
        "terms",
        "privacy",
        "gdpr",
        "license",
    ],
    DomainEnum.PERSONAL: [
        "personal",
        "reminder",
        "todo",
        "task",
        "schedule",
        "appointment",
        "meeting",
        "call",
        "follow up",
        "organize",
    ],
}


def _detect_domain(message: str) -> DomainEnum:
    """Detect the domain based on keywords in the message."""
    lower = message.lower()
    scores: dict[DomainEnum, int] = dict.fromkeys(DomainEnum, 0)

    for domain, keywords in _DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                scores[domain] += 1

    best = max(scores, key=lambda d: scores[d])
    return best if scores[best] > 0 else DomainEnum.OTHER


async def _get_default_llm_config_id(session: AsyncSession) -> UUID | None:
    """Get the first available LLM configuration ID."""
    llm_service = LLMService(session)
    configs = await llm_service.get_default_configs()

    if configs:
        return configs[0].id
    return None


# ── Schemas ───────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    agent_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    tasks_created: list[int] = []
    actions_taken: list[str] = []


# ── Endpoint ──────────────────────────────────────────────────────────────────


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Main chat endpoint. Detects domain, uses OrchestratorService to process task,
    and broadcasts real-time WebSocket updates.
    """
    logger.info("[chat] message: %s", request.message[:80])

    try:
        # Detect domain from message
        domain = _detect_domain(request.message)
        logger.debug("[chat] detected domain: %s", domain.value)

        # Get default LLM config
        llm_config_id = await _get_default_llm_config_id(session)
        if not llm_config_id:
            logger.error("[chat] no LLM configuration available")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No LLM configuration available. Please configure an LLM first.",
            )

        # Initialize orchestrator service
        orchestrator = OrchestratorService(session)

        # Process task through orchestrator
        result = await orchestrator.process_task(
            title=request.message[:200],
            description=request.message,
            llm_config_id=llm_config_id,
            priority=PriorityEnum.MEDIUM,
            requested_domain=domain,
            input_data={"source": "chat", "original_message": request.message},
            created_by="user",
        )

        # Extract task information from result
        parent_task_id = result.get("parent_task_id")
        success = result.get("success", False)
        assigned_agent = result.get("assigned_agent", "System")

        # Build actions list
        actions = []
        tasks_created = []

        if parent_task_id:
            try:
                task_id = (
                    int(parent_task_id.split("-")[0])
                    if isinstance(parent_task_id, str)
                    else int(parent_task_id)
                )
                tasks_created.append(task_id)
                actions.append(f"Task #{task_id} created")
            except (ValueError, AttributeError):
                # Handle UUID format
                actions.append(f"Task created (ID: {parent_task_id})")
                tasks_created.append(0)  # Placeholder when we can't extract numeric ID

        if assigned_agent and assigned_agent != "System":
            actions.append(f"Assigned to {assigned_agent} ({domain.value})")

        # Handle subtasks if present (complex task)
        subtasks = result.get("subtasks", [])
        if subtasks:
            actions.append(f"Broken down into {len(subtasks)} subtasks")

        # Broadcast activity event
        status_type = "completed" if success else "failed"
        await broadcast_activity(
            status=status_type,
            agent_name=assigned_agent,
            message=f"Task processed: {request.message[:60]}{'...' if len(request.message) > 60 else ''}",
        )

        # Broadcast updated metrics
        await broadcast_metrics()

        # Build reply message
        if success:
            if subtasks:
                reply = (
                    f"Got it! I've created task #{tasks_created[0] if tasks_created else 'N/A'} "
                    f"and broken it down into **{len(subtasks)} subtasks**. "
                    f"Assigned to **{assigned_agent}** ({domain.value}). "
                    "I'll coordinate the execution and keep you posted as it progresses."
                )
            else:
                reply = (
                    f"Got it! I've created task #{tasks_created[0] if tasks_created else 'N/A'} "
                    f"and assigned it to **{assigned_agent}** ({domain.value}). "
                    "I'll keep you posted as it progresses."
                )
        else:
            error_msg = result.get("error", "Unknown error")
            reply = (
                f"I encountered an issue processing your request: {error_msg}. "
                "Please try again or contact support if the problem persists."
            )

        return ChatResponse(
            reply=reply,
            tasks_created=tasks_created if tasks_created else [],
            actions_taken=actions,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("[chat] error processing message: %s", exc)

        # Broadcast error activity
        await broadcast_activity(
            status="error",
            agent_name="System",
            message=f"Error processing request: {str(exc)[:60]}",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(exc)}",
        )


def _sse(event: str, data: object) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _stream_chat(
    message: str,
    session: AsyncSession,
) -> AsyncGenerator[str, None]:
    """Generate SSE tokens for a chat message."""
    yield _sse("status", {"text": "Analyzing request…"})
    await asyncio.sleep(0)

    domain = _detect_domain(message)
    yield _sse("status", {"text": f"Domain: {domain.value}. Finding best agent…"})
    await asyncio.sleep(0)

    llm_config_id = await _get_default_llm_config_id(session)
    if not llm_config_id:
        yield _sse("error", {"message": "No LLM configuration available."})
        return

    orchestrator = OrchestratorService(session)

    try:
        result = await orchestrator.process_task(
            title=message[:200],
            description=message,
            llm_config_id=llm_config_id,
            priority=PriorityEnum.MEDIUM,
            requested_domain=domain,
            input_data={"source": "chat", "original_message": message},
            created_by="user",
        )
    except Exception as exc:
        logger.exception("[chat/stream] orchestrator error: %s", exc)
        yield _sse("error", {"message": str(exc)})
        return

    parent_task_id = result.get("parent_task_id")
    success = result.get("success", False)
    assigned_agent = result.get("assigned_agent", "System")
    subtasks = result.get("subtasks", [])

    actions: list[str] = []
    tasks_created: list[int] = []

    if parent_task_id:
        try:
            task_id = (
                int(parent_task_id.split("-")[0])
                if isinstance(parent_task_id, str)
                else int(parent_task_id)
            )
            tasks_created.append(task_id)
            actions.append(f"Task #{task_id} created")
        except (ValueError, AttributeError):
            actions.append(f"Task created (ID: {parent_task_id})")
            tasks_created.append(0)

    if assigned_agent and assigned_agent != "System":
        actions.append(f"Assigned to {assigned_agent} ({domain.value})")
    if subtasks:
        actions.append(f"Broken down into {len(subtasks)} subtasks")

    # Stream reply word-by-word for a typing effect
    if success:
        if subtasks:
            reply = (
                f"Got it! I've created task #{tasks_created[0] if tasks_created else 'N/A'} "
                f"and broken it down into {len(subtasks)} subtasks. "
                f"Assigned to {assigned_agent} ({domain.value}). "
                "I'll coordinate the execution and keep you posted."
            )
        else:
            reply = (
                f"Got it! I've created task #{tasks_created[0] if tasks_created else 'N/A'} "
                f"and assigned it to {assigned_agent} ({domain.value}). "
                "I'll keep you posted as it progresses."
            )
    else:
        error_msg = result.get("error", "Unknown error")
        reply = f"I encountered an issue: {error_msg}. Please try again."

    # Emit tokens (words) with small delay
    words = reply.split(" ")
    for i, word in enumerate(words):
        chunk = word if i == 0 else " " + word
        yield _sse("token", {"text": chunk})
        await asyncio.sleep(0.02)

    # Final event with metadata
    yield _sse(
        "done",
        {
            "tasks_created": tasks_created,
            "actions_taken": actions,
        },
    )

    await broadcast_activity(
        status="completed" if success else "failed",
        agent_name=assigned_agent,
        message=f"Task processed: {message[:60]}{'...' if len(message) > 60 else ''}",
    )
    await broadcast_metrics()


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Streaming chat endpoint using Server-Sent Events.
    Events: status | token | done | error
    """
    return StreamingResponse(
        _stream_chat(request.message, session),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
