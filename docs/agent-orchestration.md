# Qubot — Agent Orchestration

> **Module**: `backend/app/services/orchestrator_service.py` + `execution_service.py`
> **Worker**: `backend/app/worker.py`

---

## 1. Overview

Qubot's orchestration model has two tiers:

1. **Orchestrator Agent** — receives user messages, plans work, creates tasks, assigns them to agents
2. **Worker Agents** — execute tasks using tool-calling loops until completion or failure

All execution is asynchronous: the orchestrator returns immediately with a response while agents work in the background.

```
User Message
    │
    ▼
POST /chat
    │
    ▼
OrchestratorService
    ├── Build orchestrator prompt (team context + task history)
    ├── Call LLM → get {response, actions[]}
    ├── Execute each action:
    │   ├── CREATE_TASK → insert Task, emit WS event
    │   ├── ASSIGN_TASK → update Task, push to Redis Stream
    │   └── RESPOND → stream response to user
    │
    ▼
Redis Stream (task queue)
    │
    ▼
Worker Process (qubot-worker)
    ├── XREAD from Redis Stream
    ├── Load Agent + Task from DB
    ├── ExecutionService.run_agent_loop()
    │   ├── Build agent system prompt
    │   ├── Inject memory context
    │   └── Run tool-calling loop (max 20 iterations)
    │       ├── LLM call → tool_calls or stop
    │       ├── Execute each tool → ToolResult
    │       ├── Append TaskEvent (TOOL_CALL)
    │       └── Broadcast activity via Redis pub/sub
    └── On finish: update Task status, Agent status
```

---

## 2. Orchestrator Agent

### 2.1 Configuration

The orchestrator is a special `Agent` record with `is_orchestrator=True`. There is exactly one active orchestrator at a time. It has its own LLM config (typically a capable model like GPT-4o or Claude Opus).

**Recommended LLM config for orchestrator:**
- Provider: OPENAI or ANTHROPIC
- Model: `gpt-4o` or `claude-opus-4-6`
- Temperature: 0.2 (low for consistent JSON output)
- Max tokens: 4096

### 2.2 System Prompt Template

```python
# backend/app/services/orchestrator_service.py

ORCHESTRATOR_SYSTEM_PROMPT = """
You are {agent_name}, the orchestrator of a team of AI agents working in a digital coworking space called Qubot.

## Your Personality
{personality_text}

## Your Team
You have {agent_count} agents available:

{agents_list}

## Recent Activity (last 10 tasks)
{recent_tasks_list}

## Your Role
You receive instructions from the user and decide how to handle them:
1. **Answer directly** — if the request is conversational or needs your expertise
2. **Delegate** — create tasks and assign them to the best-fit agents based on their domain, class, and current workload
3. **Hybrid** — respond to the user AND create background tasks

## Task Assignment Guidelines
- Match tasks to agents by domain first (e.g., financial analysis → FINANCE domain agents)
- Consider agent class for specialist work (e.g., security audit → Ethical Hacker)
- Check workload: prefer agents with no current tasks
- Split complex requests into multiple focused tasks

## Output Format (MANDATORY)
Always respond with valid JSON matching this exact schema:
{
  "response": "<string or null — message to show the user immediately>",
  "actions": [
    {
      "type": "CREATE_TASK",
      "payload": {
        "title": "<string, max 200 chars>",
        "description": "<string, detailed instructions for the agent>",
        "domain_hint": "<DomainEnum: TECH|BUSINESS|FINANCE|HR|MARKETING|LEGAL|PERSONAL|OTHER>",
        "priority": "<PriorityEnum: LOW|MEDIUM|HIGH|CRITICAL>",
        "preferred_class": "<optional: agent class name>"
      }
    },
    {
      "type": "ASSIGN_TASK",
      "payload": {
        "task_id": "<UUID of task to assign (can reference a just-created task by title)>",
        "agent_id": "<UUID of agent to assign to>"
      }
    },
    {
      "type": "UPDATE_TASK",
      "payload": {
        "task_id": "<UUID>",
        "status": "<TaskStatusEnum>"
      }
    }
  ]
}

Rules:
- ALWAYS include the "response" field (can be null if only taking background actions)
- ALWAYS produce valid JSON — no markdown code blocks, no extra text
- CREATE_TASK before ASSIGN_TASK for the same task
- If no actions needed, return {"response": "...", "actions": []}
"""
```

### 2.3 Context Building

```python
async def build_orchestrator_context(
    orchestrator: Agent,
    session: AsyncSession
) -> dict:
    """Build the dynamic context injected into the orchestrator prompt."""

    # Get all non-orchestrator agents with their current status
    agents = await session.exec(
        select(Agent).where(Agent.is_orchestrator == False)
        .options(selectinload(Agent.agent_class))
    ).all()

    agents_list = "\n".join([
        f"- {a.name} ({a.agent_class.name}, {a.domain.value}): "
        f"status={a.status.value}"
        + (f", working on: '{a.current_task.title}'" if a.current_task_id else ", available")
        for a in agents
    ])

    # Get recent tasks (last 10)
    recent_tasks = await session.exec(
        select(Task)
        .order_by(Task.updated_at.desc())
        .limit(10)
    ).all()

    recent_tasks_list = "\n".join([
        f"- [{t.status.value}] {t.title}"
        + (f" → assigned to {t.assigned_agent.name}" if t.assigned_agent_id else "")
        for t in recent_tasks
    ])

    return {
        "agent_name": orchestrator.name,
        "personality_text": format_personality(orchestrator.personality),
        "agent_count": len(agents),
        "agents_list": agents_list or "No agents configured yet.",
        "recent_tasks_list": recent_tasks_list or "No recent tasks.",
    }
```

### 2.4 Action Execution

```python
async def execute_orchestrator_actions(
    actions: list[dict],
    session: AsyncSession,
    ws_manager: ConnectionManager,
) -> list[dict]:
    """Execute each action returned by the orchestrator LLM."""
    results = []
    created_tasks: dict[str, UUID] = {}  # title → id for cross-referencing

    for action in actions:
        action_type = action["type"]
        payload = action["payload"]

        if action_type == "CREATE_TASK":
            task = Task(
                title=payload["title"],
                description=payload["description"],
                domain_hint=payload.get("domain_hint"),
                priority=payload.get("priority", "MEDIUM"),
                created_by="orchestrator",
            )
            session.add(task)
            await session.flush()  # get id before commit

            # Create CREATED event
            event = TaskEvent(
                task_id=task.id,
                type=TaskEventTypeEnum.CREATED,
                payload={"title": task.title, "description": task.description}
            )
            session.add(event)
            created_tasks[task.title] = task.id

            # Broadcast to Kanban
            await ws_manager.broadcast_to_channel("kanban", {
                "type": "task_status_changed",
                "payload": {"task_id": str(task.id), "new_status": "BACKLOG", "task_title": task.title}
            })

            results.append({"type": "CREATE_TASK", "result": {"task_id": str(task.id), "title": task.title}})

        elif action_type == "ASSIGN_TASK":
            task_id = payload["task_id"]
            agent_id = payload["agent_id"]

            # Resolve task_id: could be a UUID or a title reference
            if task_id in created_tasks.values() or is_uuid(task_id):
                pass  # it's a real UUID
            else:
                # Try to match by title (orchestrator may reference by title)
                task_id = created_tasks.get(task_id)

            if not task_id:
                results.append({"type": "ASSIGN_TASK", "result": {"error": "Task not found"}})
                continue

            # Update task
            task = await session.get(Task, task_id)
            agent = await session.get(Agent, agent_id)

            if task and agent:
                task.assigned_agent_id = agent.id
                task.status = TaskStatusEnum.IN_PROGRESS

                # Create ASSIGNED event
                event = TaskEvent(
                    task_id=task.id,
                    type=TaskEventTypeEnum.ASSIGNED,
                    agent_id=agent.id,
                    payload={"agent_id": str(agent.id), "agent_name": agent.name}
                )
                session.add(event)

                # Update agent status
                agent.status = AgentStatusEnum.WORKING
                agent.current_task_id = task.id

                # Push to worker queue (Redis Stream)
                await redis.xadd("task_queue", {
                    "task_id": str(task.id),
                    "agent_id": str(agent.id),
                })

                # Broadcast status changes
                await ws_manager.broadcast_to_channel("kanban", {
                    "type": "task_status_changed",
                    "payload": {
                        "task_id": str(task.id),
                        "new_status": "IN_PROGRESS",
                        "assigned_agent_id": str(agent.id),
                        "assigned_agent_name": agent.name
                    }
                })
                await ws_manager.broadcast_to_channel("global", {
                    "type": "activity_feed",
                    "payload": {
                        "message": f"{agent.name} was assigned task: '{task.title}'",
                        "agent_id": str(agent.id),
                        "agent_name": agent.name,
                        "task_id": str(task.id),
                        "severity": "info"
                    }
                })

                results.append({"type": "ASSIGN_TASK", "result": {
                    "task_id": str(task.id), "agent_id": str(agent.id), "agent_name": agent.name
                }})

    await session.commit()
    return results
```

---

## 3. Task Assignment Algorithm

When the orchestrator requests `ASSIGN_TASK` without specifying an agent_id (or for auto-assignment), the `AssignmentService` selects the best agent.

```python
# backend/app/services/assignment_service.py

async def find_best_agent(
    domain_hint: Optional[DomainEnum],
    preferred_class: Optional[str],
    session: AsyncSession,
) -> Optional[Agent]:
    """
    Score all available agents and return the best match.

    Scoring:
    - Base: 100
    - OFFLINE status: disqualified (score = 0)
    - Each IN_PROGRESS task: -20 points
    - ERROR status: -30 points
    - Domain match (if domain_hint provided): +15 points
    - Class match (if preferred_class provided): +25 points
    - Least recently active (tiebreaker): +5 points
    """
    agents = await session.exec(
        select(Agent)
        .where(Agent.is_orchestrator == False)
        .where(Agent.status != AgentStatusEnum.OFFLINE)
        .options(selectinload(Agent.agent_class))
    ).all()

    if not agents:
        return None

    scores = []
    for agent in agents:
        score = 100

        # Penalize for current workload
        if agent.status == AgentStatusEnum.WORKING:
            score -= 20
        elif agent.status == AgentStatusEnum.ERROR:
            score -= 30

        # Reward for domain match
        if domain_hint and agent.domain == domain_hint:
            score += 15

        # Reward for class match
        if preferred_class and agent.agent_class.name.lower() == preferred_class.lower():
            score += 25

        scores.append((score, agent))

    if not scores:
        return None

    # Sort by score descending, then by last_active_at ascending (least recently used first)
    scores.sort(key=lambda x: (-x[0], x[1].last_active_at or datetime.min))
    return scores[0][1]
```

---

## 4. Agent Execution Loop (Worker)

The worker process runs independently and processes tasks from the Redis Stream queue.

### 4.1 Worker Entry Point

```python
# backend/app/worker.py
import asyncio
import structlog
from .database import AsyncSessionLocal
from .redis_client import get_redis
from .services.execution_service import ExecutionService

logger = structlog.get_logger()

async def main():
    redis = await get_redis()
    logger.info("qubot_worker_started")

    # Create consumer group if doesn't exist
    try:
        await redis.xgroup_create("task_queue", "workers", id="0", mkstream=True)
    except Exception:
        pass  # Group already exists

    while True:
        try:
            # Block-wait for new tasks (5 second timeout)
            messages = await redis.xreadgroup(
                groupname="workers",
                consumername="worker-1",
                streams={"task_queue": ">"},
                count=1,
                block=5000
            )

            if not messages:
                continue

            for stream_name, stream_messages in messages:
                for msg_id, msg_data in stream_messages:
                    task_id = msg_data["task_id"]
                    agent_id = msg_data["agent_id"]

                    try:
                        async with AsyncSessionLocal() as session:
                            service = ExecutionService(session, redis)
                            await service.execute_task(task_id, agent_id)

                        # Acknowledge successful processing
                        await redis.xack("task_queue", "workers", msg_id)

                    except Exception as e:
                        logger.error("task_execution_failed", task_id=task_id, error=str(e))
                        # Don't ack — message will be retried (or claimed by another worker)

        except Exception as e:
            logger.error("worker_loop_error", error=str(e))
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
```

### 4.2 Execution Service

```python
# backend/app/services/execution_service.py

MAX_ITERATIONS = 20

class ExecutionService:
    def __init__(self, session: AsyncSession, redis):
        self.session = session
        self.redis = redis

    async def execute_task(self, task_id: str, agent_id: str) -> None:
        task = await self.session.get(Task, task_id)
        agent = await self.session.get(Agent, agent_id, options=[
            selectinload(Agent.agent_class),
            selectinload(Agent.llm_config),
            selectinload(Agent.tools).selectinload(AgentTool.tool),
        ])

        if not task or not agent:
            logger.error("task_or_agent_not_found", task_id=task_id, agent_id=agent_id)
            return

        logger.info("task_execution_start", task_id=task_id, agent_id=agent_id, agent_name=agent.name)

        # Update task to STARTED state
        await self._create_task_event(task.id, agent.id, TaskEventTypeEnum.STARTED, {
            "message": f"{agent.name} started working on this task"
        })
        await self._broadcast_activity(agent, task, f"{agent.name} started: '{task.title}'", "info")

        # Build initial messages
        memory_context = await self._build_memory_context(agent, task)
        system_prompt = self._build_system_prompt(agent, task, memory_context)
        tools_schemas = self._build_tools_schemas(agent)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self._build_task_prompt(task)}
        ]

        provider = get_provider(agent.llm_config)
        iteration = 0

        try:
            while iteration < MAX_ITERATIONS:
                iteration += 1

                # Call LLM
                response = await provider.complete(
                    config=agent.llm_config,
                    messages=messages,
                    tools=tools_schemas if tools_schemas else None
                )

                # Log LLM call cost
                await self._log_llm_call(agent, task, agent.llm_config, response.usage)

                if response.finish_reason == "tool_calls":
                    # Execute each tool call
                    for tool_call in response.tool_calls:
                        result = await self._execute_tool_call(agent, task, tool_call)

                        # Append tool result to messages
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [tool_call.model_dump()]
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result.data if result.success else {"error": result.error})
                        })

                        # Broadcast activity
                        status = "200 OK" if result.success else f"ERROR: {result.error}"
                        await self._broadcast_activity(
                            agent, task,
                            f"{agent.name} called tool: {tool_call.name} → {status}",
                            "info" if result.success else "warning"
                        )

                elif response.finish_reason == "stop":
                    # Parse final response
                    final = self._parse_final_response(response.content)

                    if final["status"] == "COMPLETED":
                        await self._complete_task(agent, task, final.get("summary", "Task completed"))
                        return

                    elif final["status"] == "FAILED":
                        await self._fail_task(agent, task, final.get("reason", "Unknown failure"))
                        return

                    elif final["status"] == "PROGRESS":
                        # Progress update, continue loop
                        await self._create_task_event(task.id, agent.id, TaskEventTypeEnum.PROGRESS_UPDATE, {
                            "message": final.get("message", ""),
                            "iteration": iteration
                        })
                        messages.append({"role": "assistant", "content": response.content})
                        messages.append({"role": "user", "content": "Continue with the task."})

                    else:
                        # Unexpected format — treat as progress and continue
                        messages.append({"role": "assistant", "content": response.content})
                        messages.append({"role": "user", "content": "Continue or mark the task as COMPLETED or FAILED."})

                else:
                    # length or other finish reason
                    messages.append({"role": "assistant", "content": response.content or ""})
                    messages.append({"role": "user", "content": "Continue or summarize what you've done so far."})

            # Max iterations reached
            await self._fail_task(agent, task, f"Maximum iterations ({MAX_ITERATIONS}) reached without completion")

        except Exception as e:
            logger.error("execution_error", task_id=str(task.id), error=str(e))
            await self._fail_task(agent, task, f"Execution error: {str(e)}")
```

### 4.3 System Prompt Builder for Sub-Agents

```python
AGENT_SYSTEM_PROMPT = """
You are {name}, a {class_name} specialist in the {domain} domain.

## Your Profile
**Role**: {role_description}
**Communication Style**: {communication_style}
**Strengths**: {strengths}
**Working Style**: Detail-oriented: {detail_oriented}% | Risk tolerance: {risk_tolerance}% | Formality: {formality}%

## Context & Memory
{memory_context}

## Available Tools
You have access to the following tools:
{tools_list}

## Instructions
1. Read your task carefully and plan your approach
2. Use tools to gather information, perform calculations, or take actions
3. After each step, assess if you need more information or if you can proceed
4. When your task is COMPLETE, respond ONLY with this JSON:
   {{"status": "COMPLETED", "summary": "<2-3 sentence summary of what you accomplished>"}}
5. If you CANNOT complete the task, respond ONLY with this JSON:
   {{"status": "FAILED", "reason": "<explanation of why you cannot complete it>"}}
6. For intermediate progress, respond with:
   {{"status": "PROGRESS", "message": "<brief description of current step>"}}

## Important Rules
- Always use tools to verify facts — do not make up data
- If a tool fails, try an alternative approach before giving up
- Be precise and accurate in your outputs
- {extra_constraints}
"""

def _build_system_prompt(
    self,
    agent: Agent,
    task: Task,
    memory_context: str
) -> str:
    personality = agent.personality or {}

    # Format tools list for the prompt
    tools_list = "\n".join([
        f"- **{at.tool.name}** ({at.tool.type.value}): {at.tool.description}"
        for at in agent.tools
    ]) or "No tools assigned."

    return AGENT_SYSTEM_PROMPT.format(
        name=agent.name,
        class_name=agent.agent_class.name,
        domain=agent.domain.value,
        role_description=agent.role_description,
        communication_style=personality.get("communication_style", "professional"),
        strengths=", ".join(personality.get("strengths", [])) or "General problem solving",
        detail_oriented=personality.get("detail_oriented", 50),
        risk_tolerance=personality.get("risk_tolerance", 50),
        formality=personality.get("formality", 50),
        memory_context=memory_context or "No relevant prior context.",
        tools_list=tools_list,
        extra_constraints="Do not exceed scope of this task."
    )
```

### 4.4 Task Prompt Builder

```python
def _build_task_prompt(self, task: Task) -> str:
    return f"""## Your Task

**Title**: {task.title}

**Description**:
{task.description}

**Priority**: {task.priority.value}
**Domain**: {task.domain_hint.value if task.domain_hint else "General"}

Please complete this task now. Begin by planning your approach, then execute it step by step.
"""
```

### 4.5 Final Response Parser

```python
import json
import re

def _parse_final_response(self, content: str) -> dict:
    """
    Extract the JSON status object from agent response.
    Handles cases where the agent includes extra text around the JSON.
    """
    if not content:
        return {"status": "PROGRESS", "message": ""}

    # Try direct JSON parse first
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from content (agent may add prose around it)
    json_match = re.search(r'\{[^{}]*"status"\s*:\s*"[^"]+[^{}]*\}', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Default: treat as progress
    return {"status": "PROGRESS", "message": content[:200]}
```

---

## 5. Task State Machine

```
BACKLOG ──────────────────────────────────────────────────────────────────▶ (deleted)
   │                                                                 (manual)
   │ ASSIGN_TASK                                                         │
   ▼                                                                      │
IN_PROGRESS ───────────────────────── DONE ◄────────── IN_REVIEW ◄──────┘
   │                                                       ▲
   │ (tool execution loop)                                 │
   │                                                       │ (manual drag)
   │ COMPLETED response                                    │
   └──────────────────────────────────────────────────────┘
   │
   │ FAILED response or max iterations
   ▼
FAILED ──────────────────────────────▶ BACKLOG (retry, manual)
```

### Valid Transitions:

| From | To | Trigger |
|------|----|---------|
| BACKLOG | IN_PROGRESS | Assignment (orchestrator or manual) |
| IN_PROGRESS | IN_REVIEW | Manual drag or agent sets IN_REVIEW |
| IN_PROGRESS | DONE | Agent completes task |
| IN_PROGRESS | FAILED | Agent fails, max iterations |
| IN_REVIEW | DONE | Manual approval |
| IN_REVIEW | IN_PROGRESS | Rejection, back to work |
| FAILED | BACKLOG | Manual retry |
| Any | Any | Manual drag on Kanban board |

---

## 6. Helper Methods

```python
async def _execute_tool_call(
    self,
    agent: Agent,
    task: Task,
    tool_call: LlmToolCall
) -> ToolResult:
    """Find the tool, check permissions, execute, log event."""
    # Find the tool by name in agent's assigned tools
    agent_tool = next(
        (at for at in agent.tools if at.tool.name == tool_call.name),
        None
    )

    if not agent_tool:
        result = ToolResult(success=False, error=f"Tool '{tool_call.name}' not assigned to this agent")
    else:
        result = await execute_tool(agent, agent_tool.tool, tool_call.arguments)

    # Log TOOL_CALL event
    await self._create_task_event(task.id, agent.id, TaskEventTypeEnum.TOOL_CALL, {
        "tool_name": tool_call.name,
        "input": tool_call.arguments,
        "output": result.data if result.success else None,
        "error": result.error if not result.success else None,
        "duration_ms": result.metadata.get("duration_ms", 0),
        "success": result.success
    })

    return result

async def _complete_task(self, agent: Agent, task: Task, summary: str) -> None:
    task.status = TaskStatusEnum.DONE
    task.completed_at = datetime.utcnow()
    agent.status = AgentStatusEnum.IDLE
    agent.current_task_id = None
    agent.last_active_at = datetime.utcnow()

    await self._create_task_event(task.id, agent.id, TaskEventTypeEnum.COMPLETED, {
        "summary": summary
    })

    await self._broadcast_activity(
        agent, task,
        f"{agent.name} completed: '{task.title}'",
        "success"
    )

    # Broadcast Kanban update
    await self.redis.publish(f"ws:kanban", json.dumps({
        "type": "task_status_changed",
        "payload": {"task_id": str(task.id), "new_status": "DONE"}
    }))

    await self.session.commit()

    # Generate task memory summary (async, non-blocking)
    asyncio.create_task(self._generate_task_memory(task, agent))

async def _fail_task(self, agent: Agent, task: Task, reason: str) -> None:
    task.status = TaskStatusEnum.FAILED
    agent.status = AgentStatusEnum.ERROR
    agent.current_task_id = None

    await self._create_task_event(task.id, agent.id, TaskEventTypeEnum.FAILED, {
        "reason": reason
    })

    await self._broadcast_activity(
        agent, task,
        f"{agent.name} failed task: '{task.title}' — {reason[:100]}",
        "error"
    )

    await self.session.commit()

async def _broadcast_activity(
    self,
    agent: Agent,
    task: Task,
    message: str,
    severity: str
) -> None:
    await self.redis.publish("ws:global", json.dumps({
        "type": "activity_feed",
        "channel": "global",
        "payload": {
            "message": message,
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "agent_domain": agent.domain.value,
            "task_id": str(task.id),
            "task_title": task.title,
            "severity": severity
        },
        "timestamp": datetime.utcnow().isoformat()
    }))
```

---

## 7. Tools Schema Builder (for LLM function calling)

```python
def _build_tools_schemas(self, agent: Agent) -> list[dict]:
    """
    Convert assigned tools to OpenAI function_calling format.
    This list is passed to the LLM provider.
    """
    schemas = []
    for agent_tool in agent.tools:
        tool = agent_tool.tool
        schemas.append({
            "type": "function",
            "function": {
                "name": tool.name.replace(" ", "_").lower(),
                "description": tool.description,
                "parameters": tool.input_schema or {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        })
    return schemas
```

---

## 8. Prompt Engineering Guidelines

### For Orchestrator
- Use **low temperature** (0.1–0.3) for consistent JSON output
- Include team context in every call (agent statuses change frequently)
- Limit recent tasks to last 10 to keep context window manageable
- Add examples of action JSON in the prompt for few-shot guidance

### For Sub-Agents
- Use **moderate temperature** (0.5–0.8) for more natural outputs
- Inject memory context early in system prompt (before tools)
- Keep tool descriptions concise but precise — they directly influence tool selection
- Add domain-specific constraints in `extra_constraints` per class (e.g., Finance Manager: "Always cite data sources")
- Personality sliders (detail_oriented, risk_tolerance) should map to prompt phrases:
  - `detail_oriented > 70` → "Be thorough and check every detail"
  - `risk_tolerance < 30` → "Prefer conservative approaches, verify before acting"
  - `formality > 70` → "Use formal language and structured outputs"
