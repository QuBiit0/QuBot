import logging
import asyncio
from typing import Any
from uuid import uuid4

from app.core.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class NodesTool(BaseTool):
    name = "nodes"
    description = (
        "Manage remote nodes for distributed task execution (targeting remote Macs)"
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "register",
                    "deregister",
                    "list",
                    "status",
                    "execute",
                    "deploy",
                ],
                "description": "Action to perform",
            },
            "node_id": {
                "type": "string",
                "description": "Node identifier for status/execute actions",
            },
            "node_config": {
                "type": "object",
                "description": "Node configuration for register action",
                "properties": {
                    "name": {"type": "string"},
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                    "ssh_key_path": {"type": "string"},
                    "mac_address": {"type": "string"},
                    "capabilities": {"type": "array", "items": {"type": "string"}},
                },
            },
            "task": {
                "type": "object",
                "description": "Task to execute on node",
                "properties": {
                    "command": {"type": "string"},
                    "working_dir": {"type": "string"},
                    "timeout": {"type": "integer"},
                },
            },
        },
        "required": ["action"],
    }

    def __init__(self, config: dict = None):
        super().__init__(config)
        self._nodes: dict[str, dict] = {}
        self._node_connections: dict[str, Any] = {}

    async def execute(
        self,
        action: str,
        node_id: str = None,
        node_config: dict = None,
        task: dict = None,
        **kwargs,
    ) -> ToolResult:
        try:
            if action == "register":
                return await self._register_node(node_config)
            elif action == "deregister":
                return await self._deregister_node(node_id)
            elif action == "list":
                return await self._list_nodes()
            elif action == "status":
                return await self._get_node_status(node_id)
            elif action == "execute":
                return await self._execute_on_node(node_id, task)
            elif action == "deploy":
                return await self._deploy_to_node(node_id, task)
            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Nodes tool error: {e}")
            return ToolResult(success=False, error=str(e))

    async def _register_node(self, config: dict) -> ToolResult:
        node_id = config.get("name") or f"node_{uuid4().hex[:8]}"
        self._nodes[node_id] = {
            "id": node_id,
            "name": config.get("name"),
            "host": config.get("host"),
            "port": config.get("port", 22),
            "ssh_key_path": config.get("ssh_key_path"),
            "mac_address": config.get("mac_address"),
            "capabilities": config.get("capabilities", ["general"]),
            "status": "pending",
            "last_seen": None,
        }
        logger.info(f"Node registered: {node_id}")
        return ToolResult(
            success=True,
            result={"node_id": node_id, "status": "registered"},
            metadata={"node": self._nodes[node_id]},
        )

    async def _deregister_node(self, node_id: str) -> ToolResult:
        if node_id not in self._nodes:
            return ToolResult(success=False, error=f"Node not found: {node_id}")
        del self._nodes[node_id]
        if node_id in self._node_connections:
            del self._node_connections[node_id]
        return ToolResult(
            success=True, result={"node_id": node_id, "status": "deregistered"}
        )

    async def _list_nodes(self) -> ToolResult:
        return ToolResult(
            success=True,
            result={"nodes": list(self._nodes.values()), "count": len(self._nodes)},
        )

    async def _get_node_status(self, node_id: str) -> ToolResult:
        if node_id not in self._nodes:
            return ToolResult(success=False, error=f"Node not found: {node_id}")
        return ToolResult(success=True, result=self._nodes[node_id])

    async def _execute_on_node(self, node_id: str, task: dict) -> ToolResult:
        if node_id not in self._nodes:
            return ToolResult(success=False, error=f"Node not found: {node_id}")

        node = self._nodes[node_id]
        command = task.get("command", "")
        working_dir = task.get("working_dir", "/tmp")
        timeout = task.get("timeout", 300)

        logger.info(f"Executing on node {node_id}: {command}")

        return ToolResult(
            success=True,
            result={
                "node_id": node_id,
                "command": command,
                "output": f"Simulated execution on {node['host']}",
                "exit_code": 0,
            },
            metadata={"working_dir": working_dir, "timeout": timeout},
        )

    async def _deploy_to_node(self, node_id: str, task: dict) -> ToolResult:
        if node_id not in self._nodes:
            return ToolResult(success=False, error=f"Node not found: {node_id}")

        node = self._nodes[node_id]
        return ToolResult(
            success=True,
            result={
                "node_id": node_id,
                "status": "deployed",
                "host": node["host"],
                "message": f"Deployment simulated to {node['name'] or node_id}",
            },
        )
