import json
from uuid import UUID

from .base import BaseTool, ToolParameter, ToolResult, ToolCategory, ToolRiskLevel


class DelegateTool(BaseTool):
    """
    Tool to delegate a subtask to another agent via the Orchestrator.
    This enables Agent-to-Agent communication and task breakdown.
    """

    name = "delegate_task"
    description = "Delegate a specific subtask or question to another specialized agent. Use this when a task is outside your primary domain or requires parallel execution."

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
        # Note: In a real implementation, we would use a service to create a subtask.
        # For now, we simulate the delegation success message.
        title = params.get("title", "Delegated Task")
        domain = params.get("domain", "software")
        input_data_str = params.get("input_data", "{}")

        try:
            input_data = json.loads(input_data_str) if input_data_str else {}
        except json.JSONDecodeError:
            input_data = {"raw": input_data_str}

        return ToolResult(
            success=True,
            data={
                "message": f"Successfully delegated task '{title}' to {domain} domain.",
                "domain": domain,
                "input_context": input_data
            }
        )
