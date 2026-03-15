"""
Agent implementation template.

This is the main agent class that you can customize for your specific use case.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import yaml
import structlog
from pydantic import BaseModel

# Importar desde LMAgent (ajustar paths según estructura real)
# from lmagent.core.base_agent import BaseAgent
# from lmagent.core.tool_registry import ToolRegistry
# from lmagent.core.llm_provider import get_provider
# from lmagent.core.trajectory import TrajectoryLogger
# from lmagent.core.cost_tracker import CostTracker

logger = structlog.get_logger()


class AgentConfig(BaseModel):
    """Configuration for the agent."""
    name: str
    display_name: str
    description: str
    version: str = "1.0.0"
    
    # LLM config
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # Limits
    max_iterations: int = 10
    max_cost: float = 2.00
    timeout_seconds: int = 300
    
    # Tools
    tools: list[str] = []
    
    @classmethod
    def from_yaml(cls, path: str | Path) -> "AgentConfig":
        """Load config from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        
        return cls(
            name=data["name"],
            display_name=data["display_name"],
            description=data["description"],
            version=data.get("version", "0.1.0"),
            llm_provider=data.get("llm", {}).get("provider", "openai"),
            llm_model=data.get("llm", {}).get("model", "gpt-4o"),
            temperature=data.get("llm", {}).get("temperature", 0.7),
            max_tokens=data.get("llm", {}).get("max_tokens", 4096),
            max_iterations=data.get("limits", {}).get("max_iterations", 10),
            max_cost=data.get("limits", {}).get("max_cost", 2.00),
            timeout_seconds=data.get("limits", {}).get("timeout_seconds", 300),
            tools=data.get("tools", {}).get("from_registry", []),
        )


class MyAgent:
    """
    Custom agent implementation.
    
    This agent [describe what your agent does].
    
    Example:
        >>> agent = MyAgent.from_config("config.yaml")
        >>> result = await agent.run("Your input here")
        >>> print(result)
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize the agent with configuration."""
        self.config = config
        self.history: list[dict[str, Any]] = []
        self.iteration_count = 0
        self.total_cost = 0.0
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        # Initialize tools
        self.tools = self._load_tools()
        
        # Initialize LLM provider
        # self.llm = get_provider(config.llm_provider, config.llm_model)
        
        # Initialize tracking
        # self.trajectory = TrajectoryLogger()
        # self.cost_tracker = CostTracker(max_cost=config.max_cost)
        
        logger.info(
            "agent_initialized",
            name=config.name,
            model=config.llm_model,
            tools=list(self.tools.keys())
        )
    
    @classmethod
    def from_config(cls, config_path: str | Path) -> "MyAgent":
        """Create agent from config file."""
        config = AgentConfig.from_yaml(config_path)
        return cls(config)
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file."""
        prompt_path = Path(__file__).parent / "prompts" / "system.md"
        if prompt_path.exists():
            return prompt_path.read_text()
        return "You are a helpful AI assistant."
    
    def _load_tools(self) -> dict[str, Any]:
        """Load and initialize tools."""
        tools = {}
        
        # Load tools from registry
        # for tool_name in self.config.tools:
        #     tools[tool_name] = ToolRegistry.get(tool_name)
        
        # Load custom tools
        # from .tools import custom_tool
        # tools["custom_tool"] = custom_tool.CustomTool()
        
        return tools
    
    async def run(
        self,
        user_input: str,
        context: dict[str, Any] | None = None
    ) -> str:
        """
        Run the agent with user input.
        
        Args:
            user_input: The user's query or task.
            context: Optional additional context.
        
        Returns:
            The agent's final response.
        
        Raises:
            CostLimitExceeded: If the cost limit is reached.
            MaxIterationsExceeded: If max iterations is reached.
        """
        logger.info(
            "agent_run_start",
            input_length=len(user_input),
            context_keys=list(context.keys()) if context else []
        )
        
        # Add user message to history
        self.history.append({
            "role": "user",
            "content": user_input
        })
        
        # Main agent loop
        for iteration in range(self.config.max_iterations):
            self.iteration_count = iteration + 1
            
            logger.info(f"🤠 INFO ========================= STEP {iteration + 1} =========================")
            
            # Get LLM response
            # response = await self.llm.complete(
            #     system_prompt=self.system_prompt,
            #     messages=self.history,
            #     tools=self.tools,
            #     temperature=self.config.temperature,
            #     max_tokens=self.config.max_tokens
            # )
            
            # For template purposes, simulate a response
            response = await self._simulate_response(user_input, iteration)
            
            # Track cost
            # self.cost_tracker.track(
            #     model=self.config.llm_model,
            #     input_tokens=response.usage.input_tokens,
            #     output_tokens=response.usage.output_tokens
            # )
            
            # Log thinking
            if hasattr(response, 'thinking'):
                logger.info(f"💭 THOUGHT: {response.thinking}")
            
            # If there are tool calls, execute them
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    logger.info(f"🎬 ACTION: {tool_call.name}({tool_call.args})")
                    
                    # Execute tool
                    # result = await self.tools[tool_call.name].execute(**tool_call.args)
                    result = {"success": True, "data": "Simulated result"}
                    
                    logger.info(f"📤 OBSERVATION: {str(result)[:200]}...")
                    
                    # Add to history
                    self.history.append({
                        "role": "tool",
                        "name": tool_call.name,
                        "result": result
                    })
            else:
                # No tool calls, agent wants to respond
                final_response = response.content if hasattr(response, 'content') else str(response)
                
                self.history.append({
                    "role": "assistant",
                    "content": final_response
                })
                
                logger.info(
                    "agent_run_complete",
                    iterations=self.iteration_count,
                    cost=self.total_cost
                )
                
                return final_response
        
        # Max iterations reached
        logger.warning("agent_max_iterations_reached")
        return "I've reached my maximum number of steps. Here's what I've accomplished so far..."
    
    async def _simulate_response(self, user_input: str, iteration: int) -> Any:
        """Simulate a response for template testing."""
        # This is a placeholder. In real implementation,
        # this would be replaced by actual LLM calls.
        
        class SimulatedResponse:
            thinking = f"Processing iteration {iteration + 1}..."
            content = f"This is a simulated response to: {user_input}"
            tool_calls = [] if iteration > 0 else []  # No tools in simulation
        
        await asyncio.sleep(0.1)  # Simulate API latency
        return SimulatedResponse()
    
    def get_trajectory(self) -> list[dict[str, Any]]:
        """Get the full trajectory of the agent run."""
        return self.history.copy()
    
    def get_cost(self) -> float:
        """Get the total cost of the agent run."""
        return self.total_cost


# Example usage
async def main():
    """Example of how to use the agent."""
    # Load agent from config
    agent = MyAgent.from_config("config.yaml")
    
    # Run agent
    result = await agent.run("What is the weather like today?")
    print(f"Result: {result}")
    
    # Get metrics
    print(f"Iterations: {agent.iteration_count}")
    print(f"Cost: ${agent.get_cost():.4f}")


if __name__ == "__main__":
    asyncio.run(main())
