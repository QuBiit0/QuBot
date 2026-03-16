"""
Agent Service - Business logic for agent management
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models.agent import Agent, AgentClass, AgentTool
from ..models.enums import AgentStatusEnum


class AgentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_agent(
        self,
        name: str,
        gender: str,
        class_id: UUID,
        domain: str,
        role_description: str,
        personality: dict,
        llm_config_id: UUID,
        avatar_config: dict,
        is_orchestrator: bool = False,
    ) -> Agent:
        """Create a new agent"""
        agent = Agent(
            name=name,
            gender=gender,
            class_id=class_id,
            domain=domain,
            role_description=role_description,
            personality=personality,
            llm_config_id=llm_config_id,
            avatar_config=avatar_config,
            is_orchestrator=is_orchestrator,
            status=AgentStatusEnum.IDLE,
        )
        self.session.add(agent)
        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def get_agent(self, agent_id: UUID) -> Agent | None:
        """Get agent by ID"""
        result = await self.session.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()

    async def get_agents(
        self,
        status: AgentStatusEnum | None = None,
        domain: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Agent]:
        """Get list of agents with optional filters"""
        query = select(Agent)

        if status:
            query = query.where(Agent.status == status)
        if domain:
            query = query.where(Agent.domain == domain)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_agent(self, agent_id: UUID, **updates) -> Agent | None:
        """Update agent fields"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return None

        for key, value in updates.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def delete_agent(self, agent_id: UUID) -> bool:
        """Soft delete agent by setting status to OFFLINE"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return False

        agent.status = AgentStatusEnum.OFFLINE
        await self.session.commit()
        return True

    async def update_agent_status(
        self,
        agent_id: UUID,
        status: AgentStatusEnum,
        current_task_id: UUID | None = None,
    ) -> Agent | None:
        """Update agent status and optionally current task"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return None

        agent.status = status
        if current_task_id is not None:
            agent.current_task_id = current_task_id

        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def assign_tool(
        self,
        agent_id: UUID,
        tool_id: UUID,
        permissions: str = "READ_ONLY",
    ) -> AgentTool:
        """Assign a tool to an agent"""
        agent_tool = AgentTool(
            agent_id=agent_id,
            tool_id=tool_id,
            permissions=permissions,
        )
        self.session.add(agent_tool)
        await self.session.commit()
        return agent_tool

    async def unassign_tool(self, agent_id: UUID, tool_id: UUID) -> bool:
        """Remove a tool assignment from an agent"""
        result = await self.session.execute(
            select(AgentTool).where(
                AgentTool.agent_id == agent_id,
                AgentTool.tool_id == tool_id,
            )
        )
        agent_tool = result.scalar_one_or_none()
        if not agent_tool:
            return False

        await self.session.delete(agent_tool)
        await self.session.commit()
        return True

    async def get_agent_tools(self, agent_id: UUID) -> list[AgentTool]:
        """Get all tools assigned to an agent"""
        result = await self.session.execute(
            select(AgentTool).where(AgentTool.agent_id == agent_id)
        )
        return result.scalars().all()

    # Agent Class methods
    async def get_agent_classes(
        self,
        domain: str | None = None,
        is_custom: bool | None = None,
    ) -> list[AgentClass]:
        """Get agent classes with optional filters"""
        query = select(AgentClass)

        if domain:
            query = query.where(AgentClass.domain == domain)
        if is_custom is not None:
            query = query.where(AgentClass.is_custom == is_custom)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_agent_class(self, class_id: UUID) -> AgentClass | None:
        """Get agent class by ID"""
        result = await self.session.execute(
            select(AgentClass).where(AgentClass.id == class_id)
        )
        return result.scalar_one_or_none()

    async def create_agent_class(
        self,
        name: str,
        description: str,
        domain: str,
        default_avatar_config: dict,
    ) -> AgentClass:
        """Create a custom agent class"""
        agent_class = AgentClass(
            name=name,
            description=description,
            domain=domain,
            is_custom=True,
            default_avatar_config=default_avatar_config,
        )
        self.session.add(agent_class)
        await self.session.commit()
        await self.session.refresh(agent_class)
        return agent_class

    async def get_orchestrator(self) -> Agent | None:
        """Get the orchestrator agent"""
        result = await self.session.execute(
            select(Agent).where(Agent.is_orchestrator == True)
        )
        return result.scalar_one_or_none()
