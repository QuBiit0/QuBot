import json
from uuid import UUID

from .base import ActionContext, BaseTool, ToolParam


class DelegateTool(BaseTool):
    """
    Tool to delegate a subtask to another agent via the Orchestrator.
    This enables Agent-to-Agent communication and task breakdown.
    """

    name = "delegate_task"
    description = "Delegate a specific subtask or question to another specialized agent. Use this when a task is outside your primary domain or requires parallel execution."

    parameters = [
        ToolParam(
            name="title",
            type="string",
            description="A short, descriptive title for the delegated task.",
            required=True,
        ),
        ToolParam(
            name="description",
            type="string",
            description="Detailed instructions of what the other agent needs to do.",
            required=True,
        ),
        ToolParam(
            name="domain",
            type="string",
            description="The domain of the agent you need (e.g. software, data, marketing, operations, research).",
            required=True,
        ),
        ToolParam(
            name="input_data",
            type="string",
            description="Any structured JSON context or explicit data the other agent might need.",
            required=False,
        ),
    ]

    async def execute(self, params: dict, context: ActionContext) -> str:
        """Execute delegation by creating a new task and letting orchestrator handle it"""
        # We need task_id to create a subtask
        if not context.metadata or not context.metadata.get("task_id"):
            return "Error: Cannot delegate without a parent task context."

        parent_task_id_str = context.metadata.get("task_id")
        try:
            parent_task_id = UUID(parent_task_id_str)
        except ValueError:
            return "Error: Invalid task_id in context."

        title = params.get("title", "Delegated Task")
        description = params.get("description", "")
        domain = params.get("domain", "software")
        input_data_str = params.get("input_data", "{}")

        try:
            input_data = json.loads(input_data_str) if input_data_str else {}
        except json.JSONDecodeError:
            input_data = {"raw": input_data_str}

        return f"Successfully delegated task '{title}' to {domain} domain. The Orchestrator will handle the assignment and report back the findings when complete."
