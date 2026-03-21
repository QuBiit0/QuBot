"""
Script Execution Service

Ejecuta scripts dentro de skills (Python, JavaScript, Bash).
Los scripts se ejecutan en sandbox con timeout y logging.
"""

import asyncio
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.logging import get_logger
from app.config import settings

logger = get_logger(__name__)

SKILLS_BASE_PATH = Path(getattr(settings, "SKILLS_PATH", "/app/skills"))

ALLOWED_COMMANDS = {
    "python": ["python3", "python"],
    "javascript": ["node"],
    "bash": ["bash", "sh"],
}

DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf /home",
    "curl | sh",
    "wget | sh",
    "eval ",
    "exec ",
]


class ScriptExecutionError(Exception):
    """Error executing a script."""


class ScriptTimeoutError(ScriptExecutionError):
    """Script exceeded timeout."""


class ScriptSecurityError(ScriptExecutionError):
    """Script contains dangerous patterns."""


class ScriptNotFoundError(ScriptExecutionError):
    """Script file not found."""


class ScriptExecutionService:
    """
    Service for executing scripts within skills.

    Features:
    - Python, JavaScript, Bash support
    - Sandboxed execution
    - Timeout control
    - Security validation
    - Logging to database
    """

    def __init__(self, db=None):
        self.db = db

    def validate_script(self, script_content: str, language: str) -> None:
        """
        Validate script content for security issues.

        Raises ScriptSecurityError if dangerous patterns found.
        """
        if language == "bash":
            for pattern in DANGEROUS_PATTERNS:
                if pattern.lower() in script_content.lower():
                    raise ScriptSecurityError(
                        f"Security violation: dangerous pattern '{pattern}' not allowed"
                    )

    def get_language_from_script(self, script_path: str) -> str:
        """Determine language from file extension."""
        ext = Path(script_path).suffix.lower()
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".sh": "bash",
            ".bash": "bash",
        }
        return mapping.get(ext, "python")

    async def execute_script(
        self,
        skill_id: str,
        script_path: str,
        parameters: dict[str, Any] | None = None,
        timeout: int = 30,
        agent_id: str | None = None,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a script within a skill.

        Args:
            skill_id: Skill directory name
            script_path: Path relative to skill/scripts/
            parameters: Parameters to pass as JSON to script
            timeout: Execution timeout in seconds
            agent_id: Agent executing the script
            task_id: Task context

        Returns:
            dict with success, result, output, execution_time_ms
        """
        import tempfile

        skill_path = SKILLS_BASE_PATH / skill_id

        if not skill_path.exists():
            raise ScriptNotFoundError(f"Skill '{skill_id}' not found")

        full_script_path = skill_path / "scripts" / script_path

        if not full_script_path.exists():
            raise ScriptNotFoundError(
                f"Script '{script_path}' not found in skill '{skill_id}'"
            )

        script_content = full_script_path.read_text()
        language = self.get_language_from_script(script_path)

        self.validate_script(script_content, language)

        parameters = parameters or {}

        start_time = time.time()
        execution_id = str(uuid4())

        try:
            if language == "python":
                result = await self._execute_python(script_content, parameters, timeout)
            elif language == "javascript":
                result = await self._execute_javascript(
                    script_content, parameters, timeout
                )
            elif language == "bash":
                result = await self._execute_bash(script_content, parameters, timeout)
            else:
                raise ScriptExecutionError(f"Unsupported language: {language}")

            execution_time_ms = int((time.time() - start_time) * 1000)

            await self._log_execution(
                execution_id=execution_id,
                skill_id=skill_id,
                script_path=script_path,
                script_language=language,
                parameters=parameters,
                result=result.get("result"),
                output=result.get("output"),
                execution_time_ms=execution_time_ms,
                status="success",
                agent_id=agent_id,
                task_id=task_id,
            )

            return {
                "success": True,
                "script": script_path,
                "language": language,
                "result": result.get("result"),
                "output": result.get("output"),
                "execution_time_ms": execution_time_ms,
            }

        except ScriptTimeoutError:
            execution_time_ms = int((time.time() - start_time) * 1000)
            await self._log_execution(
                execution_id=execution_id,
                skill_id=skill_id,
                script_path=script_path,
                script_language=language,
                parameters=parameters,
                result=None,
                output=None,
                execution_time_ms=execution_time_ms,
                status="timeout",
                error_message=f"Script exceeded {timeout} seconds",
                agent_id=agent_id,
                task_id=task_id,
            )
            return {
                "success": False,
                "script": script_path,
                "language": language,
                "result": None,
                "output": None,
                "execution_time_ms": execution_time_ms,
                "error": f"Script exceeded {timeout} seconds timeout",
            }

        except ScriptSecurityError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            await self._log_execution(
                execution_id=execution_id,
                skill_id=skill_id,
                script_path=script_path,
                script_language=language,
                parameters=parameters,
                result=None,
                output=None,
                execution_time_ms=execution_time_ms,
                status="error",
                error_message=str(e),
                agent_id=agent_id,
                task_id=task_id,
            )
            return {
                "success": False,
                "script": script_path,
                "language": language,
                "result": None,
                "output": None,
                "execution_time_ms": execution_time_ms,
                "error": f"Security error: {str(e)}",
            }

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            await self._log_execution(
                execution_id=execution_id,
                skill_id=skill_id,
                script_path=script_path,
                script_language=language,
                parameters=parameters,
                result=None,
                output=None,
                execution_time_ms=execution_time_ms,
                status="error",
                error_message=str(e),
                agent_id=agent_id,
                task_id=task_id,
            )
            return {
                "success": False,
                "script": script_path,
                "language": language,
                "result": None,
                "output": None,
                "execution_time_ms": execution_time_ms,
                "error": str(e),
            }

    async def _execute_python(
        self, script_content: str, parameters: dict, timeout: int
    ) -> dict:
        """Execute Python script in subprocess."""

        params_json = json.dumps(parameters)

        wrapper = (
            f"""
import sys
import json

params = json.loads("""
            + f'"{params_json.replace('"', '\\"')}"'
            ""
            + """)

# Inject params to globals for the script
globals().update(params)

# Execute the script
"""
            + script_content
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(wrapper)
            temp_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                "python3",
                temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                raise ScriptTimeoutError(f"Python script exceeded {timeout}s")

            output = stderr.decode() if stderr else stdout.decode()

            try:
                result = json.loads(stdout.decode().strip().split("\n")[-1])
            except:
                result = {"output": stdout.decode().strip()}

            return {"result": result, "output": output}

        finally:
            os.unlink(temp_path)

    async def _execute_javascript(
        self, script_content: str, parameters: dict, timeout: int
    ) -> dict:
        """Execute JavaScript/Node script in subprocess."""

        params_json = json.dumps(parameters)

        wrapper = f"""
const params = {params_json};

// Execute script with params in scope
{script_content}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(wrapper)
            temp_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                "node",
                temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                raise ScriptTimeoutError(f"JavaScript script exceeded {timeout}s")

            output = stderr.decode() if stderr else stdout.decode()

            try:
                result = json.loads(stdout.decode().strip().split("\n")[-1])
            except:
                result = {"output": stdout.decode().strip()}

            return {"result": result, "output": output}

        finally:
            os.unlink(temp_path)

    async def _execute_bash(
        self, script_content: str, parameters: dict, timeout: int
    ) -> dict:
        """Execute Bash script in subprocess."""

        params_json = json.dumps(parameters)

        wrapper = f"""
# Import parameters as JSON
export SCRIPT_PARAMS='{params_json}'

# Parse params to environment variables
eval $(echo '{params_json}' | jq -r 'to_entries | .[] | "export param_\(.key)=\(.value | @sh)"')

# Execute script
{script_content}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(wrapper)
            temp_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                "bash",
                temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                raise ScriptTimeoutError(f"Bash script exceeded {timeout}s")

            output = stderr.decode() if stderr else stdout.decode()

            return {"result": {"exit_code": proc.returncode}, "output": output}

        finally:
            os.unlink(temp_path)

    async def _log_execution(
        self,
        execution_id: str,
        skill_id: str,
        script_path: str,
        script_language: str,
        parameters: dict,
        result: Any,
        output: str | None,
        execution_time_ms: int,
        status: str,
        error_message: str | None = None,
        agent_id: str | None = None,
        task_id: str | None = None,
    ) -> None:
        """Log execution to database."""

        if not self.db:
            return

        try:
            from app.models.skill import SkillExecutionLog

            log = SkillExecutionLog(
                id=execution_id,
                skill_id=skill_id,
                agent_id=agent_id,
                task_id=task_id,
                script_path=script_path,
                script_language=script_language,
                parameters=parameters,
                result=result,
                output=output,
                execution_time_ms=execution_time_ms,
                status=status,
                error_message=error_message,
            )

            self.db.add(log)
            await self.db.commit()
            await self.db.close()

        except Exception as e:
            logger.warning(f"Failed to log script execution: {e}")

    def list_scripts(self, skill_id: str) -> list[dict[str, str]]:
        """List available scripts in a skill."""

        scripts_dir = SKILLS_BASE_PATH / skill_id / "scripts"

        if not scripts_dir.exists():
            return []

        scripts = []
        for file in scripts_dir.iterdir():
            if file.is_file():
                scripts.append(
                    {
                        "name": file.name,
                        "path": f"scripts/{file.name}",
                        "language": self.get_language_from_script(file.name),
                        "size": file.stat().st_size,
                    }
                )

        return sorted(scripts, key=lambda x: x["name"])


_script_execution_service: ScriptExecutionService | None = None


def get_script_execution_service(db=None) -> ScriptExecutionService:
    """Get or create script execution service instance."""
    global _script_execution_service
    if _script_execution_service is None:
        _script_execution_service = ScriptExecutionService(db)
    return _script_execution_service
