"""
Workflows API Endpoints - Visual Workflow Builder
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...database import get_session
from ...models.workflow import Workflow

router = APIRouter()


# ─── Schemas ────────────────────────────────────────────────────────────────

class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    is_active: bool = True


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    nodes: list[dict[str, Any]] | None = None
    edges: list[dict[str, Any]] | None = None
    is_active: bool | None = None


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/workflows", response_model=None)
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """List all workflows."""
    result = await session.execute(
        select(Workflow).order_by(Workflow.updated_at.desc()).offset(skip).limit(limit)
    )
    workflows = result.scalars().all()

    count_result = await session.execute(select(Workflow))
    total = len(count_result.scalars().all())

    return {
        "data": [_serialize(w) for w in workflows],
        "meta": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total else 1,
        },
    }


@router.post("/workflows", response_model=None, status_code=201)
async def create_workflow(
    body: WorkflowCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new workflow."""
    workflow = Workflow(
        name=body.name,
        description=body.description,
        nodes=body.nodes,
        edges=body.edges,
        is_active=body.is_active,
    )
    session.add(workflow)
    await session.commit()
    await session.refresh(workflow)
    return {"data": _serialize(workflow)}


@router.get("/workflows/{workflow_id}", response_model=None)
async def get_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a workflow by ID."""
    workflow = await session.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"data": _serialize(workflow)}


@router.patch("/workflows/{workflow_id}", response_model=None)
async def update_workflow(
    workflow_id: UUID,
    body: WorkflowUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a workflow (nodes/edges/name/description)."""
    workflow = await session.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(workflow, field, value)
    workflow.updated_at = datetime.utcnow()

    session.add(workflow)
    await session.commit()
    await session.refresh(workflow)
    return {"data": _serialize(workflow)}


@router.delete("/workflows/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete a workflow."""
    workflow = await session.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await session.delete(workflow)
    await session.commit()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _serialize(w: Workflow) -> dict:
    return {
        "id": str(w.id),
        "name": w.name,
        "description": w.description,
        "nodes": w.nodes or [],
        "edges": w.edges or [],
        "is_active": w.is_active,
        "created_by": w.created_by,
        "created_at": w.created_at.isoformat(),
        "updated_at": w.updated_at.isoformat(),
    }
