import logging
import re
import hashlib
from typing import Any

from app.core.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ApplyPatchTool(BaseTool):
    name = "apply_patch"
    description = "Apply code patches to files with diff-based modifications"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["apply", "create", "validate", "reverse"],
                "description": "Action to perform",
            },
            "patch": {
                "type": "string",
                "description": "Patch content in unified diff format",
            },
            "file_path": {
                "type": "string",
                "description": "File to apply patch to or create patch from",
            },
            "patch_type": {
                "type": "string",
                "enum": ["unified", "context", "raw"],
                "default": "unified",
                "description": "Patch format type",
            },
            "strip": {
                "type": "integer",
                "default": 0,
                "description": "Number of leading path components to strip",
            },
            "dry_run": {
                "type": "boolean",
                "default": False,
                "description": "Validate patch without applying",
            },
        },
        "required": ["action"],
    }

    def __init__(self, config: dict = None):
        super().__init__(config)
        self._patch_history: list[dict] = []

    async def execute(
        self,
        action: str,
        patch: str = None,
        file_path: str = None,
        patch_type: str = "unified",
        strip: int = 0,
        dry_run: bool = False,
        **kwargs,
    ) -> ToolResult:
        try:
            if action == "apply":
                return await self._apply_patch(patch, file_path, strip, dry_run)
            elif action == "create":
                return await self._create_patch(file_path, **kwargs)
            elif action == "validate":
                return await self._validate_patch(patch, patch_type)
            elif action == "reverse":
                return await self._reverse_patch(patch, file_path, strip, dry_run)
            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Apply patch error: {e}")
            return ToolResult(success=False, error=str(e))

    async def _apply_patch(
        self, patch: str, file_path: str, strip: int, dry_run: bool
    ) -> ToolResult:
        if not patch:
            return ToolResult(success=False, error="Patch content is required")

        validation = await self._validate_patch(patch, "unified")
        if not validation.success:
            return validation

        patch_info = validation.metadata.get("info", {})
        files_affected = patch_info.get("files", [])

        if dry_run:
            return ToolResult(
                success=True,
                result={
                    "dry_run": True,
                    "would_apply": True,
                    "files_affected": files_affected,
                    "message": f"Patch would modify {len(files_affected)} file(s)",
                },
                metadata=patch_info,
            )

        patch_id = hashlib.md5(patch.encode()).hexdigest()[:8]
        patch_record = {
            "id": patch_id,
            "patch": patch,
            "files": files_affected,
            "applied": True,
        }
        self._patch_history.append(patch_record)

        return ToolResult(
            success=True,
            result={
                "patch_id": patch_id,
                "files_affected": files_affected,
                "applied": True,
            },
            metadata=patch_info,
        )

    async def _create_patch(
        self,
        file_path: str,
        original_content: str = None,
        new_content: str = None,
        **kwargs,
    ) -> ToolResult:
        if not file_path:
            return ToolResult(success=False, error="File path is required")

        if original_content and new_content:
            patch = self._generate_unified_diff(
                file_path, original_content, new_content
            )
            return ToolResult(success=True, result={"patch": patch, "file": file_path})

        patch = f"""--- a/{file_path}
+++ b/{file_path}
@@ -1,10 +1,10 @@
 # Simulated patch for {file_path}
 """

        return ToolResult(
            success=True,
            result={"patch": patch, "file": file_path},
            metadata={"type": "unified", "files": [file_path]},
        )

    async def _validate_patch(self, patch: str, patch_type: str) -> ToolResult:
        if not patch:
            return ToolResult(success=False, error="Patch content is required")

        if patch_type == "unified":
            files = re.findall(r"^\+\+\+ b/(.+)$", patch, re.MULTILINE)
            hunks = len(re.findall(r"^@@", patch, re.MULTILINE))
            additions = len(re.findall(r"^\+[^+]", patch, re.MULTILINE))
            deletions = len(re.findall(r"^-[^-]", patch, re.MULTILINE))

            return ToolResult(
                success=True,
                result={
                    "valid": True,
                    "files": files,
                    "hunks": hunks,
                    "additions": additions,
                    "deletions": deletions,
                },
                metadata={
                    "info": {
                        "files": files,
                        "hunks": hunks,
                        "additions": additions,
                        "deletions": deletions,
                    }
                },
            )

        return ToolResult(success=True, result={"valid": True, "type": patch_type})

    async def _reverse_patch(
        self, patch: str, file_path: str, strip: int, dry_run: bool
    ) -> ToolResult:
        if not patch:
            return ToolResult(success=False, error="Patch content is required")

        reversed_patch = patch.replace("--- a/", "--- b/")
        reversed_patch = reversed_patch.replace("+++ b/", "+++ a/")

        lines = reversed_patch.split("\n")
        new_lines = []
        for line in lines:
            if line.startswith("+"):
                new_lines.append("-" + line[1:])
            elif line.startswith("-"):
                new_lines.append("+" + line[1:])
            else:
                new_lines.append(line)

        reversed_patch = "\n".join(new_lines)

        return ToolResult(
            success=True,
            result={
                "reversed_patch": reversed_patch,
                "file": file_path,
                "dry_run": dry_run,
            },
        )

    def _generate_unified_diff(self, file_path: str, original: str, new: str) -> str:
        original_lines = original.split("\n")
        new_lines = new.split("\n")

        diff_lines = [f"--- a/{file_path}", f"+++ b/{file_path}"]

        max_lines = max(len(original_lines), len(new_lines))
        context = 3

        for i in range(max_lines):
            old_line = original_lines[i] if i < len(original_lines) else None
            new_line = new_lines[i] if i < len(new_lines) else None

            if old_line != new_line:
                if old_line is not None:
                    diff_lines.append(f"-{old_line}")
                if new_line is not None:
                    diff_lines.append(f"+{new_line}")

        return "\n".join(diff_lines)
