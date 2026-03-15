"""
System Shell Tool - Execute shell commands with safety restrictions
"""
import asyncio
import re
import time
from typing import Any, Dict, Optional, List
import shlex

from .base import BaseTool, ToolResult, ToolParameter, ToolCategory, ToolRiskLevel


class SystemShellTool(BaseTool):
    """
    Tool for executing shell commands with safety restrictions.
    
    IMPORTANT: This tool is DANGEROUS and should only be enabled
    for trusted agents with strict command whitelisting.
    """
    
    name = "system_shell"
    description = (
        "Execute shell commands on the system. "
        "Use for running scripts, file operations, git commands, etc. "
        "Commands are filtered through a whitelist for safety."
    )
    category = ToolCategory.SYSTEM
    risk_level = ToolRiskLevel.DANGEROUS
    
    # Default allowed commands (conservative)
    DEFAULT_ALLOWED_COMMANDS = [
        # File operations
        "ls", "cat", "head", "tail", "wc", "find", "grep",
        # Git
        "git", "git status", "git log", "git diff", "git show",
        # Python
        "python", "python3", "pip", "pip3",
        # Node
        "node", "npm", "npx",
        # Build tools
        "make", "cmake",
        # System info
        "echo", "pwd", "which", "uname", "df", "du",
        # Text processing
        "awk", "sed", "cut", "sort", "uniq",
        # Compression
        "tar", "gzip", "gunzip", "zip", "unzip",
        # Docker (read-only)
        "docker ps", "docker images", "docker logs",
    ]
    
    # Dangerous patterns to block (regex)
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",
        r">\s*/dev/",
        r"mkfs",
        r"dd\s+if=",
        r":\(\)\s*\{",
        r"curl.*\|\s*sh",
        r"wget.*\|\s*sh",
        r"eval\s*\$",
        r"bash\s+-c",
    ]
    
    # Default timeout
    DEFAULT_TIMEOUT = 30
    MAX_TIMEOUT = 300  # 5 minutes
    
    # Max output size (1MB)
    MAX_OUTPUT_SIZE = 1024 * 1024
    
    def _get_parameters_schema(self) -> Dict[str, ToolParameter]:
        return {
            "command": ToolParameter(
                name="command",
                type="string",
                description="Shell command to execute. Must be in the allowed commands list.",
                required=True,
            ),
            "cwd": ToolParameter(
                name="cwd",
                type="string",
                description="Working directory for command execution",
                required=False,
            ),
            "timeout": ToolParameter(
                name="timeout",
                type="integer",
                description=f"Command timeout in seconds (max {self.MAX_TIMEOUT})",
                required=False,
                default=self.DEFAULT_TIMEOUT,
            ),
            "env_vars": ToolParameter(
                name="env_vars",
                type="object",
                description="Environment variables as key-value pairs",
                required=False,
                default={},
            ),
        }
    
    def _validate_config(self) -> None:
        """Validate tool configuration"""
        # Allowed commands (whitelist)
        self.allowed_commands = self.config.get(
            "allowed_commands",
            self.DEFAULT_ALLOWED_COMMANDS,
        )
        
        # Convert to set for faster lookup
        self._allowed_set = set(cmd.split()[0] for cmd in self.allowed_commands)
        
        # Blocked patterns
        self.blocked_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.get("blocked_patterns", self.DANGEROUS_PATTERNS)
        ]
        
        # Working directory restriction
        self.allowed_cwd = self.config.get("allowed_cwd")
        
        # Environment variable whitelist
        self.allowed_env_vars = self.config.get("allowed_env_vars", [])
    
    def _validate_command(self, command: str) -> tuple[bool, Optional[str]]:
        """
        Validate command against security rules.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if pattern.search(command):
                return False, f"Command contains blocked pattern: {pattern.pattern}"
        
        # Extract base command
        try:
            # Handle complex commands with pipes, etc.
            parts = shlex.split(command)
            if not parts:
                return False, "Empty command"
            base_cmd = parts[0]
        except ValueError as e:
            return False, f"Invalid command syntax: {str(e)}"
        
        # Check if base command is allowed
        if base_cmd not in self._allowed_set:
            return False, f"Command '{base_cmd}' not in allowed list"
        
        # Check full command prefix matches allowed patterns
        command_prefix = " ".join(parts[:2]) if len(parts) > 1 else parts[0]
        allowed_full = [cmd for cmd in self.allowed_commands if command.startswith(cmd)]
        
        # If no exact match, check if base command is allowed
        if not allowed_full and base_cmd not in self._allowed_set:
            return False, f"Command not in allowed list"
        
        return True, None
    
    def _validate_cwd(self, cwd: Optional[str]) -> tuple[bool, Optional[str]]:
        """Validate working directory"""
        if cwd is None:
            return True, None
        
        if self.allowed_cwd:
            import os
            # Ensure cwd is within allowed directory
            real_cwd = os.path.realpath(cwd)
            real_allowed = os.path.realpath(self.allowed_cwd)
            if not real_cwd.startswith(real_allowed):
                return False, f"Working directory must be within {self.allowed_cwd}"
        
        return True, None
    
    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> ToolResult:
        """
        Execute shell command.
        
        Args:
            command: Shell command to execute
            cwd: Working directory
            timeout: Command timeout
            env_vars: Additional environment variables
            
        Returns:
            ToolResult with command output
        """
        start_time = time.time()
        
        # Validate command
        is_valid, error = self._validate_command(command)
        if not is_valid:
            return ToolResult(
                success=False,
                error=f"Security violation: {error}",
            )
        
        # Validate cwd
        is_valid, error = self._validate_cwd(cwd)
        if not is_valid:
            return ToolResult(
                success=False,
                error=f"Invalid working directory: {error}",
            )
        
        # Cap timeout
        timeout = min(timeout, self.MAX_TIMEOUT)
        
        # Prepare environment
        import os
        env = os.environ.copy()
        if env_vars:
            # Filter to allowed env vars if specified
            if self.allowed_env_vars:
                env_vars = {k: v for k, v in env_vars.items() if k in self.allowed_env_vars}
            env.update(env_vars)
        
        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    error=f"Command timed out after {timeout} seconds",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            # Truncate if too large
            if len(stdout_str) > self.MAX_OUTPUT_SIZE:
                stdout_str = stdout_str[:self.MAX_OUTPUT_SIZE] + "\n... [truncated]"
            if len(stderr_str) > self.MAX_OUTPUT_SIZE:
                stderr_str = stderr_str[:self.MAX_OUTPUT_SIZE] + "\n... [truncated]"
            
            return ToolResult(
                success=process.returncode == 0,
                data={
                    "returncode": process.returncode,
                    "command": command,
                },
                stdout=stdout_str,
                stderr=stderr_str,
                execution_time_ms=execution_time,
                metadata={
                    "returncode": process.returncode,
                    "cwd": cwd,
                    "timeout": timeout,
                },
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to execute command: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
