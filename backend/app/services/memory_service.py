"""
Memory Service - Business logic for memory management
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, select

from ..models.enums import DomainEnum
from ..models.memory import AgentMemory, GlobalMemory, TaskMemory


class MemoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    # Global Memory methods
    async def create_global_memory(
        self,
        key: str,
        content: str,
        content_type: str = "text",
        tags: list[str] | None = None,
    ) -> GlobalMemory:
        """Create global memory entry"""
        memory = GlobalMemory(
            key=key,
            content=content,
            content_type=content_type,
            tags=tags or [],
        )
        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)
        return memory

    async def get_global_memory(self, memory_id: UUID) -> GlobalMemory | None:
        """Get global memory by ID"""
        result = await self.session.execute(
            select(GlobalMemory).where(GlobalMemory.id == memory_id)
        )
        return result.scalar_one_or_none()

    async def get_global_memories(
        self,
        tags: list[str] | None = None,
        search_query: str | None = None,
        limit: int = 10,
    ) -> list[GlobalMemory]:
        """Get global memories with optional filters"""
        query = select(GlobalMemory).order_by(desc(GlobalMemory.updated_at))

        if tags:
            # PostgreSQL JSON array contains check
            query = query.where(GlobalMemory.tags.cast(JSONB).op("?|")(tags))

        if search_query:
            query = query.where(GlobalMemory.content.ilike(f"%{search_query}%"))

        query = query.limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_global_memory(
        self, memory_id: UUID, **updates
    ) -> GlobalMemory | None:
        """Update global memory"""
        memory = await self.get_global_memory(memory_id)
        if not memory:
            return None

        for key, value in updates.items():
            if hasattr(memory, key):
                setattr(memory, key, value)

        memory.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(memory)
        return memory

    async def delete_global_memory(self, memory_id: UUID) -> bool:
        """Delete global memory"""
        memory = await self.get_global_memory(memory_id)
        if not memory:
            return False

        await self.session.delete(memory)
        await self.session.commit()
        return True

    # Agent Memory methods
    async def create_agent_memory(
        self,
        agent_id: UUID,
        key: str,
        content: str,
        importance: int = 3,
    ) -> AgentMemory:
        """Create or update agent memory"""
        # Check if exists
        result = await self.session.execute(
            select(AgentMemory).where(
                AgentMemory.agent_id == agent_id,
                AgentMemory.key == key,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.content = content
            existing.importance = importance
            existing.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        memory = AgentMemory(
            agent_id=agent_id,
            key=key,
            content=content,
            importance=importance,
        )
        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)
        return memory

    async def get_agent_memories(
        self,
        agent_id: UUID,
        limit: int = 10,
        min_importance: int = 1,
    ) -> list[AgentMemory]:
        """Get agent memories sorted by importance and recency"""
        result = await self.session.execute(
            select(AgentMemory)
            .where(AgentMemory.agent_id == agent_id)
            .where(AgentMemory.importance >= min_importance)
            .order_by(desc(AgentMemory.importance), desc(AgentMemory.last_accessed))
            .limit(limit)
        )
        memories = result.scalars().all()

        # Update last_accessed
        for memory in memories:
            memory.last_accessed = datetime.utcnow()
        await self.session.commit()

        return memories

    async def delete_agent_memory(self, memory_id: UUID) -> bool:
        """Delete agent memory"""
        result = await self.session.execute(
            select(AgentMemory).where(AgentMemory.id == memory_id)
        )
        memory = result.scalar_one_or_none()
        if not memory:
            return False

        await self.session.delete(memory)
        await self.session.commit()
        return True

    # Task Memory methods
    async def create_task_memory(
        self,
        task_id: UUID,
        summary: str,
        key_facts: list[str] | None = None,
    ) -> TaskMemory:
        """Create task memory (summary of completed task)"""
        memory = TaskMemory(
            task_id=task_id,
            summary=summary,
            key_facts=key_facts or [],
        )
        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)
        return memory

    async def get_task_memory(self, task_id: UUID) -> TaskMemory | None:
        """Get memory for a task"""
        result = await self.session.execute(
            select(TaskMemory).where(TaskMemory.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_recent_task_memories(
        self,
        domain: DomainEnum | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """Get recent task memories, optionally filtered by domain"""
        from ..models.task import Task

        query = (
            select(TaskMemory, Task.title, Task.domain_hint)
            .join(Task, TaskMemory.task_id == Task.id)
            .order_by(desc(TaskMemory.created_at))
        )

        if domain:
            query = query.where(Task.domain_hint == domain)

        query = query.limit(limit)
        result = await self.session.execute(query)

        return [
            {
                "task_title": row[1],
                "domain": row[2],
                "summary": row[0].summary,
                "key_facts": row[0].key_facts,
            }
            for row in result.all()
        ]

    # Context building for agent prompts
    async def build_agent_context(
        self,
        agent_id: UUID,
        task_domain: DomainEnum | None = None,
    ) -> str:
        """Build memory context block for agent system prompt"""
        sections = []

        # 1. Global memories filtered by domain tag
        domain_tag = task_domain.value.lower() if task_domain else None
        global_mems = await self.get_global_memories(
            tags=[domain_tag] if domain_tag else None,
            limit=3,
        )
        if global_mems:
            sections.append("### Shared Knowledge")
            for mem in global_mems:
                sections.append(f"**{mem.key}**:\n{mem.content[:500]}")

        # 2. Agent-specific memories (high importance first)
        agent_mems = await self.get_agent_memories(
            agent_id=agent_id,
            limit=8,
            min_importance=2,
        )
        if agent_mems:
            sections.append("### Your Memory")
            for mem in agent_mems:
                importance_label = "⚠️" if mem.importance >= 4 else "ℹ️"
                sections.append(
                    f"{importance_label} **{mem.key}**: {mem.content[:300]}"
                )

        # 3. Recent similar tasks
        recent_tasks = await self.get_recent_task_memories(domain=task_domain, limit=2)
        if recent_tasks:
            sections.append("### Recent Similar Work")
            for task_mem in recent_tasks:
                sections.append(
                    f"- **{task_mem['task_title']}**: {task_mem['summary'][:200]}"
                )

        if not sections:
            return ""

        return "\n\n".join(sections)
