"""
Tool Execution API Endpoints
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.security import get_current_user
from ...core.tools import register_default_tools
from ...database import get_session
from ...models.user import User
from ...services import ToolExecutionService

router = APIRouter()


@router.on_event("startup")
async def startup_event():
    """Register default tools on startup"""
    register_default_tools()


@router.get("/tools/available", response_model=dict)
async def list_available_tools(
    session: AsyncSession = Depends(get_session),
):
    """List all available tools with their schemas"""
    service = ToolExecutionService(session)
    tools = service.get_available_tools()

    return {"data": tools}


@router.post("/tools/execute", response_model=dict)
async def execute_tool(
    execution_data: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Execute a tool by name.

    Request body:
    {
        "tool_name": "http_api",
        "params": {"url": "https://api.example.com/data", "method": "GET"},
        "agent_id": "optional-uuid",
        "task_id": "optional-uuid"
    }
    """
    service = ToolExecutionService(session)

    tool_name = execution_data.get("tool_name")
    params = execution_data.get("params", {})
    agent_id = execution_data.get("agent_id")
    task_id = execution_data.get("task_id")

    if not tool_name:
        raise HTTPException(status_code=400, detail="tool_name is required")

    # Convert string UUIDs to UUID objects
    if agent_id:
        agent_id = UUID(agent_id)
    if task_id:
        task_id = UUID(task_id)

    result = await service.execute_tool(
        tool_name=tool_name,
        params=params,
        agent_id=agent_id,
        task_id=task_id,
    )

    return {
        "data": {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time_ms": result.execution_time_ms,
            "metadata": result.metadata,
        }
    }


@router.post("/tools/execute-with-llm", response_model=dict)
async def execute_with_llm_tools(
    execution_data: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Execute LLM completion with tool calling loop.

    Request body:
    {
        "llm_config_id": "uuid",
        "messages": [{"role": "user", "content": "Search for ..."}],
        "system_prompt": "You are a helpful assistant...",
        "max_iterations": 5,
        "agent_id": "optional-uuid",
        "task_id": "optional-uuid"
    }
    """
    service = ToolExecutionService(session)

    llm_config_id = UUID(execution_data["llm_config_id"])
    messages = execution_data.get("messages", [])
    system_prompt = execution_data.get("system_prompt")
    max_iterations = execution_data.get("max_iterations", 5)
    agent_id = execution_data.get("agent_id")
    task_id = execution_data.get("task_id")

    if agent_id:
        agent_id = UUID(agent_id)
    if task_id:
        task_id = UUID(task_id)

    try:
        response = await service.run_with_tools(
            llm_config_id=llm_config_id,
            messages=messages,
            system_prompt=system_prompt,
            max_iterations=max_iterations,
            agent_id=agent_id,
            task_id=task_id,
        )

        return {
            "data": {
                "content": response.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments,
                    }
                    for tc in response.tool_calls
                ],
                "finish_reason": response.finish_reason.value,
                "usage": {
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "total_tokens": response.total_tokens,
                },
                "model": response.model,
                "latency_ms": response.latency_ms,
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")


@router.post("/tasks/{task_id}/execute-tools", response_model=dict)
async def execute_task_with_tools(
    task_id: UUID,
    execution_data: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Execute a task with tool calling capabilities.

    Request body:
    {
        "llm_config_id": "uuid",
        "system_prompt": "Optional system prompt",
        "max_iterations": 5
    }
    """
    from ...services import TaskService

    task_service = TaskService(session)
    tool_service = ToolExecutionService(session)

    # Get task
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get LLM config
    llm_config_id = UUID(execution_data["llm_config_id"])

    # Build messages from task
    messages = [
        {"role": "user", "content": task.description or task.title},
    ]

    # Add context if available
    if task.input_data and isinstance(task.input_data, dict):
        context = task.input_data.get("context")
        if context:
            messages.insert(0, {"role": "system", "content": f"Context: {context}"})

    system_prompt = execution_data.get("system_prompt")
    max_iterations = execution_data.get("max_iterations", 5)

    try:
        response = await tool_service.run_with_tools(
            llm_config_id=llm_config_id,
            messages=messages,
            system_prompt=system_prompt,
            max_iterations=max_iterations,
            agent_id=task.assigned_agent_id,
            task_id=task_id,
        )

        # Update task with result
        await task_service.add_progress_update(
            task_id=task_id,
            agent_id=task.assigned_agent_id,
            message=response.content or "Task completed with tool calls",
        )

        return {
            "data": {
                "content": response.content,
                "finish_reason": response.finish_reason.value,
                "usage": {
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                },
                "model": response.model,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")
