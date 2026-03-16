"""
Orchestrator Service - Coordinates multi-agent task execution

The orchestrator is responsible for:
1. Receiving high-level tasks from users
2. Breaking down complex tasks into subtasks
3. Assigning subtasks to appropriate agents
4. Monitoring execution and handling dependencies
5. Aggregating results and reporting back
"""

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.agent import Agent
from ..models.enums import DomainEnum, PriorityEnum
from ..models.task import Task
from .agent_service import AgentService
from .execution_service import ExecutionService
from .llm_service import LLMService
from .memory_service import MemoryService
from .task_service import TaskService


class SubtaskDefinition:
    """Definition of a subtask created by the orchestrator"""

    def __init__(
        self,
        title: str,
        description: str,
        domain: DomainEnum,
        priority: PriorityEnum = PriorityEnum.MEDIUM,
        depends_on: list[UUID] | None = None,
        input_data: dict | None = None,
    ):
        self.title = title
        self.description = description
        self.domain = domain
        self.priority = priority
        self.depends_on = depends_on or []
        self.input_data = input_data or {}
        self.id = uuid4()


class OrchestratorService:
    """
    Service for orchestrating multi-agent task execution.

    The orchestrator acts as a meta-agent that:
    - Analyzes complex tasks
    - Plans execution strategy
    - Coordinates multiple specialized agents
    - Synthesizes final results
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_service = TaskService(session)
        self.agent_service = AgentService(session)
        self.execution_service = ExecutionService(session)
        self.memory_service = MemoryService(session)
        self.llm_service = LLMService(session)

    async def process_task(
        self,
        title: str,
        description: str,
        llm_config_id: UUID,
        priority: PriorityEnum = PriorityEnum.MEDIUM,
        requested_domain: DomainEnum | None = None,
        input_data: dict | None = None,
        created_by: str = "user",
    ) -> dict[str, Any]:
        """
        Process a high-level task through the orchestrator.

        Args:
            title: Task title
            description: Task description
            llm_config_id: LLM config for planning
            priority: Task priority
            requested_domain: Optional domain hint
            input_data: Optional input data
            created_by: Who created the task

        Returns:
            Processing result with created tasks
        """
        # Create parent task
        parent_task = await self.task_service.create_task(
            title=title,
            description=description,
            priority=priority,
            domain_hint=requested_domain,
            created_by=created_by,
        )

        # Analyze task complexity
        analysis = await self._analyze_task(
            title=title,
            description=description,
            llm_config_id=llm_config_id,
        )

        # Decide strategy
        if analysis["complexity"] == "simple":
            # Single agent execution
            return await self._execute_simple_task(
                parent_task=parent_task,
                analysis=analysis,
                llm_config_id=llm_config_id,
            )
        else:
            # Multi-agent orchestration
            return await self._execute_complex_task(
                parent_task=parent_task,
                analysis=analysis,
                llm_config_id=llm_config_id,
            )

    async def _analyze_task(
        self,
        title: str,
        description: str,
        llm_config_id: UUID,
    ) -> dict[str, Any]:
        """Analyze task to determine complexity and approach"""

        prompt = f"""Analyze the following task and determine the best execution approach.

Task: {title}
Description: {description}

Analyze and respond with a JSON object:
{{
    "complexity": "simple|complex",
    "reasoning": "brief explanation",
    "domains": ["list", "of", "relevant", "domains"],
    "requires_multiple_agents": true|false,
    "estimated_steps": number,
    "can_parallelize": true|false
}}

Guidelines:
- "simple": Single step, single domain, clear instructions
- "complex": Multiple steps, multiple domains, or requires coordination
- Domains: software, data, finance, legal, marketing, hr, operations, research
"""

        response = await self.llm_service.complete(
            config_id=llm_config_id,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            # Extract JSON from response
            content = response.content or "{}"
            # Find JSON block
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            analysis = json.loads(content.strip())
        except json.JSONDecodeError:
            # Fallback analysis
            analysis = {
                "complexity": "simple",
                "reasoning": "Failed to parse analysis, defaulting to simple",
                "domains": ["software"],
                "requires_multiple_agents": False,
                "estimated_steps": 1,
                "can_parallelize": False,
            }

        return analysis

    async def _execute_simple_task(
        self,
        parent_task: Task,
        analysis: dict[str, Any],
        llm_config_id: UUID,
    ) -> dict[str, Any]:
        """Execute a simple task with a single agent"""

        # Find best agent for the domain
        domain = self._parse_domain(
            analysis["domains"][0] if analysis["domains"] else "software"
        )

        agent = await self._find_or_create_agent(
            domain=domain,
            llm_config_id=llm_config_id,
        )

        if not agent:
            return {
                "success": False,
                "error": f"No agent available for domain: {domain}",
                "parent_task_id": str(parent_task.id),
            }

        # Assign task to agent
        await self.task_service.assign_task(
            task_id=parent_task.id,
            agent_id=agent.id,
        )

        # Execute
        result = await self.execution_service.execute_task(
            task_id=parent_task.id,
            max_iterations=10,
        )

        return {
            "success": result["success"],
            "parent_task_id": str(parent_task.id),
            "assigned_agent": agent.name,
            "execution_result": result,
        }

    async def _execute_complex_task(
        self,
        parent_task: Task,
        analysis: dict[str, Any],
        llm_config_id: UUID,
    ) -> dict[str, Any]:
        """Execute a complex task by breaking it down into subtasks"""

        # Decompose task into subtasks
        subtasks = await self._decompose_task(
            parent_task=parent_task,
            analysis=analysis,
            llm_config_id=llm_config_id,
        )

        # Create subtasks in database
        created_tasks = []
        for subtask_def in subtasks:
            task = await self.task_service.create_task(
                title=subtask_def.title,
                description=subtask_def.description,
                priority=subtask_def.priority,
                domain_hint=subtask_def.domain,
                parent_task_id=parent_task.id,
                input_data=subtask_def.input_data,
                created_by="orchestrator",
            )
            created_tasks.append((task, subtask_def))

        # Assign agents to subtasks
        assignments = await self._assign_agents_to_tasks(
            tasks=created_tasks,
            llm_config_id=llm_config_id,
        )

        # Execute subtasks
        results = await self._execute_subtasks(
            assignments=assignments,
            can_parallelize=analysis.get("can_parallelize", False),
        )

        # Synthesize results
        final_result = await self._synthesize_results(
            parent_task=parent_task,
            subtask_results=results,
            llm_config_id=llm_config_id,
        )

        return {
            "success": final_result["success"],
            "parent_task_id": str(parent_task.id),
            "subtasks": [
                {
                    "id": str(task.id),
                    "title": task.title,
                    "domain": task.domain_hint,
                    "status": task.status.value,
                }
                for task, _ in created_tasks
            ],
            "final_result": final_result,
        }

    async def _decompose_task(
        self,
        parent_task: Task,
        analysis: dict[str, Any],
        llm_config_id: UUID,
    ) -> list[SubtaskDefinition]:
        """Decompose complex task into subtasks"""

        prompt = f"""Break down the following complex task into subtasks.

Parent Task: {parent_task.title}
Description: {parent_task.description}

Domains involved: {", ".join(analysis.get("domains", ["software"]))}
Estimated steps: {analysis.get("estimated_steps", 3)}

Respond with a JSON array of subtasks:
[
    {{
        "title": "Subtask title",
        "description": "Detailed description",
        "domain": "software|data|finance|legal|marketing|hr|operations|research",
        "priority": "high|medium|low",
        "depends_on": [0],  // indices of subtasks this depends on
        "input_data": {{}}  // any specific input needed
    }}
]

Guidelines:
- Make subtasks clear and actionable
- Each subtask should be assignable to a single agent
- Specify dependencies when order matters
- Use appropriate domains for each subtask
"""

        response = await self.llm_service.complete(
            config_id=llm_config_id,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            content = response.content or "[]"
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            subtask_data = json.loads(content.strip())
        except json.JSONDecodeError:
            # Fallback: single subtask
            subtask_data = [
                {
                    "title": f"Execute: {parent_task.title}",
                    "description": parent_task.description,
                    "domain": analysis.get("domains", ["software"])[0],
                    "priority": "medium",
                    "depends_on": [],
                    "input_data": {},
                }
            ]

        # Convert to SubtaskDefinition
        subtasks = []
        for data in subtask_data:
            subtasks.append(
                SubtaskDefinition(
                    title=data["title"],
                    description=data["description"],
                    domain=self._parse_domain(data["domain"]),
                    priority=self._parse_priority(data.get("priority", "medium")),
                    depends_on=[],  # We'll resolve dependencies after creating UUIDs
                    input_data=data.get("input_data", {}),
                )
            )

        return subtasks

    async def _assign_agents_to_tasks(
        self,
        tasks: list[tuple[Task, SubtaskDefinition]],
        llm_config_id: UUID,
    ) -> list[tuple[Task, Agent]]:
        """Assign agents to subtasks"""
        assignments = []

        for task, subtask_def in tasks:
            agent = await self._find_or_create_agent(
                domain=subtask_def.domain,
                llm_config_id=llm_config_id,
            )

            if agent:
                await self.task_service.assign_task(
                    task_id=task.id,
                    agent_id=agent.id,
                )
                assignments.append((task, agent))

        return assignments

    async def _execute_subtasks(
        self,
        assignments: list[tuple[Task, Agent]],
        can_parallelize: bool,
    ) -> list[dict[str, Any]]:
        """Execute subtasks"""
        results = []

        if can_parallelize:
            # In a real implementation, use asyncio.gather or worker queue
            # For now, execute sequentially
            for task, agent in assignments:
                result = await self.execution_service.execute_task(
                    task_id=task.id,
                    max_iterations=10,
                )
                results.append(
                    {
                        "task_id": str(task.id),
                        "agent": agent.name,
                        "result": result,
                    }
                )
        else:
            # Sequential execution
            for task, agent in assignments:
                result = await self.execution_service.execute_task(
                    task_id=task.id,
                    max_iterations=10,
                )
                results.append(
                    {
                        "task_id": str(task.id),
                        "agent": agent.name,
                        "result": result,
                    }
                )

        return results

    async def _synthesize_results(
        self,
        parent_task: Task,
        subtask_results: list[dict[str, Any]],
        llm_config_id: UUID,
    ) -> dict[str, Any]:
        """Synthesize subtask results into final output"""

        # Collect successful results
        successful_results = [
            r for r in subtask_results if r["result"].get("success", False)
        ]

        if not successful_results:
            return {
                "success": False,
                "error": "All subtasks failed",
            }

        # Build synthesis prompt
        results_summary = "\n\n".join(
            [
                f"Subtask: {r['agent']}\n{r['result'].get('output', 'No output')}"
                for r in successful_results
            ]
        )

        prompt = f"""Synthesize the following subtask results into a coherent final response.

Original Task: {parent_task.title}
Description: {parent_task.description}

Subtask Results:
{results_summary}

Provide a comprehensive summary that:
1. Integrates all subtask results
2. Presents findings clearly
3. Highlights any key insights or decisions
"""

        response = await self.llm_service.complete(
            config_id=llm_config_id,
            messages=[{"role": "user", "content": prompt}],
        )

        return {
            "success": True,
            "output": response.content,
            "subtask_count": len(subtask_results),
            "successful_count": len(successful_results),
        }

    async def _find_or_create_agent(
        self,
        domain: DomainEnum,
        llm_config_id: UUID,
    ) -> Agent | None:
        """Find or create an agent for a domain"""
        # Find available agent
        agents = await self.agent_service.get_agents(
            domain=domain.value,
            limit=1,
        )

        if agents:
            return agents[0]

        # Find agent class for domain
        classes = await self.agent_service.get_agent_classes(
            domain=domain.value,
        )

        if not classes:
            return None

        # Create agent
        agent_class = classes[0]
        agent = await self.agent_service.create_agent(
            name=f"{domain.value.title()} Agent {datetime.utcnow().strftime('%H%M')}",
            gender="neutral",
            class_id=agent_class.id,
            domain=domain.value,
            role_description=f"Specialized agent for {domain.value} tasks",
            personality={"analytical": 0.8, "creative": 0.4},
            llm_config_id=llm_config_id,
            avatar_config={"color": "#3B82F6"},
        )

        return agent

    def _parse_domain(self, domain_str: str) -> DomainEnum:
        """Parse domain string to enum"""
        try:
            return DomainEnum(domain_str.lower())
        except ValueError:
            return DomainEnum.SOFTWARE

    def _parse_priority(self, priority_str: str) -> PriorityEnum:
        """Parse priority string to enum"""
        try:
            return PriorityEnum(priority_str.upper())
        except ValueError:
            return PriorityEnum.MEDIUM
