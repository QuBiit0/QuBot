"""
Skill Creator Tool - Create skills as Markdown files with resources.

Skills are directories containing:
- SKILL.md (main file with frontmatter)
- scripts/ (helper scripts)
- templates/ (templates)
- assets/ (images, icons)
- references/ (documentation)
"""

import json
import os
from pathlib import Path

from .base import BaseTool, ToolParameter, ToolResult, ToolCategory, ToolRiskLevel


class SkillCreatorTool(BaseTool):
    """
    Create reusable skills as Markdown files. Each skill is a directory
    with a SKILL.md file and optional scripts, templates, assets, and references.
    """

    name = "create_skill"
    description = (
        "Create a new skill as a Markdown file with metadata. "
        "Skills can include scripts, templates, and assets. "
        "Use to teach agents new capabilities or workflows."
    )

    category = ToolCategory.SYSTEM
    risk_level = ToolRiskLevel.NORMAL

    SKILLS_BASE_PATH = "/app/skills"

    DEFAULT_SKILL_TEMPLATE = """---
name: "{skill_id}"
description: "{description}"
user-invocable: true
argument-hint: "[task description]"
compatibility: "Universal - All AI agents"
license: MIT

metadata:
  author: "agent"
  version: "1.0.0"
  framework: Qubot
  icon: "{icon}"
  role: "{name}"
  type: "capability"
  category: "{category}"
  triggers: {triggers}
---

# {name}

{description}

## System Prompt

```
You are a {name} skill. Your purpose is to {description}.
```

## Instructions

{instructions}

## Resources

{has_resources}

## Examples

{examples}
"""

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "name": ToolParameter(
                name="name",
                type="string",
                description="Human-readable name for the skill (e.g., 'Data Analyzer', 'Email Sender')",
                required=True,
            ),
            "skill_id": ToolParameter(
                name="skill_id",
                type="string",
                description="Unique ID in kebab-case (e.g., 'data-analyzer', 'email-sender')",
                required=True,
            ),
            "description": ToolParameter(
                name="description",
                type="string",
                description="What this skill does (used by agents to understand when to use it)",
                required=False,
                default="",
            ),
            "instructions": ToolParameter(
                name="instructions",
                type="string",
                description="Detailed instructions for the agent on how to use this skill",
                required=False,
                default="",
            ),
            "examples": ToolParameter(
                name="examples",
                type="string",
                description="Example use cases or prompts for this skill",
                required=False,
                default="",
            ),
            "category": ToolParameter(
                name="category",
                type="string",
                description="Skill category: development, data, design, operations, marketing, research, custom",
                required=False,
                default="custom",
                enum=[
                    "development",
                    "data",
                    "design",
                    "operations",
                    "marketing",
                    "research",
                    "custom",
                ],
            ),
            "icon": ToolParameter(
                name="icon",
                type="string",
                description="Emoji icon for the skill",
                required=False,
                default="📦",
            ),
            "triggers": ToolParameter(
                name="triggers",
                type="string",
                description='Slash commands that activate this skill (JSON array, e.g. \'["/analyze", "/data"]\')',
                required=False,
                default="[]",
            ),
            "scripts": ToolParameter(
                name="scripts",
                type="string",
                description="JSON object of scripts to create: {'script.py': 'print(\"hello\")'}",
                required=False,
                default="{}",
            ),
            "templates": ToolParameter(
                name="templates",
                type="string",
                description="JSON object of templates to create: {'template.md': '# {{title}}'}",
                required=False,
                default="{}",
            ),
            "references": ToolParameter(
                name="references",
                type="string",
                description="JSON object of reference docs: {'api.md': '# API Reference'}",
                required=False,
                default="{}",
            ),
        }

    async def execute(self, **params) -> ToolResult:
        """Create a new skill directory with SKILL.md and resources"""
        import shutil

        name = params.get("name", "")
        skill_id = params.get("skill_id", "").lower().replace(" ", "-")
        description = params.get("description", "")
        instructions = params.get("instructions", "")
        examples = params.get("examples", "")
        category = params.get("category", "custom")
        icon = params.get("icon", "📦")
        triggers_str = params.get("triggers", "[]")
        scripts_str = params.get("scripts", "{}")
        templates_str = params.get("templates", "{}")
        references_str = params.get("references", "{}")

        if not name:
            return ToolResult(success=False, error="Skill name is required")

        if not skill_id:
            return ToolResult(success=False, error="Skill ID is required")

        if not skill_id.replace("-", "").replace("_", "").isalnum():
            return ToolResult(
                success=False,
                error="Skill ID must contain only letters, numbers, and hyphens",
            )

        try:
            triggers = json.loads(triggers_str) if triggers_str else []
            scripts = json.loads(scripts_str) if scripts_str else {}
            templates = json.loads(templates_str) if templates_str else {}
            references = json.loads(references_str) if references_str else {}
        except json.JSONDecodeError as e:
            return ToolResult(success=False, error=f"Invalid JSON: {str(e)}")

        try:
            skill_path = Path(self.SKILLS_BASE_PATH) / skill_id

            if skill_path.exists():
                return ToolResult(
                    success=False, error=f"Skill '{skill_id}' already exists"
                )

            skill_path.mkdir(parents=True, exist_ok=True)

            (skill_path / "scripts").mkdir(exist_ok=True)
            (skill_path / "templates").mkdir(exist_ok=True)
            (skill_path / "assets").mkdir(exist_ok=True)
            (skill_path / "references").mkdir(exist_ok=True)

            skill_content = self._generate_skill_content(
                name=name,
                skill_id=skill_id,
                description=description,
                instructions=instructions,
                examples=examples,
                category=category,
                icon=icon,
                triggers=triggers,
                has_scripts=bool(scripts),
                has_templates=bool(templates),
                has_references=bool(references),
            )

            (skill_path / "SKILL.md").write_text(skill_content)

            for filename, content in scripts.items():
                (skill_path / "scripts" / filename).write_text(content)

            for filename, content in templates.items():
                (skill_path / "templates" / filename).write_text(content)

            for filename, content in references.items():
                (skill_path / "references" / filename).write_text(content)

            created_files = ["SKILL.md"]
            created_files.extend([f"scripts/{f}" for f in scripts.keys()])
            created_files.extend([f"templates/{f}" for f in templates.keys()])
            created_files.extend([f"references/{f}" for f in references.keys()])

            return ToolResult(
                success=True,
                data={
                    "message": f"Successfully created skill '{name}'",
                    "skill_id": skill_id,
                    "name": name,
                    "path": str(skill_path),
                    "category": category,
                    "triggers": triggers,
                    "files_created": created_files,
                    "usage": f"Agent can activate with: /{skill_id} or mention triggers",
                },
            )

        except PermissionError:
            return ToolResult(
                success=False,
                error="Permission denied. Cannot create skills directory.",
            )
        except Exception as e:
            import shutil as sh

            created_path = Path(self.SKILLS_BASE_PATH) / skill_id
            if created_path.exists():
                sh.rmtree(created_path, ignore_errors=True)
            return ToolResult(success=False, error=f"Failed to create skill: {str(e)}")

    def _generate_skill_content(
        self,
        name: str,
        skill_id: str,
        description: str,
        instructions: str,
        examples: str,
        category: str,
        icon: str,
        triggers: list,
        has_scripts: bool,
        has_templates: bool,
        has_references: bool,
    ) -> str:
        """Generate the SKILL.md content with frontmatter"""

        triggers_str = json.dumps(triggers)

        resources_section = "This skill has no additional resources."
        if has_scripts or has_templates or has_references:
            resources_parts = []
            if has_scripts:
                resources_parts.append("- `scripts/` - Helper scripts")
            if has_templates:
                resources_parts.append("- `templates/` - Templates")
            if has_references:
                resources_parts.append("- `references/` - Documentation")
            resources_section = "## Resources\n\n" + "\n".join(resources_parts)

        examples_section = ""
        if examples:
            examples_section = f"## Examples\n\n{examples}\n"

        return f'''---
name: "{skill_id}"
description: "{description}"
user-invocable: true
argument-hint: "[task description]"
compatibility: "Universal - All AI agents"
license: MIT

metadata:
  author: "agent"
  version: "1.0.0"
  framework: Qubot
  icon: "{icon}"
  role: "{name}"
  type: "capability"
  category: "{category}"
  triggers: {triggers_str}
---

# {icon} {name}

{description}

## System Prompt

```
You are **{name}**. Your purpose is to {description or "perform the defined task"}.
Follow these instructions carefully to complete the task effectively.
```

## Instructions

{instructions or "Execute the task according to the user's request. Use available resources and tools."}

{resources_section}

{examples_section}

## Metadata

| Field | Value |
|:------|:------|
| Version | 1.0.0 |
| Category | {category} |
| Created | Auto-generated |
'''
