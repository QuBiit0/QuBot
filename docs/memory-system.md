# Qubot — Memory System

> **Module**: `backend/app/services/memory_service.py`
> **Models**: `GlobalMemory`, `AgentMemory`, `TaskMemory` (see database-schema.md)

---

## 1. Overview

Qubot has three types of memory, each serving a different purpose:

| Type | Scope | Written by | Read by |
|------|-------|-----------|---------|
| `GlobalMemory` | All agents | User (via UI) / Orchestrator | All agents, context injection |
| `AgentMemory` | Per agent | Agent itself (via tool) / User | That agent, context injection |
| `TaskMemory` | Per task | System (auto, post-task) | Future tasks with similar domain |

Memory is injected into agent prompts as context. Currently uses SQL text search; designed for future vector DB upgrade.

---

## 2. Memory Types

### 2.1 GlobalMemory

Shared knowledge available to all agents. Examples:
- Company overview, mission, values
- Technical documentation
- Business rules and constraints
- Preferences and style guides

```python
class GlobalMemory(SQLModel, table=True):
    id: UUID
    key: str              # Unique identifier, e.g. "company_overview"
    content: str          # The actual knowledge (text, markdown, or JSON string)
    content_type: str     # "text" | "markdown" | "json"
    tags: list[str]       # For filtering, e.g. ["finance", "q3", "targets"]
    embedding_ref: str    # Future: vector chunk ID
    created_at: datetime
    updated_at: datetime
```

### 2.2 AgentMemory

Per-agent persistent memory. Agents accumulate knowledge about their domain over time. Examples:
- "User prefers financial data in markdown tables"
- "API endpoint /v2/financials requires date range parameter"
- "Don't use cached data for Q3 2024, always fetch fresh"

```python
class AgentMemory(SQLModel, table=True):
    id: UUID
    agent_id: UUID        # Which agent owns this memory
    key: str              # Identifier, e.g. "user_preference_output_format"
    content: str          # The memory content
    importance: int       # 1 (low) to 5 (critical) — affects retrieval priority
    last_accessed: datetime
    created_at, updated_at: datetime
```

### 2.3 TaskMemory

LLM-generated summary of a completed task. Created automatically after task completion.

```python
class TaskMemory(SQLModel, table=True):
    id: UUID
    task_id: UUID         # Links to the completed task
    summary: str          # 2-3 paragraph LLM-generated summary
    key_facts: list[str]  # Bullet points: important findings, decisions made
    created_at: datetime
```

---

## 3. Memory Service

```python
# backend/app/services/memory_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from uuid import UUID
from typing import Optional
from ..models.memory import GlobalMemory, AgentMemory, TaskMemory
from ..models.enums import DomainEnum


class MemoryService:

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Global Memory ────────────────────────────────────────────────────

    async def get_global_memories(
        self,
        tags: Optional[list[str]] = None,
        search_query: Optional[str] = None,
        limit: int = 10
    ) -> list[GlobalMemory]:
        """
        Retrieve global memories, optionally filtered by tags or text search.
        """
        query = select(GlobalMemory).order_by(GlobalMemory.updated_at.desc())

        if tags:
            # Filter memories that contain ANY of the given tags
            # JSON array contains check (PostgreSQL)
            from sqlalchemy import cast
            from sqlalchemy.dialects.postgresql import JSONB
            # Use PostgreSQL ?| operator for JSON array overlap
            query = query.where(
                GlobalMemory.tags.cast(JSONB).op('?|')(tags)
            )

        if search_query:
            # Simple text search (future: replace with vector similarity)
            query = query.where(
                GlobalMemory.content.ilike(f"%{search_query}%")
            )

        query = query.limit(limit)
        return (await self.session.exec(query)).all()

    async def create_global_memory(
        self,
        key: str,
        content: str,
        content_type: str = "text",
        tags: list[str] = None
    ) -> GlobalMemory:
        memory = GlobalMemory(
            key=key,
            content=content,
            content_type=content_type,
            tags=tags or []
        )
        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)
        return memory

    async def update_global_memory(self, id: UUID, **kwargs) -> Optional[GlobalMemory]:
        memory = await self.session.get(GlobalMemory, id)
        if not memory:
            return None
        for key, value in kwargs.items():
            setattr(memory, key, value)
        from datetime import datetime
        memory.updated_at = datetime.utcnow()
        await self.session.commit()
        return memory

    # ── Agent Memory ──────────────────────────────────────────────────────

    async def get_agent_memories(
        self,
        agent_id: UUID,
        limit: int = 10,
        min_importance: int = 1
    ) -> list[AgentMemory]:
        """
        Retrieve agent memories sorted by importance (highest first), then recency.
        """
        query = (
            select(AgentMemory)
            .where(AgentMemory.agent_id == agent_id)
            .where(AgentMemory.importance >= min_importance)
            .order_by(AgentMemory.importance.desc(), AgentMemory.last_accessed.desc())
            .limit(limit)
        )
        memories = (await self.session.exec(query)).all()

        # Update last_accessed for retrieved memories
        from datetime import datetime
        for mem in memories:
            mem.last_accessed = datetime.utcnow()
        await self.session.commit()

        return memories

    async def write_agent_memory(
        self,
        agent_id: UUID,
        key: str,
        content: str,
        importance: int = 3
    ) -> AgentMemory:
        """
        Upsert an agent memory entry.
        If key already exists for this agent, update it. Otherwise create new.
        """
        # Check for existing entry with same key
        existing = await self.session.exec(
            select(AgentMemory)
            .where(AgentMemory.agent_id == agent_id)
            .where(AgentMemory.key == key)
        ).first()

        if existing:
            existing.content = content
            existing.importance = importance
            from datetime import datetime
            existing.updated_at = datetime.utcnow()
            await self.session.commit()
            return existing
        else:
            memory = AgentMemory(
                agent_id=agent_id,
                key=key,
                content=content,
                importance=importance
            )
            self.session.add(memory)
            await self.session.commit()
            await self.session.refresh(memory)
            return memory

    # ── Task Memory ───────────────────────────────────────────────────────

    async def get_task_memory(self, task_id: UUID) -> Optional[TaskMemory]:
        return await self.session.get(TaskMemory, task_id)

    async def get_recent_task_memories(
        self,
        domain: Optional[DomainEnum] = None,
        limit: int = 5
    ) -> list[dict]:
        """
        Get recent TaskMemory entries, optionally filtered by domain.
        Used for injecting past task context into agent prompts.
        """
        from ..models.task import Task
        query = (
            select(TaskMemory, Task.title, Task.domain_hint)
            .join(Task, TaskMemory.task_id == Task.id)
            .order_by(TaskMemory.created_at.desc())
        )
        if domain:
            query = query.where(Task.domain_hint == domain)
        query = query.limit(limit)

        results = (await self.session.exec(query)).all()
        return [
            {
                "task_title": row[1],
                "domain": row[2],
                "summary": row[0].summary,
                "key_facts": row[0].key_facts
            }
            for row in results
        ]
```

---

## 4. Context Injection (Agent Prompt Builder)

Memory is injected into agent prompts before the task description.

```python
# backend/app/services/memory_service.py (continued)

async def build_agent_context(
    self,
    agent_id: UUID,
    task_domain: Optional[DomainEnum] = None,
) -> str:
    """
    Build the memory context block to inject into agent system prompt.
    Returns formatted markdown string.
    """
    sections = []

    # 1. Global memories filtered by domain tag
    domain_tag = task_domain.value.lower() if task_domain else None
    global_mems = await self.get_global_memories(
        tags=[domain_tag] if domain_tag else None,
        limit=3
    )
    if global_mems:
        sections.append("### Shared Knowledge")
        for mem in global_mems:
            sections.append(f"**{mem.key}**:\n{mem.content[:500]}")

    # 2. Agent-specific memories (high importance first)
    agent_mems = await self.get_agent_memories(
        agent_id=agent_id,
        limit=8,
        min_importance=2  # Skip importance=1 (trivial) in prompts
    )
    if agent_mems:
        sections.append("### Your Memory")
        for mem in agent_mems:
            importance_label = "⚠️" if mem.importance >= 4 else "ℹ️"
            sections.append(f"{importance_label} **{mem.key}**: {mem.content[:300]}")

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
```

---

## 5. Automatic Task Memory Generation

After a task is marked DONE, an LLM call generates a structured summary saved to `TaskMemory`.

```python
# Called from ExecutionService._generate_task_memory()

async def generate_task_memory(
    self,
    task: "Task",
    agent: "Agent",
    task_events: list["TaskEvent"],
    llm_config: "LlmConfig"
) -> TaskMemory:
    """
    Use LLM to summarize a completed task into structured memory.
    This is called asynchronously after task completion (non-blocking).
    """

    # Format task events for the summarization prompt
    events_text = "\n".join([
        f"- [{e.type.value}] {json.dumps(e.payload)[:200]}"
        for e in task_events
        if e.type in (TaskEventTypeEnum.TOOL_CALL, TaskEventTypeEnum.COMPLETED,
                      TaskEventTypeEnum.PROGRESS_UPDATE)
    ])

    summary_prompt = f"""
Summarize this completed AI agent task into structured memory.

## Task
Title: {task.title}
Description: {task.description}

## What Happened (event log)
{events_text or "No detailed events recorded."}

## Output Format (JSON)
{{
  "summary": "<2-3 sentences: what was accomplished, how, key outcome>",
  "key_facts": [
    "<specific finding or fact worth remembering>",
    "<another fact>",
    ...
  ]
}}

Be specific and factual. Include concrete values, URLs, file paths, or data points from the events.
Output ONLY valid JSON.
"""

    from ..llm.registry import get_provider
    provider = get_provider(llm_config)

    try:
        response = await provider.complete(
            config=llm_config,
            messages=[
                {"role": "user", "content": summary_prompt}
            ]
        )

        parsed = json.loads(response.content)
        task_memory = TaskMemory(
            task_id=task.id,
            summary=parsed.get("summary", "Task completed"),
            key_facts=parsed.get("key_facts", [])
        )
        self.session.add(task_memory)
        await self.session.commit()
        return task_memory

    except Exception as e:
        # If summarization fails, create a basic memory entry
        task_memory = TaskMemory(
            task_id=task.id,
            summary=f"Task '{task.title}' completed by {agent.name}.",
            key_facts=[]
        )
        self.session.add(task_memory)
        await self.session.commit()
        return task_memory
```

---

## 6. Memory Write Tool (for Agents)

Agents can write to their own memory using the `memory_write` tool. This is a built-in tool that agents receive if configured.

```python
# This tool is NOT in the DB — it's auto-available to all agents
# It wraps MemoryService.write_agent_memory()

class MemoryWriteTool(BaseTool):
    """
    Allows an agent to store important information in their persistent memory.

    Use this when you discover:
    - User preferences or requirements
    - Important facts about the domain
    - Information that will be useful in future tasks
    - Credentials or endpoints that should be remembered
    """

    name = "memory_write"
    description = (
        "Store important information in your persistent memory for future use. "
        "Use importance 5 for critical facts, 3 for useful context, 1 for minor notes."
    )

    # Input schema for LLM
    INPUT_SCHEMA = {
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "Short identifier for this memory (e.g., 'user_output_preference')"
            },
            "content": {
                "type": "string",
                "description": "The information to remember"
            },
            "importance": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "1=trivial, 3=useful, 5=critical"
            }
        },
        "required": ["key", "content"]
    }

    async def execute(self, agent, **kwargs) -> ToolResult:
        key = kwargs.get("key", "")
        content = kwargs.get("content", "")
        importance = kwargs.get("importance", 3)

        if not key or not content:
            return ToolResult(success=False, error="key and content are required")

        memory = await self.memory_service.write_agent_memory(
            agent_id=agent.id,
            key=key,
            content=content,
            importance=min(max(int(importance), 1), 5)
        )
        return ToolResult(
            success=True,
            data={"memory_id": str(memory.id), "key": key, "importance": memory.importance}
        )
```

---

## 7. Future Vector DB Integration

The current implementation uses SQL text search. The design supports upgrading to vector similarity search without changing the interface.

### Current (SQL LIKE):
```python
# Simple text search in MemoryService.get_global_memories()
query.where(GlobalMemory.content.ilike(f"%{search_query}%"))
```

### Future (pgvector):
```python
# Option A: pgvector extension
# 1. Add vector column to GlobalMemory: embedding vector(1536)
# 2. Add pgvector index: CREATE INDEX ON global_memory USING ivfflat (embedding vector_cosine_ops)
# 3. Replace LIKE search with:
query.order_by(
    GlobalMemory.embedding.cosine_distance(query_embedding)
).limit(k)

# Option B: Chroma/Weaviate external store
# - Store embeddings in vector DB
# - GlobalMemory.embedding_ref stores the vector DB document ID
# - Replace LIKE search with vector DB similarity query
```

### Abstraction Layer (future-proof interface):

```python
class MemoryStore(ABC):
    @abstractmethod
    async def search(self, query: str, k: int = 5, tags: list[str] = None) -> list[dict]:
        """Return top-k relevant memory entries for a query."""
        ...

class SqlMemoryStore(MemoryStore):
    """Current implementation — SQL LIKE search."""
    async def search(self, query, k=5, tags=None):
        # ... SQL LIKE search

class PgvectorMemoryStore(MemoryStore):
    """Future implementation — pgvector cosine similarity."""
    async def search(self, query, k=5, tags=None):
        # Generate embedding for query
        # Search by cosine distance
        ...
```

### Embedding Field Preparation

`GlobalMemory.embedding_ref` is already in the schema. When vector DB is added:
1. On `create_global_memory`: generate embedding, store in vector DB, save chunk ID to `embedding_ref`
2. On `get_global_memories`: use vector similarity instead of LIKE

---

## 8. Memory Management Guidelines

### What Agents Should Store (importance levels):

| Importance | Example |
|-----------|---------|
| 5 (Critical) | "API key for finance service is stored in ENV var FINANCE_KEY" |
| 4 (High) | "User wants all reports in Spanish" |
| 3 (Useful) | "Finance API rate limit: 100 req/min" |
| 2 (Context) | "Q3 data available at /api/q3/2024" |
| 1 (Trivial) | "Last request took 342ms" |

### Memory Retention Policy:

- `AgentMemory`: Indefinite (manual deletion via UI)
- `TaskMemory`: Indefinite (manual deletion via UI)
- `GlobalMemory`: Indefinite (user-managed)
- `LlmCallLog`: 90 days (configurable, for cost reporting)

### UI Memory Management:

- `/settings/memory` page: view/edit GlobalMemory entries
- Agent detail page: view/delete AgentMemory entries
- No automatic pruning in v1 — add scheduled cleanup job in v2
