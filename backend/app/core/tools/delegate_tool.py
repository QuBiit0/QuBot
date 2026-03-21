import json
from uuid import UUID

from .base import BaseTool, ToolParameter, ToolResult, ToolCategory, ToolRiskLevel
from app.models.enums import DomainEnum


class DelegateTool(BaseTool):
    """
    Tool to delegate a subtask to another agent via the Orchestrator.
    This enables Agent-to-Agent communication and task breakdown.
    """

    name = "delegate_task"
    description = "Delegate a specific subtask or question to another specialized agent. Use this when a task is outside your primary domain or requires parallel execution. Creates a new task that will be picked up by a specialized agent."

    category = ToolCategory.SYSTEM
    risk_level = ToolRiskLevel.NORMAL

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "title": ToolParameter(
                name="title",
                type="string",
                description="A short, descriptive title for the delegated task.",
                required=True,
            ),
            "description": ToolParameter(
                name="description",
                type="string",
                description="Detailed instructions of what the other agent needs to do.",
                required=True,
            ),
            "domain": ToolParameter(
                name="domain",
                type="string",
                description="The domain of the agent you need (e.g. software, data, marketing, operations, research).",
                required=True,
            ),
            "input_data": ToolParameter(
                name="input_data",
                type="string",
                description="Any structured JSON context or explicit data the other agent might need.",
                required=False,
            ),
        }

    async def execute(self, **params) -> ToolResult:
        """Execute delegation by creating a new task and letting orchestrator handle it"""
        from app.database import get_session
        from app.services import TaskService, OrchestratorService
        from app.models.enums import PriorityEnum, DomainEnum

        title = params.get("title", "Delegated Task")
        description = params.get("description", "")
        domain = params.get("domain", "software")
        input_data_str = params.get("input_data", "{}")

        try:
            input_data = json.loads(input_data_str) if input_data_str else {}
        except json.JSONDecodeError:
            input_data = {"raw": input_data_str}

        try:
            async for session in get_session():
                task_service = TaskService(session)
                orchestrator = OrchestratorService(session)

                normalized_domain = self._normalize_domain(domain)

                task = await task_service.create_task(
                    title=title,
                    description=f"{description}\n\n---\nDelegated Task\nDomain: {domain}\n\nInput Data:\n{json.dumps(input_data, indent=2)}",
                    domain_hint=normalized_domain.value,
                    priority=PriorityEnum.MEDIUM,
                    created_by="agent",
                )

                result = await orchestrator.process_task(task.id)

                return ToolResult(
                    success=True,
                    data={
                        "message": f"Successfully delegated task '{title}' to {domain} domain.",
                        "task_id": str(task.id),
                        "domain": domain,
                        "input_context": input_data,
                        "status": "processed" if result else "queued",
                    },
                )
                break
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to delegate task: {str(e)}")

    def _normalize_domain(self, domain: str) -> DomainEnum:
        """Map common domain names to DomainEnum values"""
        mapping = {
            "software": "TECH",
            "tech": "TECH",
            "coding": "TECH",
            "programming": "TECH",
            "data": "DATA",
            "analytics": "DATA",
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
