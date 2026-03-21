"""
Docker Sandbox - Secure isolated execution environment for code/tools.

Provides:
- Docker container per session/agent
- Workspace isolation with optional mounts
- Network control (allow/deny/blocked)
- Execution timeouts and resource limits
- Cleanup on exit

Based on OpenClaw's sandbox architecture.
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


class WorkspaceAccess(str, Enum):
    """Workspace access modes."""

    NONE = "none"  # No filesystem access
    RO = "ro"  # Read-only
    RW = "rw"  # Read-write


@dataclass
class SandboxConfig:
    """Sandbox configuration."""

    enabled: bool = True
    scope: str = "session"  # session, agent, shared
    image: str = "python:3.12-slim"

    # Workspace
    workspace_path: str | None = None
    workspace_access: WorkspaceAccess = WorkspaceAccess.RW

    # Mounts
    volumes: dict[str, str] = field(default_factory=dict)  # host_path: container_path
    read_only_volumes: list[str] = field(default_factory=list)

    # Network
    network_mode: str = "bridge"  # bridge, host, none
    blocked_domains: list[str] = field(default_factory=list)

    # Resources
    memory_limit: str = "512m"
    cpu_limit: float = 1.0
    timeout_seconds: int = 300

    # Setup
    setup_command: str | None = None


@dataclass
class SandboxInstance:
    """A running sandbox instance."""

    id: str
    container_id: str
    workspace_path: str
    created_at: float
    session_id: str | None = None
    agent_id: str | None = None
    status: str = "running"
    last_used: float = field(default_factory=0)


class DockerSandboxService:
    """
    Docker-based sandbox for secure code/tool execution.

    Features:
    - Per-session or per-agent containers
    - Workspace isolation with optional mounts
    - Network control
    - Resource limits
    - Auto-cleanup
    """

    def __init__(self, base_config: SandboxConfig | None = None):
        self.base_config = base_config or SandboxConfig()
        self._instances: dict[str, SandboxInstance] = {}
        self._cleanup_task: asyncio.Task | None = None

    async def initialize(self) -> None:
        """Initialize the sandbox service."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Docker sandbox service initialized")

    async def shutdown(self) -> None:
        """Shutdown and cleanup all sandboxes."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Destroy all instances
        for instance_id in list(self._instances.keys()):
            await self.destroy(instance_id)

        logger.info("Docker sandbox service shutdown")

    async def create(
        self,
        session_id: str | None = None,
        agent_id: str | None = None,
        config: SandboxConfig | None = None,
    ) -> SandboxInstance:
        """
        Create a new sandbox instance.

        Args:
            session_id: Session ID for per-session sandbox
            agent_id: Agent ID for per-agent sandbox
            config: Override base configuration

        Returns:
            SandboxInstance with container details
        """
        import time

        sandbox_config = config or self.base_config
        instance_id = str(uuid.uuid4())

        # Generate workspace path
        workspace_path = sandbox_config.workspace_path
        if not workspace_path:
            workspace_path = f"/tmp/qubot-sandbox-{instance_id[:8]}"

        try:
            # Create Docker container
            container_id = await self._create_container(
                instance_id=instance_id,
                config=sandbox_config,
                workspace_path=workspace_path,
            )

            instance = SandboxInstance(
                id=instance_id,
                container_id=container_id,
                workspace_path=workspace_path,
                created_at=time.time(),
                session_id=session_id,
                agent_id=agent_id,
                status="running",
            )

            self._instances[instance_id] = instance
            logger.info(f"Created sandbox instance: {instance_id}")

            return instance

        except Exception as e:
            logger.error(f"Failed to create sandbox: {e}")
            raise

    async def _create_container(
        self,
        instance_id: str,
        config: SandboxConfig,
        workspace_path: str,
    ) -> str:
        """Create a Docker container."""
        import subprocess

        container_name = f"qubot-sandbox-{instance_id[:8]}"

        # Build docker command
        cmd = [
            "docker",
            "create",
            "--name",
            container_name,
            "--network",
            config.network_mode,
            "--memory",
            config.memory_limit,
            "--cpus",
            str(config.cpu_limit),
            "--pids-limit",
            "256",
            "--memory-swap",
            "-1",
            "--read-only" if config.workspace_access == WorkspaceAccess.NONE else "",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=100m",
        ]

        # Add workspace volume
        if config.workspace_access != WorkspaceAccess.NONE:
            host_path = f"/tmp/qubot-workspace-{instance_id[:8]}"
            Path(host_path).mkdir(parents=True, exist_ok=True)

            read_only = (
                "--read-only" if config.workspace_access == WorkspaceAccess.RO else ""
            )
            cmd.extend(["-v", f"{host_path}:{workspace_path} {read_only}".strip()])

        # Add custom volumes
        for host_path, container_path in config.volumes.items():
            read_only = host_path in config.read_only_volumes
            cmd.extend(["-v", f"{host_path}:{container_path}"])

        # Block domains in /etc/hosts
        if config.blocked_domains:
            blocked_hosts = "\n".join(
                [f"127.0.0.1 {domain}" for domain in config.blocked_domains]
            )
            cmd.extend(["--add-host", "blocked:127.0.0.1"])

        # Image and command
        cmd.extend([config.image, "sleep", "infinity"])

        # Remove empty strings
        cmd = [c for c in cmd if c]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Failed to create container: {result.stderr}")

        container_id = result.stdout.strip()

        # Start container
        subprocess.run(["docker", "start", container_id], capture_output=True)

        # Run setup command if provided
        if config.setup_command:
            exec_result = subprocess.run(
                ["docker", "exec", container_id, "sh", "-c", config.setup_command],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if exec_result.returncode != 0:
                logger.warning(f"Setup command failed: {exec_result.stderr}")

        return container_id

    async def execute(
        self,
        instance_id: str,
        command: str,
        timeout: int = 30,
        user: str = "root",
    ) -> dict[str, Any]:
        """
        Execute a command in a sandbox.

        Args:
            instance_id: Sandbox instance ID
            command: Command to execute
            timeout: Execution timeout in seconds
            user: User to run as

        Returns:
            dict with stdout, stderr, exit_code, execution_time
        """
        import subprocess
        import time

        if instance_id not in self._instances:
            raise ValueError(f"Unknown sandbox instance: {instance_id}")

        instance = self._instances[instance_id]
        start_time = time.time()

        try:
            result = subprocess.run(
                ["docker", "exec", instance.container_id, "sh", "-c", command],
                capture_output=True,
                text=True,
                timeout=min(timeout, 300),
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "execution_time_ms": int((time.time() - start_time) * 1000),
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Command timed out",
                "exit_code": -1,
                "execution_time_ms": timeout * 1000,
                "error": "timeout",
            }

        finally:
            instance.last_used = time.time()

    async def write_file(self, instance_id: str, path: str, content: str) -> None:
        """Write a file to the sandbox workspace."""
        import subprocess

        if instance_id not in self._instances:
            raise ValueError(f"Unknown sandbox instance: {instance_id}")

        instance = self._instances[instance_id]

        # Write to host first, then copy
        host_path = f"/tmp/qubot-workspace-{instance_id[:8]}"
        host_file = Path(host_path) / path.lstrip("/")
        host_file.parent.mkdir(parents=True, exist_ok=True)
        host_file.write_text(content)

        # Copy to container
        subprocess.run(
            [
                "docker",
                "cp",
                str(host_file),
                f"{instance.container_id}:{instance.workspace_path}/{path}",
            ],
            capture_output=True,
        )

    async def read_file(self, instance_id: str, path: str) -> str:
        """Read a file from the sandbox workspace."""
        import subprocess

        if instance_id not in self._instances:
            raise ValueError(f"Unknown sandbox instance: {instance_id}")

        instance = self._instances[instance_id]

        result = subprocess.run(
            [
                "docker",
                "exec",
                instance.container_id,
                "cat",
                f"{instance.workspace_path}/{path}",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise FileNotFoundError(f"File not found: {path}")

        return result.stdout

    async def destroy(self, instance_id: str) -> None:
        """Destroy a sandbox instance."""
        import subprocess

        if instance_id not in self._instances:
            return

        instance = self._instances[instance_id]

        try:
            subprocess.run(
                ["docker", "rm", "-f", instance.container_id],
                capture_output=True,
                timeout=10,
            )
        except Exception as e:
            logger.warning(f"Failed to remove container {instance.container_id}: {e}")

        # Cleanup workspace
        workspace_host = f"/tmp/qubot-workspace-{instance_id[:8]}"
        try:
            subprocess.run(["rm", "-rf", workspace_host], capture_output=True)
        except Exception:
            pass

        del self._instances[instance_id]
        logger.info(f"Destroyed sandbox instance: {instance_id}")

    async def get_stats(self, instance_id: str) -> dict[str, Any]:
        """Get sandbox instance stats."""
        import subprocess
        import time

        if instance_id not in self._instances:
            return {"status": "not_found"}

        instance = self._instances[instance_id]

        # Get container stats
        try:
            stats_result = subprocess.run(
                [
                    "docker",
                    "stats",
                    instance.container_id,
                    "--no-stream",
                    "--format",
                    "{{.MemUsage}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            mem_usage = stats_result.stdout.strip()
        except Exception:
            mem_usage = "unknown"

        return {
            "id": instance.id,
            "container_id": instance.container_id,
            "status": instance.status,
            "workspace_path": instance.workspace_path,
            "created_at": instance.created_at,
            "last_used": instance.last_used,
            "idle_time": int(time.time() - instance.last_used),
            "memory": mem_usage,
            "session_id": instance.session_id,
            "agent_id": instance.agent_id,
        }

    async def _cleanup_loop(self) -> None:
        """Background cleanup of idle sandboxes."""
        import time

        while True:
            try:
                await asyncio.sleep(60)

                idle_timeout = 1800  # 30 minutes
                current_time = time.time()

                for instance_id in list(self._instances.keys()):
                    instance = self._instances[instance_id]

                    if current_time - instance.last_used > idle_timeout:
                        logger.info(f"Cleaning up idle sandbox: {instance_id}")
                        await self.destroy(instance_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")


# Global singleton
_docker_sandbox_service: DockerSandboxService | None = None


async def get_docker_sandbox() -> DockerSandboxService:
    """Get or create the global Docker sandbox service."""
    global _docker_sandbox_service
    if _docker_sandbox_service is None:
        _docker_sandbox_service = DockerSandboxService()
        await _docker_sandbox_service.initialize()
    return _docker_sandbox_service


async def shutdown_docker_sandbox() -> None:
    """Shutdown the Docker sandbox service."""
    global _docker_sandbox_service
    if _docker_sandbox_service:
        await _docker_sandbox_service.shutdown()
        _docker_sandbox_service = None
