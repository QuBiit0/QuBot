import logging
import base64
import json
import uuid
from io import BytesIO
from typing import Any

from app.core.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class CanvasTool(BaseTool):
    name = "canvas"
    description = "Visual rendering and canvas manipulation for generating images, diagrams, and UI mockups"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "render", "update", "export", "list"],
                "description": "Action to perform",
            },
            "canvas_id": {"type": "string", "description": "Canvas identifier"},
            "canvas_config": {
                "type": "object",
                "description": "Canvas configuration",
                "properties": {
                    "width": {"type": "integer", "default": 800},
                    "height": {"type": "integer", "default": 600},
                    "background": {"type": "string", "default": "#ffffff"},
                    "elements": {"type": "array", "items": {"type": "object"}},
                },
            },
            "elements": {
                "type": "array",
                "description": "Elements to add/update on canvas",
                "items": {"type": "object"},
            },
            "format": {
                "type": "string",
                "enum": ["png", "svg", "json"],
                "default": "png",
                "description": "Export format",
            },
        },
        "required": ["action"],
    }

    def __init__(self, config: dict = None):
        super().__init__(config)
        self._canvases: dict[str, dict] = {}

    async def execute(
        self,
        action: str,
        canvas_id: str = None,
        canvas_config: dict = None,
        elements: list = None,
        format: str = "png",
        **kwargs,
    ) -> ToolResult:
        try:
            if action == "create":
                return await self._create_canvas(canvas_config or {})
            elif action == "render":
                return await self._render_canvas(canvas_id, elements or [])
            elif action == "update":
                return await self._update_canvas(canvas_id, elements or [])
            elif action == "export":
                return await self._export_canvas(canvas_id, format)
            elif action == "list":
                return await self._list_canvases()
            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Canvas tool error: {e}")
            return ToolResult(success=False, error=str(e))

    async def _create_canvas(self, config: dict) -> ToolResult:
        canvas_id = f"canvas_{uuid.uuid4().hex[:8]}"
        width = config.get("width", 800)
        height = config.get("height", 600)
        background = config.get("background", "#ffffff")

        canvas = {
            "id": canvas_id,
            "width": width,
            "height": height,
            "background": background,
            "elements": config.get("elements", []),
            "created": True,
        }
        self._canvases[canvas_id] = canvas

        return ToolResult(
            success=True,
            result={
                "canvas_id": canvas_id,
                "config": {"width": width, "height": height},
            },
            metadata={"canvas": canvas},
        )

    async def _render_canvas(self, canvas_id: str, elements: list) -> ToolResult:
        if canvas_id not in self._canvases:
            return ToolResult(success=False, error=f"Canvas not found: {canvas_id}")

        canvas = self._canvases[canvas_id]
        canvas["elements"].extend(elements)

        image_data = self._generate_mock_image(canvas)

        return ToolResult(
            success=True,
            result={
                "canvas_id": canvas_id,
                "image": image_data,
                "element_count": len(canvas["elements"]),
            },
            metadata={"width": canvas["width"], "height": canvas["height"]},
        )

    async def _update_canvas(self, canvas_id: str, elements: list) -> ToolResult:
        if canvas_id not in self._canvases:
            return ToolResult(success=False, error=f"Canvas not found: {canvas_id}")

        canvas = self._canvases[canvas_id]
        for element in elements:
            element_id = element.get("id")
            for i, existing in enumerate(canvas["elements"]):
                if existing.get("id") == element_id:
                    canvas["elements"][i] = element
                    break
            else:
                canvas["elements"].append(element)

        return ToolResult(
            success=True,
            result={"canvas_id": canvas_id, "elements_updated": len(elements)},
            metadata={"total_elements": len(canvas["elements"])},
        )

    async def _export_canvas(self, canvas_id: str, format: str) -> ToolResult:
        if canvas_id not in self._canvases:
            return ToolResult(success=False, error=f"Canvas not found: {canvas_id}")

        canvas = self._canvases[canvas_id]

        if format == "json":
            data = json.dumps(canvas, indent=2)
            return ToolResult(
                success=True,
                result={"canvas_id": canvas_id, "data": data, "format": "json"},
            )
        elif format == "svg":
            svg = self._generate_svg(canvas)
            return ToolResult(
                success=True,
                result={"canvas_id": canvas_id, "data": svg, "format": "svg"},
            )
        else:
            image_data = self._generate_mock_image(canvas)
            return ToolResult(
                success=True,
                result={"canvas_id": canvas_id, "image": image_data, "format": "png"},
            )

    async def _list_canvases(self) -> ToolResult:
        return ToolResult(
            success=True,
            result={
                "canvases": list(self._canvases.keys()),
                "count": len(self._canvases),
            },
        )

    def _generate_mock_image(self, canvas: dict) -> str:
        return base64.b64encode(b"Mock PNG Image Data").decode("utf-8")

    def _generate_svg(self, canvas: dict) -> str:
        width = canvas.get("width", 800)
        height = canvas.get("height", 600)
        bg = canvas.get("background", "#ffffff")

        elements_svg = ""
        for elem in canvas.get("elements", []):
            elem_type = elem.get("type", "rect")
            if elem_type == "rect":
                x = elem.get("x", 0)
                y = elem.get("y", 0)
                w = elem.get("width", 100)
                h = elem.get("height", 100)
                fill = elem.get("fill", "#000000")
                elements_svg += (
                    f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'
                )
            elif elem_type == "text":
                x = elem.get("x", 0)
                y = elem.get("y", 20)
                text = elem.get("text", "")
                fill = elem.get("fill", "#000000")
                elements_svg += f'<text x="{x}" y="{y}" fill="{fill}">{text}</text>'

        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
            <rect width="100%" height="100%" fill="{bg}"/>
            {elements_svg}
        </svg>'''
        return svg
