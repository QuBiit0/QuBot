"""
Skills API Endpoints

Skills are Markdown files stored in the filesystem.
This module handles CRUD operations and file management.
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.logging import get_logger
from app.database import get_session
from app.models.agent import Agent
from app.models.skill import (
    AgentSkill,
    AgentSkillAssignSchema,
    AgentSkillResponseSchema,
    Skill,
    SkillCategory,
    SkillCreateSchema,
    SkillResponseSchema,
    SkillUpdateSchema,
    SkillContentResponse,
    SkillExecutionResponseSchema,
)
from app.utils.id_generator import generate_id

logger = get_logger(__name__)

router = APIRouter(prefix="/skills", tags=["skills"])

SKILLS_BASE_PATH = Path("/app/skills")


@router.get("", response_model=list[SkillResponseSchema])
async def list_skills(
    public_only: bool = False,
    official_only: bool = False,
    search: str | None = None,
    category: SkillCategory | None = None,
    db: Session = Depends(get_session),
):
    """
    List available skills from filesystem.
    """
    skills = []

    if not SKILLS_BASE_PATH.exists():
        return []

    for skill_dir in SKILLS_BASE_PATH.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        try:
            content = skill_md.read_text()
            frontmatter = _parse_frontmatter(content)

            skill_data = {
                "id": skill_dir.name,
                "name": frontmatter.get("name", skill_dir.name),
                "description": frontmatter.get("description", ""),
                "category": frontmatter.get("category", "custom"),
                "triggers": frontmatter.get("triggers", []),
                "icon": frontmatter.get("icon", "📦"),
                "created_by": frontmatter.get("author"),
                "is_public": True,
                "is_official": frontmatter.get("official", False),
                "version": frontmatter.get("version", "1.0.0"),
                "usage_count": 0,
                "rating_average": 0,
                "rating_count": 0,
                "base_path": str(skill_dir),
                "has_scripts": (skill_dir / "scripts").exists(),
                "has_templates": (skill_dir / "templates").exists(),
                "has_assets": (skill_dir / "assets").exists(),
                "has_references": (skill_dir / "references").exists(),
                "created_at": datetime.fromtimestamp(skill_dir.stat().st_ctime),
                "updated_at": datetime.fromtimestamp(skill_dir.stat().st_mtime),
            }

            if category and skill_data["category"] != category.value:
                continue

            if search:
                search_lower = search.lower()
                if (
                    search_lower not in skill_data["name"].lower()
                    and search_lower not in skill_data["description"].lower()
                ):
                    continue

            if official_only and not skill_data["is_official"]:
                continue

            if public_only and not skill_data["is_public"]:
                continue

            skills.append(skill_data)

        except Exception as e:
            logger.warning(f"Failed to read skill {skill_dir.name}: {e}")
            continue

    return sorted(skills, key=lambda x: x["usage_count"], reverse=True)


@router.post(
    "", response_model=SkillResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_skill(
    skill_data: SkillCreateSchema,
    current_user=Depends(get_current_user),
):
    """Create a new skill directory with SKILL.md file."""

    skill_id = skill_data.id
    skill_path = SKILLS_BASE_PATH / skill_id

    if skill_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Skill '{skill_id}' already exists",
        )

    try:
        skill_path.mkdir(parents=True, exist_ok=True)
        (skill_path / "scripts").mkdir(exist_ok=True)
        (skill_path / "templates").mkdir(exist_ok=True)
        (skill_path / "assets").mkdir(exist_ok=True)
        (skill_path / "references").mkdir(exist_ok=True)

        skill_content = _generate_skill_md(
            skill_id=skill_id,
            name=skill_data.name,
            description=skill_data.description or "",
            category=skill_data.category.value,
            icon=skill_data.icon,
            triggers=skill_data.triggers,
            author=current_user.id if hasattr(current_user, "id") else "unknown",
        )

        (skill_path / "SKILL.md").write_text(skill_content)

        logger.info(f"Created skill: {skill_id}")

        return {
            "id": skill_id,
            "name": skill_data.name,
            "description": skill_data.description,
            "category": skill_data.category,
            "triggers": skill_data.triggers,
            "icon": skill_data.icon,
            "created_by": current_user.id if hasattr(current_user, "id") else None,
            "is_public": skill_data.is_public,
            "is_official": False,
            "version": "1.0.0",
            "usage_count": 0,
            "rating_average": 0,
            "rating_count": 0,
            "base_path": str(skill_path),
            "has_scripts": True,
            "has_templates": True,
            "has_assets": True,
            "has_references": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    except Exception as e:
        if skill_path.exists():
            shutil.rmtree(skill_path, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill: {str(e)}",
        )


@router.get("/{skill_id}", response_model=SkillContentResponse)
async def get_skill(
    skill_id: str,
    current_user=Depends(get_current_user),
):
    """Get skill content including full SKILL.md and file list."""

    skill_path = SKILLS_BASE_PATH / skill_id
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )

    try:
        content = skill_md.read_text()
        frontmatter = _parse_frontmatter(content)

        files = []
        for root, dirs, filenames in os.walk(skill_path):
            for filename in filenames:
                filepath = Path(root) / filename
                rel_path = filepath.relative_to(skill_path)
                files.append(
                    {
                        "path": str(rel_path),
                        "type": "file",
                    }
                )

        return {
            "id": skill_id,
            "name": frontmatter.get("name", skill_id),
            "description": frontmatter.get("description", ""),
            "category": frontmatter.get("category", "custom"),
            "triggers": frontmatter.get("triggers", []),
            "icon": frontmatter.get("icon", "📦"),
            "content": content,
            "metadata": frontmatter,
            "files": files,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read skill: {str(e)}",
        )


@router.put("/{skill_id}", response_model=SkillResponseSchema)
async def update_skill(
    skill_id: str,
    skill_data: SkillUpdateSchema,
    current_user=Depends(get_current_user),
):
    """Update skill metadata and SKILL.md frontmatter."""

    skill_path = SKILLS_BASE_PATH / skill_id
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )

    try:
        content = skill_md.read_text()
        frontmatter = _parse_frontmatter(content)
        body = _extract_body(content)

        if skill_data.name:
            frontmatter["name"] = skill_data.name
        if skill_data.description is not None:
            frontmatter["description"] = skill_data.description
        if skill_data.category:
            frontmatter["category"] = skill_data.category.value
        if skill_data.icon:
            frontmatter["icon"] = skill_data.icon
        if skill_data.triggers is not None:
            frontmatter["triggers"] = skill_data.triggers
        if skill_data.version:
            frontmatter["version"] = skill_data.version

        new_content = _generate_skill_md(
            skill_id=skill_id,
            name=frontmatter.get("name", skill_id),
            description=frontmatter.get("description", ""),
            category=frontmatter.get("category", "custom"),
            icon=frontmatter.get("icon", "📦"),
            triggers=frontmatter.get("triggers", []),
            author=frontmatter.get("author", "unknown"),
            body=body,
            version=frontmatter.get("version", "1.0.0"),
        )

        skill_md.write_text(new_content)

        return {
            "id": skill_id,
            "name": frontmatter.get("name", skill_id),
            "description": frontmatter.get("description", ""),
            "category": frontmatter.get("category", "custom"),
            "triggers": frontmatter.get("triggers", []),
            "icon": frontmatter.get("icon", "📦"),
            "created_by": frontmatter.get("author"),
            "is_public": True,
            "is_official": frontmatter.get("official", False),
            "version": frontmatter.get("version", "1.0.0"),
            "usage_count": 0,
            "rating_average": 0,
            "rating_count": 0,
            "base_path": str(skill_path),
            "has_scripts": (skill_path / "scripts").exists(),
            "has_templates": (skill_path / "templates").exists(),
            "has_assets": (skill_path / "assets").exists(),
            "has_references": (skill_path / "references").exists(),
            "created_at": datetime.fromtimestamp(skill_path.stat().st_ctime),
            "updated_at": datetime.utcnow(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill: {str(e)}",
        )


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    current_user=Depends(get_current_user),
):
    """Delete a skill directory."""

    skill_path = SKILLS_BASE_PATH / skill_id

    if not skill_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )

    try:
        shutil.rmtree(skill_path)
        logger.info(f"Deleted skill: {skill_id}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete skill: {str(e)}",
        )


@router.get("/{skill_id}/files/{path:path}")
async def get_skill_file(
    skill_id: str,
    path: str,
):
    """Get a file from within a skill directory."""

    skill_path = SKILLS_BASE_PATH / skill_id / path

    if not skill_path.exists() or not skill_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return {"path": str(skill_path), "content": skill_path.read_text()}


@router.post("/{skill_id}/files/{path:path}")
async def create_skill_file(
    skill_id: str,
    path: str,
    content: str,
):
    """Create or update a file within a skill directory."""

    skill_path = SKILLS_BASE_PATH / skill_id

    if not skill_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )

    file_path = skill_path / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)

    return {"path": str(file_path), "created": True}


@router.post("/{skill_id}/execute")
async def execute_skill(
    skill_id: str,
    parameters: dict[str, Any] | None = None,
    timeout: int = 30,
    agent_id: str | None = None,
    task_id: str | None = None,
    db: Session = Depends(get_session),
):
    """
    Execute a skill with given parameters.

    The skill must have an executable code block (Python or JavaScript).
    Execution is sandboxed with timeout and security validation.
    """
    from dataclasses import dataclass
    from enum import Enum

    class SkillLanguageEnum(str, Enum):
        PYTHON = "python"
        JAVASCRIPT = "javascript"

    @dataclass
    class RuntimeSkill:
        """Runtime skill object for execution (not stored in DB)."""

        id: str
        name: str
        description: str
        code: str
        language: Any
        metadata: dict

    skill_path = SKILLS_BASE_PATH / skill_id
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )

    try:
        content = skill_md.read_text()
        frontmatter = _parse_frontmatter(content)
        body = _extract_body(content)

        if not body or len(body.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skill has no executable code",
            )

        language_str = frontmatter.get("language", "python").lower()
        if language_str == "python":
            language = SkillLanguageEnum.PYTHON
        elif language_str in ("javascript", "js"):
            language = SkillLanguageEnum.JAVASCRIPT
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language: {language_str}. Use 'python' or 'javascript'.",
            )

        skill = RuntimeSkill(
            id=skill_id,
            name=frontmatter.get("name", skill_id),
            description=frontmatter.get("description", ""),
            code=body,
            language=language,
            metadata=frontmatter,
        )

        from app.services.skill_execution_service import SkillExecutionService

        service = SkillExecutionService(db)

        result = await service.execute_skill(
            skill=skill,
            parameters=parameters or {},
            agent_id=agent_id,
            task_id=task_id,
            timeout=timeout,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute skill {skill_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute skill: {str(e)}",
        )


# Helper functions


def _parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown content."""
    import yaml

    if not content.startswith("---"):
        return {}

    parts = content[3:].split("---", 1)
    if len(parts) < 2:
        return {}

    try:
        return yaml.safe_load(parts[0]) or {}
    except:
        return {}


def _extract_body(content: str) -> str:
    """Extract body content after frontmatter."""
    if not content.startswith("---"):
        return content

    parts = content[3:].split("---", 1)
    if len(parts) < 2:
        return ""

    return parts[1].strip()


def _generate_skill_md(
    skill_id: str,
    name: str,
    description: str,
    category: str,
    icon: str,
    triggers: list,
    author: str,
    body: str = "",
    version: str = "1.0.0",
) -> str:
    """Generate SKILL.md content with frontmatter."""
    import yaml

    frontmatter = {
        "name": skill_id,
        "description": description,
        "user-invocable": True,
        "argument-hint": "[task description]",
        "compatibility": "Universal",
        "license": "MIT",
        "metadata": {
            "author": author,
            "version": version,
            "framework": "Qubot",
            "icon": icon,
            "role": name,
            "type": "capability",
            "category": category,
            "triggers": triggers,
        },
    }

    content = "---\n"
    content += yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
    content += "---\n\n"

    if body:
        content += body + "\n\n"

    content += f"# {icon} {name}\n\n{description}\n"

    return content
