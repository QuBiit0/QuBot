"""
Skill Execution Service

Safely executes user-defined skills in a sandboxed environment.
Inspired by OpenClaw but with enhanced security.
"""

import asyncio
import json
import re
import sys
import time
import traceback
from io import StringIO
from typing import Any, Dict, Optional
from contextlib import redirect_stdout, redirect_stderr

import aiohttp
from sqlalchemy.orm import Session

from app.models.skill import Skill, SkillExecutionLog, SkillLanguage
from app.core.logging import get_logger
from app.config import settings

logger = get_logger(__name__)


class SkillExecutionError(Exception):
    """Custom exception for skill execution errors."""
    pass


class SkillTimeoutError(SkillExecutionError):
    """Raised when skill execution exceeds timeout."""
    pass


class SkillSecurityError(SkillExecutionError):
    """Raised when skill code violates security policies."""
    pass


class SkillExecutionService:
    """
    Service for executing skills safely.
    
    Security features:
    - Code validation (no imports de sistema peligrosos)
    - Timeout enforcement
    - Memory limits (via ulimit en container)
    - No network access (opcional)
    - Output capture
    """
    
    # Palabras clave prohibidas en código Python
    PYTHON_BLACKLIST = [
        '__import__',
        'eval(',
        'exec(',
        'compile(',
        'open(',
        'file(',
        'os.system',
        'os.popen',
        'subprocess',
        'sys.exit',
        'quit(',
        'exit(',
        'import os',
        'import sys',
        'import subprocess',
        'import socket',
    ]
    
    # Imports permitidos (whitelist approach)
    PYTHON_ALLOWED_IMPORTS = [
        'json',
        're',
        'math',
        'random',
        'datetime',
        'time',
        'collections',
        'itertools',
        'functools',
        'typing',
        'urllib.parse',
        'hashlib',
        'base64',
        'string',
        'statistics',
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_code(self, code: str, language: SkillLanguage) -> None:
        """
        Validates skill code for security issues.
        
        Raises SkillSecurityError if code violates policies.
        """
        if language == SkillLanguage.PYTHON:
            self._validate_python_code(code)
        elif language == SkillLanguage.JAVASCRIPT:
            self._validate_javascript_code(code)
    
    def _validate_python_code(self, code: str) -> None:
        """Validate Python code security."""
        # Check for blacklisted patterns
        code_lower = code.lower()
        
        for pattern in self.PYTHON_BLACKLIST:
            if pattern.lower() in code_lower:
                raise SkillSecurityError(
                    f"Security violation: '{pattern}' is not allowed in skill code"
                )
        
        # Check for dangerous builtins
        dangerous_builtins = ['eval', 'exec', '__import__', 'compile']
        for builtin in dangerous_builtins:
            if builtin in code:
                raise SkillSecurityError(
                    f"Security violation: '{builtin}' builtin is not allowed"
                )
        
        # Check imports (basic check)
        import_pattern = r'^import\s+(\w+)|^from\s+(\w+)\s+import'
        for line in code.split('\n'):
            match = re.match(import_pattern, line.strip())
            if match:
                module = match.group(1) or match.group(2)
                base_module = module.split('.')[0]
                
                if base_module not in self.PYTHON_ALLOWED_IMPORTS:
                    raise SkillSecurityError(
                        f"Security violation: import '{module}' is not allowed. "
                        f"Allowed modules: {', '.join(self.PYTHON_ALLOWED_IMPORTS)}"
                    )
    
    def _validate_javascript_code(self, code: str) -> None:
        """Validate JavaScript code security."""
        # Basic JS validation
        js_blacklist = [
            'eval(',
            'Function(',
            'require(',
            'process.',
            'child_process',
            'fs.',
            'fs[',
            'require("fs")',
            "require('fs')",
        ]
        
        code_lower = code.lower()
        for pattern in js_blacklist:
            if pattern in code_lower:
                raise SkillSecurityError(
                    f"Security violation: '{pattern}' is not allowed in JS skill code"
                )
    
    async def execute_skill(
        self,
        skill: Skill,
        parameters: Dict[str, Any],
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a skill with given parameters.
        
        Returns:
            Dict with keys: success, result, error, execution_time_ms
        """
        start_time = time.time()
        
        try:
            # Validate code before execution
            self.validate_code(skill.code, skill.language)
            
            # Execute based on language
            if skill.language == SkillLanguage.PYTHON:
                result = await self._execute_python(skill.code, parameters, timeout)
            elif skill.language == SkillLanguage.JAVASCRIPT:
                result = await self._execute_javascript(skill.code, parameters, timeout)
            else:
                raise SkillExecutionError(f"Unsupported language: {skill.language}")
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Log successful execution
            self._log_execution(
                skill_id=skill.id,
                agent_id=agent_id,
                task_id=task_id,
                parameters=parameters,
                result=result,
                status="success",
                execution_time_ms=execution_time
            )
            
            return {
                "success": True,
                "result": result,
                "error": None,
                "execution_time_ms": execution_time
            }
            
        except asyncio.TimeoutError:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = f"Skill execution timed out after {timeout} seconds"
            
            self._log_execution(
                skill_id=skill.id,
                agent_id=agent_id,
                task_id=task_id,
                parameters=parameters,
                error_message=error_msg,
                status="timeout",
                execution_time_ms=execution_time
            )
            
            return {
                "success": False,
                "result": None,
                "error": error_msg,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            self._log_execution(
                skill_id=skill.id,
                agent_id=agent_id,
                task_id=task_id,
                parameters=parameters,
                error_message=error_msg,
                status="error",
                execution_time_ms=execution_time
            )
            
            return {
                "success": False,
                "result": None,
                "error": error_msg,
                "execution_time_ms": execution_time
            }
    
    async def _execute_python(
        self, 
        code: str, 
        parameters: Dict[str, Any],
        timeout: int
    ) -> Any:
        """Execute Python code safely."""
        
        # Create isolated namespace
        namespace = {
            '__builtins__': {
                'True': True,
                'False': False,
                'None': None,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'print': lambda *args: None,  # Disable print
                'Exception': Exception,
                'TypeError': TypeError,
                'ValueError': ValueError,
                'KeyError': KeyError,
                'IndexError': IndexError,
            },
            'params': parameters,
            'result': None
        }
        
        # Add allowed imports to namespace
        import json
        import re as regex
        import math
        import random
        from datetime import datetime, timedelta
        
        namespace['json'] = json
        namespace['re'] = regex
        namespace['math'] = math
        namespace['random'] = random
        namespace['datetime'] = datetime
        namespace['timedelta'] = timedelta
        
        # Wrap code to capture result
        wrapped_code = f"""
{code}

# If there's a main function, call it
if 'main' in dir():
    if callable(main):
        result = main(params)
    else:
        result = main
else:
    # Otherwise, result is whatever was last assigned
    pass
"""
        
        # Execute in thread pool to not block
        loop = asyncio.get_event_loop()
        
        def run_code():
            exec(wrapped_code, namespace)
            return namespace.get('result')
        
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, run_code),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            raise SkillTimeoutError(f"Execution exceeded {timeout} seconds")
    
    async def _execute_javascript(
        self, 
        code: str, 
        parameters: Dict[str, Any],
        timeout: int
    ) -> Any:
        """Execute JavaScript code using Node.js."""
        import subprocess
        import tempfile
        import os
        
        # Wrap code to get result
        wrapped_code = f"""
const params = {json.dumps(parameters)};

{code}

// If main is defined, call it
if (typeof main === 'function') {{
    const result = main(params);
    console.log('__RESULT__:' + JSON.stringify(result));
}} else {{
    console.log('__RESULT__:null');
}}
"""
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(wrapped_code)
            temp_file = f.name
        
        try:
            # Execute with timeout
            proc = await asyncio.create_subprocess_exec(
                'node', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024*1024  # 1MB output limit
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            
            if proc.returncode != 0:
                raise SkillExecutionError(f"JS Error: {stderr.decode()}")
            
            # Parse result
            output = stdout.decode()
            for line in output.split('\n'):
                if line.startswith('__RESULT__:'):
                    result_json = line.replace('__RESULT__:', '')
                    return json.loads(result_json)
            
            return None
            
        except asyncio.TimeoutError:
            proc.kill()
            raise SkillTimeoutError(f"Execution exceeded {timeout} seconds")
        finally:
            os.unlink(temp_file)
    
    def _log_execution(
        self,
        skill_id: str,
        agent_id: Optional[str],
        task_id: Optional[str],
        parameters: Dict[str, Any],
        result: Any = None,
        error_message: Optional[str] = None,
        status: str = "success",
        execution_time_ms: int = 0
    ) -> None:
        """Log skill execution to database."""
        try:
            from app.utils.id_generator import generate_id
            
            log = SkillExecutionLog(
                id=generate_id(),
                skill_id=skill_id,
                agent_id=agent_id,
                task_id=task_id,
                parameters=parameters,
                result=result if status == "success" else None,
                error_message=error_message,
                execution_time_ms=execution_time_ms,
                status=status
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log skill execution: {e}")
            self.db.rollback()


# Global service instance
_skill_execution_service: Optional[SkillExecutionService] = None


def get_skill_execution_service(db: Session) -> SkillExecutionService:
    """Get or create skill execution service instance."""
    return SkillExecutionService(db)
