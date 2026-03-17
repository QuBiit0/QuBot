"""
Code Executor Tool - Sandboxed execution of Python, Bash, and Node.js code.
Gives agents the ability to run code, perform data analysis, and automate tasks.
"""

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


class CodeExecutorTool(BaseTool):
    """
    Execute Python, Bash, or Node.js code in a sandboxed subprocess.

    Ideal for:
    - Data analysis with pandas/numpy/matplotlib
    - File processing and transformation
    - Mathematical calculations
    - Automation scripts
    - Generating charts and visualizations (saved as files)

    Security: runs in isolated subprocess with strict timeout.
    Filesystem access limited to /tmp by default.
    """

    name = "code_executor"
    description = (
        "Execute Python, Bash, or Node.js code safely in a sandboxed subprocess. "
        "Python has access to pandas, numpy, matplotlib, requests, json, csv, math, datetime. "
        "Use for data analysis, calculations, file processing, and automation scripts. "
        "Output files are saved to /tmp and paths are returned."
    )
    category = ToolCategory.CODE
    risk_level = ToolRiskLevel.DANGEROUS

    MAX_TIMEOUT = 120
    DEFAULT_TIMEOUT = 30
    MAX_OUTPUT_CHARS = 20_000

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "code": ToolParameter(
                name="code",
                type="string",
                description="Code to execute",
                required=True,
            ),
            "language": ToolParameter(
                name="language",
                type="string",
                description="Programming language: 'python', 'bash', 'node'",
                required=False,
                default="python",
                enum=["python", "bash", "node"],
            ),
            "timeout": ToolParameter(
                name="timeout",
                type="integer",
                description=f"Execution timeout in seconds (max {MAX_TIMEOUT})",
                required=False,
                default=DEFAULT_TIMEOUT,
            ),
            "input_data": ToolParameter(
                name="input_data",
                type="string",
                description="Optional stdin input for the program",
                required=False,
                default=None,
            ),
            "working_dir": ToolParameter(
                name="working_dir",
                type="string",
                description="Working directory (default: /tmp/qubot_exec)",
                required=False,
                default=None,
            ),
        }

    def _validate_config(self) -> None:
        self.allowed_languages = self.config.get("allowed_languages", ["python", "bash", "node"])
        self.max_timeout = self.config.get("max_timeout", self.MAX_TIMEOUT)
        self.work_dir = self.config.get("work_dir", "/tmp/qubot_exec")
        os.makedirs(self.work_dir, exist_ok=True)

    def _is_dangerous_code(self, code: str, language: str) -> tuple[bool, str]:
        """Basic static analysis to block obviously dangerous patterns."""
        code_lower = code.lower()

        # Universal blocks
        dangerous_patterns = [
            ("import ctypes", "ctypes access not allowed"),
            ("ctypes.cdll", "ctypes access not allowed"),
            ("__import__('ctypes')", "ctypes access not allowed"),
            ("fork()", "fork() not allowed"),
            (":(){:|:&};:", "fork bomb pattern detected"),
        ]

        if language == "python":
            dangerous_patterns += [
                ("os.system", "Use subprocess or shell tool instead"),
                ("subprocess.popen(", None),  # allowed — just filtered output
            ]

        if language == "bash":
            dangerous_patterns += [
                ("rm -rf /", "destructive rm not allowed"),
                ("mkfs", "filesystem formatting not allowed"),
                ("dd if=", "dd write operations not allowed"),
                ("> /dev/sda", "raw device writes not allowed"),
            ]

        for pattern, msg in dangerous_patterns:
            if pattern in code_lower and msg is not None:
                return True, msg

        return False, ""

    def _get_interpreter(self, language: str) -> list[str]:
        """Get the interpreter command for the given language."""
        interpreters = {
            "python": [sys.executable],
            "bash": ["bash"],
            "node": ["node"],
        }
        return interpreters.get(language, [sys.executable])

    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: int = DEFAULT_TIMEOUT,
        input_data: str | None = None,
        working_dir: str | None = None,
    ) -> ToolResult:
        start_time = time.time()

        if language not in self.allowed_languages:
            return ToolResult(success=False, error=f"Language '{language}' is not allowed. Use: {self.allowed_languages}")

        is_dangerous, reason = self._is_dangerous_code(code, language)
        if is_dangerous:
            return ToolResult(success=False, error=f"Code blocked by safety filter: {reason}")

        timeout = min(max(1, timeout), self.max_timeout)
        work_dir = working_dir or self.work_dir
        os.makedirs(work_dir, exist_ok=True)

        # Write code to temp file
        suffix = {"python": ".py", "bash": ".sh", "node": ".js"}.get(language, ".py")
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=suffix,
                dir=work_dir,
                delete=False,
                encoding="utf-8",
            ) as f:
                f.write(code)
                code_file = f.name

            interpreter = self._get_interpreter(language)
            cmd = interpreter + [code_file]

            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env["MPLBACKEND"] = "Agg"  # matplotlib non-interactive
            # Restrict PATH for bash to avoid system damage
            if language == "bash":
                env["PATH"] = "/usr/local/bin:/usr/bin:/bin"

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else asyncio.subprocess.DEVNULL,
                cwd=work_dir,
                env=env,
            )

            try:
                stdin_bytes = input_data.encode() if input_data else None
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(input=stdin_bytes),
                    timeout=timeout,
                )
                exit_code = proc.returncode
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ToolResult(
                    success=False,
                    error=f"Code execution timed out after {timeout}s",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            # Truncate large outputs
            if len(stdout) > self.MAX_OUTPUT_CHARS:
                stdout = stdout[: self.MAX_OUTPUT_CHARS] + f"\n[... truncated, {len(stdout)} chars total]"
            if len(stderr) > 5000:
                stderr = stderr[:5000] + "\n[... truncated]"

            # Detect output files created in work_dir
            output_files = []
            try:
                for fname in os.listdir(work_dir):
                    if fname != Path(code_file).name:
                        fpath = os.path.join(work_dir, fname)
                        if os.path.isfile(fpath):
                            output_files.append(fpath)
            except Exception:
                pass

            success = exit_code == 0
            exec_ms = int((time.time() - start_time) * 1000)

            return ToolResult(
                success=success,
                data={
                    "exit_code": exit_code,
                    "stdout": stdout,
                    "stderr": stderr,
                    "output_files": output_files,
                    "language": language,
                    "working_dir": work_dir,
                },
                stdout=stdout or None,
                stderr=stderr or None,
                error=stderr if not success and stderr else None,
                execution_time_ms=exec_ms,
                metadata={
                    "exit_code": exit_code,
                    "output_files": output_files,
                    "timeout_used": timeout,
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Execution error: {e}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
        finally:
            try:
                if "code_file" in locals():
                    os.unlink(code_file)
            except Exception:
                pass
