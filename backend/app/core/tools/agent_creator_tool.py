"""
Agent Creator Tool - Allows agents to spawn specialized agents dynamically.

This enables autonomous agent creation similar to OpenClaw/Nanobot.
Agents can create helper agents for specific tasks.
"""

import json
from uuid import UUID

from .base import BaseTool, ToolParameter, ToolResult, ToolCategory, ToolRiskLevel
from app.models.enums import DomainEnum


class AgentCreatorTool(BaseTool):
    """
    Create new specialized agents on-demand. Use this when you need parallel
    execution, specialized skills, or want to break complex tasks into
    multiple specialized agents working simultaneously.
    """

    name = "create_agent"
    description = (
        "Create a new specialized agent for specific tasks. "
        "The agent will be spawned with the specified domain expertise and configuration. "
        "Use for parallel task execution, specialized subtasks, or when you need multiple agents."
    )

    category = ToolCategory.SYSTEM
    risk_level = ToolRiskLevel.DANGEROUS

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "name": ToolParameter(
                name="name",
                type="string",
                description="Unique name for the new agent",
                required=True,
            ),
            "domain": ToolParameter(
                name="domain",
                type="string",
                description="Domain expertise: 'software', 'data', 'business', 'research'",
                required=True,
            ),
            "role_description": ToolParameter(
                name="role_description",
                type="string",
                description="Description of the agent's role and responsibilities",
                required=False,
                default="",
            ),
            "instructions": ToolParameter(
                name="instructions",
                type="string",
                description="Specific instructions or context for this agent",
                required=False,
                default="",
            ),
            "llm_config_id": ToolParameter(
                name="llm_config_id",
                type="string",
                description="LLM config UUID to use (optional, uses default)",
                required=False,
                default="",
            ),
            "tools": ToolParameter(
                name="tools",
                type="string",
                description="JSON array of tool names to enable for this agent",
                required=False,
                default="[]",
            ),
        }

    async def execute(self, **params) -> ToolResult:
        """Create a new agent"""
        from app.database import get_session
        from app.services import AgentService, TaskService
        from app.models.enums import DomainEnum

        name = params.get("name", "")
        domain = params.get("domain", "software")
        role_description = params.get("role_description", "")
        instructions = params.get("instructions", "")
        llm_config_id = params.get("llm_config_id", "")
        tools_str = params.get("tools", "[]")

        if not name:
            return ToolResult(success=False, error="Agent name is required")

        try:
            tools = json.loads(tools_str) if tools_str else []
        except json.JSONDecodeError:
            tools = []

        try:
            async for session in get_session():
                agent_service = AgentService(session)

                normalized_domain = self._normalize_domain(domain)

                agent_class_id = await self._get_agent_class_id(
                    session, normalized_domain
                )
                llm_uuid = UUID(llm_config_id) if llm_config_id else None

                agent = await agent_service.create_agent(
                    name=name,
                    gender="neutral",
                    class_id=agent_class_id,
                    domain=normalized_domain.value,
                    role_description=role_description or f"Specialized {domain} agent",
                    personality={"analytical": 0.8, "creative": 0.6},
                    llm_config_id=llm_uuid,
                    avatar_config={"color": self._get_domain_color(normalized_domain)},
                )

                if instructions:
                    task_service = TaskService(session)
                    task = await task_service.create_task(
                        title=f"Initial task for {name}",
                        description=instructions,
                        domain=normalized_domain,
                        created_by="agent",
                        metadata={"created_by_agent": True, "parent_agent": name},
                    )

                return ToolResult(
                    success=True,
                    data={
                        "message": f"Successfully created agent '{name}'",
                        "agent_id": str(agent.id),
                        "domain": domain,
                        "status": "active",
                        "task_created": bool(instructions),
                    },
                )
                break
        except ValueError as e:
            return ToolResult(success=False, error=f"Invalid parameters: {str(e)}")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to create agent: {str(e)}")

    def _normalize_domain(self, domain: str) -> DomainEnum:
        """Map domain strings to DomainEnum"""
        mapping = {
            "software": "TECH",
            "tech": "TECH",
            "coding": "TECH",
            "programming": "TECH",
            "data": "DATA",
            "analytics": "DATA",
            "data science": "DATA",
            "marketing": "BUSINESS",
            "sales": "BUSINESS",
            "operations": "BUSINESS",
            "hr": "BUSINESS",
            "research": "OTHER",
            "general": "OTHER",
        }
        normalized = mapping.get(domain.lower(), "TECH")
        try:
            return DomainEnum(normalized)
        except ValueError:
            return DomainEnum.TECH

    async def _get_agent_class_id(self, session, domain: DomainEnum) -> UUID | None:
        """Get agent class ID for domain"""
        from app.services import AgentService
        from sqlalchemy import select
        from app.models.agent import AgentClass

        agent_service = AgentService(session)
        classes = await agent_service.get_agent_classes(domain=domain.value)

        if classes:
            return classes[0].id

        classes_result = await session.execute(select(AgentClass).limit(1))
        first_class = classes_result.scalar_one_or_none()
        return first_class.id if first_class else None

    def _get_domain_color(self, domain: DomainEnum) -> str:
        """Get avatar color for domain"""
        colors = {
            DomainEnum.TECH: "#3B82F6",
            DomainEnum.DATA: "#10B981",
            DomainEnum.BUSINESS: "#F59E0B",
            DomainEnum.OTHER: "#8B5CF6",
        }
        return colors.get(domain, "#6B7280")
