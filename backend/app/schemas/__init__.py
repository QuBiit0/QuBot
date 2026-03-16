"""Pydantic request/response schemas for all API endpoints."""

from .agents import (
    AgentClassCreateRequest,
    AgentCreateRequest,
    AgentStatusUpdateRequest,
    AgentUpdateRequest,
    ToolAssignmentRequest,
)
from .execution import AutoAssignRequest, ExecuteTaskRequest, OrchestratorProcessRequest
from .llm_configs import (
    ChatCompletionRequest,
    ChatMessage,
    ChatToolDefinition,
    LlmConfigCreateRequest,
    LlmConfigUpdateRequest,
)
from .memories import (
    AgentMemoryCreateRequest,
    AgentMemoryUpdateRequest,
    GlobalMemoryCreateRequest,
    GlobalMemoryUpdateRequest,
    TaskMemoryCreateRequest,
)
from .tasks import (
    SubtaskCreateRequest,
    TaskAssignRequest,
    TaskCreateRequest,
    TaskEventRequest,
    TaskStatusUpdateRequest,
    TaskUpdateRequest,
)
from .tool_execution import LlmToolsExecuteRequest, TaskToolsExecuteRequest, ToolExecuteRequest
from .tools import ToolAssignRequest, ToolCreateRequest, ToolUpdateRequest

__all__ = [
    # agents
    "AgentCreateRequest",
    "AgentUpdateRequest",
    "AgentStatusUpdateRequest",
    "AgentClassCreateRequest",
    "ToolAssignmentRequest",
    # execution
    "ExecuteTaskRequest",
    "OrchestratorProcessRequest",
    "AutoAssignRequest",
    # llm_configs
    "LlmConfigCreateRequest",
    "LlmConfigUpdateRequest",
    "ChatCompletionRequest",
    "ChatMessage",
    "ChatToolDefinition",
    # memories
    "GlobalMemoryCreateRequest",
    "GlobalMemoryUpdateRequest",
    "AgentMemoryCreateRequest",
    "AgentMemoryUpdateRequest",
    "TaskMemoryCreateRequest",
    # tasks
    "TaskCreateRequest",
    "TaskUpdateRequest",
    "TaskStatusUpdateRequest",
    "TaskAssignRequest",
    "TaskEventRequest",
    "SubtaskCreateRequest",
    # tool_execution
    "ToolExecuteRequest",
    "LlmToolsExecuteRequest",
    "TaskToolsExecuteRequest",
    # tools
    "ToolCreateRequest",
    "ToolUpdateRequest",
    "ToolAssignRequest",
]
