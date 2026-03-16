"""
Assignment Service - Intelligent task-to-agent assignment

Uses scoring algorithm based on:
1. Domain expertise match
2. Current workload
3. Past performance on similar tasks
4. Agent availability
5. Tool requirements
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.agent import Agent
from ..models.enums import (
    AgentStatusEnum,
    DomainEnum,
    TaskEventTypeEnum,
    TaskStatusEnum,
)
from ..models.task import Task, TaskEvent
from .agent_service import AgentService
from .task_service import TaskService


@dataclass
class AssignmentScore:
    """Score breakdown for agent-task assignment"""

    agent_id: UUID
    agent_name: str
    total_score: float
    domain_match: float  # 0-40 points
    workload_score: float  # 0-25 points
    performance_score: float  # 0-25 points
    availability_score: float  # 0-10 points

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": str(self.agent_id),
            "agent_name": self.agent_name,
            "total_score": round(self.total_score, 2),
            "breakdown": {
                "domain_match": round(self.domain_match, 2),
                "workload": round(self.workload_score, 2),
                "performance": round(self.performance_score, 2),
                "availability": round(self.availability_score, 2),
            },
        }


class AssignmentService:
    """
    Service for intelligent task assignment.

    Uses a multi-factor scoring algorithm to find the best agent for a task.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_service = TaskService(session)
        self.agent_service = AgentService(session)

    async def find_best_agent(
        self,
        task_id: UUID,
        consider_all: bool = False,
    ) -> AssignmentScore | None:
        """
        Find the best agent for a task.

        Args:
            task_id: Task to assign
            consider_all: If True, consider all agents including busy ones

        Returns:
            Best assignment score or None if no suitable agent
        """
        task = await self.task_service.get_task(task_id)
        if not task:
            return None

        # Get candidate agents
        if consider_all:
            agents = await self.agent_service.get_agents(limit=100)
        else:
            # Only available agents
            agents = await self.agent_service.get_agents(
                status=AgentStatusEnum.IDLE,
                limit=100,
            )

        if not agents:
            return None

        # Score each agent
        scores = []
        for agent in agents:
            score = await self._score_agent_for_task(agent, task)
            scores.append(score)

        # Sort by total score
        scores.sort(key=lambda x: x.total_score, reverse=True)

        return scores[0] if scores else None

    async def get_assignment_recommendations(
        self,
        task_id: UUID,
        top_k: int = 3,
    ) -> list[AssignmentScore]:
        """
        Get top-k agent recommendations for a task.

        Args:
            task_id: Task to assign
            top_k: Number of recommendations

        Returns:
            List of assignment scores sorted by suitability
        """
        task = await self.task_service.get_task(task_id)
        if not task:
            return []

        # Get all agents
        agents = await self.agent_service.get_agents(limit=100)

        # Score each agent
        scores = []
        for agent in agents:
            score = await self._score_agent_for_task(agent, task)
            scores.append(score)

        # Sort and return top-k
        scores.sort(key=lambda x: x.total_score, reverse=True)
        return scores[:top_k]

    async def _score_agent_for_task(
        self,
        agent: Agent,
        task: Task,
    ) -> AssignmentScore:
        """Calculate assignment score for an agent-task pair"""

        # Domain match (0-40 points)
        domain_match = self._calculate_domain_match(agent, task)

        # Workload score (0-25 points)
        workload_score = await self._calculate_workload_score(agent)

        # Performance score (0-25 points)
        performance_score = await self._calculate_performance_score(agent, task)

        # Availability score (0-10 points)
        availability_score = self._calculate_availability_score(agent)

        # Total score
        total = domain_match + workload_score + performance_score + availability_score

        return AssignmentScore(
            agent_id=agent.id,
            agent_name=agent.name,
            total_score=total,
            domain_match=domain_match,
            workload_score=workload_score,
            performance_score=performance_score,
            availability_score=availability_score,
        )

    def _calculate_domain_match(
        self,
        agent: Agent,
        task: Task,
    ) -> float:
        """
        Calculate domain match score (0-40 points).

        Exact domain match = 40 points
        Related domain = 20-30 points
        Different domain = 0-10 points
        """
        if not task.domain_hint:
            return 20.0  # Neutral if no domain specified

        if agent.domain == task.domain_hint.value:
            return 40.0  # Perfect match

        # Domain relationships
        related_domains = {
            DomainEnum.SOFTWARE: [DomainEnum.DATA, DomainEnum.RESEARCH],
            DomainEnum.DATA: [
                DomainEnum.SOFTWARE,
                DomainEnum.RESEARCH,
                DomainEnum.FINANCE,
            ],
            DomainEnum.FINANCE: [
                DomainEnum.DATA,
                DomainEnum.LEGAL,
                DomainEnum.OPERATIONS,
            ],
            DomainEnum.LEGAL: [DomainEnum.FINANCE, DomainEnum.HR],
            DomainEnum.HR: [DomainEnum.LEGAL, DomainEnum.OPERATIONS],
            DomainEnum.MARKETING: [DomainEnum.OPERATIONS],
            DomainEnum.OPERATIONS: [DomainEnum.MARKETING, DomainEnum.HR],
            DomainEnum.RESEARCH: [DomainEnum.SOFTWARE, DomainEnum.DATA],
        }

        try:
            agent_domain = DomainEnum(agent.domain)
            if task.domain_hint in related_domains.get(agent_domain, []):
                return 25.0  # Related domain
        except ValueError:
            pass

        return 5.0  # Different domain

    async def _calculate_workload_score(
        self,
        agent: Agent,
    ) -> float:
        """
        Calculate workload score (0-25 points).

        Fewer active tasks = higher score
        """
        # Count active tasks
        result = await self.session.execute(
            select(Task).where(
                Task.assigned_agent_id == agent.id,
                Task.status.in_([TaskStatusEnum.BACKLOG, TaskStatusEnum.IN_PROGRESS]),
            )
        )
        active_tasks = len(result.scalars().all())

        if active_tasks == 0:
            return 25.0  # Completely free
        elif active_tasks == 1:
            return 20.0
        elif active_tasks == 2:
            return 15.0
        elif active_tasks <= 4:
            return 8.0
        else:
            return 2.0  # Very busy

    async def _calculate_performance_score(
        self,
        agent: Agent,
        task: Task,
    ) -> float:
        """
        Calculate performance score based on past tasks (0-25 points).

        Based on success rate and average completion time.
        """
        # Get recent completed tasks
        since = datetime.utcnow() - timedelta(days=30)

        result = await self.session.execute(
            select(TaskEvent)
            .join(Task)
            .where(
                Task.assigned_agent_id == agent.id,
                TaskEvent.created_at >= since,
                TaskEvent.type.in_(
                    [
                        TaskEventTypeEnum.COMPLETED,
                        TaskEventTypeEnum.FAILED,
                    ]
                ),
            )
        )
        events = result.scalars().all()

        if not events:
            return 15.0  # Neutral for new agents

        # Calculate success rate
        completed = sum(1 for e in events if e.type == TaskEventTypeEnum.COMPLETED)
        failed = sum(1 for e in events if e.type == TaskEventTypeEnum.FAILED)
        total = completed + failed

        if total == 0:
            return 15.0

        success_rate = completed / total

        # Base score on success rate (0-20 points)
        base_score = success_rate * 20

        # Bonus for similar domain tasks (0-5 points)
        domain_bonus = 0.0
        if task.domain_hint and agent.domain == task.domain_hint.value:
            domain_bonus = 5.0

        return min(25.0, base_score + domain_bonus)

    def _calculate_availability_score(
        self,
        agent: Agent,
    ) -> float:
        """
        Calculate availability score (0-10 points).

        Based on current status.
        """
        status_scores = {
            AgentStatusEnum.IDLE: 10.0,
            AgentStatusEnum.WORKING: 2.0,
            AgentStatusEnum.ERROR: 0.0,
            AgentStatusEnum.OFFLINE: 0.0,
        }

        return status_scores.get(agent.status, 0.0)

    async def auto_assign_task(
        self,
        task_id: UUID,
        force: bool = False,
    ) -> AssignmentScore | None:
        """
        Automatically assign task to best available agent.

        Args:
            task_id: Task to assign
            force: If True, assign even if agent is busy

        Returns:
            Assignment result or None if no suitable agent
        """
        best = await self.find_best_agent(
            task_id=task_id,
            consider_all=force,
        )

        if not best:
            return None

        # Only auto-assign if score is decent
        if best.total_score < 30 and not force:
            return None

        # Perform assignment
        await self.task_service.assign_task(
            task_id=task_id,
            agent_id=best.agent_id,
        )

        return best

    async def get_agent_stats(
        self,
        agent_id: UUID,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get performance statistics for an agent"""
        since = datetime.utcnow() - timedelta(days=days)

        # Task counts
        result = await self.session.execute(
            select(Task).where(
                Task.assigned_agent_id == agent_id,
                Task.created_at >= since,
            )
        )
        tasks = result.scalars().all()

        completed = sum(1 for t in tasks if t.status == TaskStatusEnum.DONE)
        failed = sum(1 for t in tasks if t.status == TaskStatusEnum.FAILED)
        in_progress = sum(1 for t in tasks if t.status == TaskStatusEnum.IN_PROGRESS)

        # Average completion time
        completion_times = []
        for task in tasks:
            if task.status == TaskStatusEnum.DONE and task.completed_at:
                duration = (task.completed_at - task.created_at).total_seconds()
                completion_times.append(duration)

        avg_time = (
            sum(completion_times) / len(completion_times) if completion_times else 0
        )

        return {
            "total_tasks": len(tasks),
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "success_rate": round(completed / len(tasks), 2) if tasks else 0,
            "average_completion_time_seconds": round(avg_time, 2),
            "period_days": days,
        }

    async def rebalance_workload(
        self,
        dry_run: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Analyze workload distribution and suggest/perform rebalancing.

        Args:
            dry_run: If True, only return suggestions without making changes

        Returns:
            List of suggested reassignments
        """
        # Get all active tasks
        result = await self.session.execute(
            select(Task).where(
                Task.status.in_([TaskStatusEnum.BACKLOG, TaskStatusEnum.IN_PROGRESS]),
            )
        )
        active_tasks = result.scalars().all()

        suggestions = []

        for task in active_tasks:
            # Check if current assignment is optimal
            current_assignment = await self.find_best_agent(
                task_id=task.id,
                consider_all=True,
            )

            if not current_assignment:
                continue

            # If best agent is different from current
            if (
                task.assigned_agent_id
                and current_assignment.agent_id != task.assigned_agent_id
            ):
                current_agent = await self.agent_service.get_agent(
                    task.assigned_agent_id
                )

                suggestions.append(
                    {
                        "task_id": str(task.id),
                        "task_title": task.title,
                        "current_agent": current_agent.name
                        if current_agent
                        else "None",
                        "suggested_agent": current_assignment.agent_name,
                        "reason": "Better domain match and lower workload",
                        "score_improvement": round(current_assignment.total_score, 2),
                    }
                )

                if not dry_run:
                    await self.task_service.assign_task(
                        task_id=task.id,
                        agent_id=current_assignment.agent_id,
                    )

        return suggestions
