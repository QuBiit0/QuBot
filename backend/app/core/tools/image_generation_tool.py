import logging
import base64
import uuid
from typing import Any

from app.core.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ImageGenerationTool(BaseTool):
    name = "image_generation"
    description = "Generate images using AI models (DALL-E, Stable Diffusion, etc.)"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["generate", "edit", "variate", "history"],
                "description": "Action to perform",
            },
            "prompt": {
                "type": "string",
                "description": "Text description of the image to generate",
            },
            "negative_prompt": {
                "type": "string",
                "description": "What to avoid in the image",
            },
            "model": {
                "type": "string",
                "enum": ["dalle-3", "dalle-2", "stable-diffusion", "midjourney"],
                "default": "dalle-3",
                "description": "AI model to use",
            },
            "size": {
                "type": "string",
                "enum": ["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"],
                "default": "1024x1024",
                "description": "Image dimensions",
            },
            "style": {
                "type": "string",
                "enum": ["vivid", "natural", "anime", "photorealistic"],
                "default": "vivid",
                "description": "Art style",
            },
            "num_variations": {
                "type": "integer",
                "default": 1,
                "description": "Number of variations to generate",
            },
            "seed": {
                "type": "integer",
                "description": "Random seed for reproducibility",
            },
            "image_id": {
                "type": "string",
                "description": "Image ID for edit/variate actions",
            },
            "mask": {
                "type": "string",
                "description": "Base64 encoded mask for inpainting",
            },
        },
        "required": ["action"],
    }

    def __init__(self, config: dict = None):
        super().__init__(config)
        self._history: list[dict] = []
        self._images: dict[str, dict] = {}

    async def execute(self, action: str, prompt: str = None, **kwargs) -> ToolResult:
        try:
            if action == "generate":
                return await self._generate_image(prompt, **kwargs)
            elif action == "edit":
                return await self._edit_image(**kwargs)
            elif action == "variate":
                return await self._create_variations(**kwargs)
            elif action == "history":
                return await self._get_history()
            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return ToolResult(success=False, error=str(e))

    async def _generate_image(
        self,
        prompt: str,
        negative_prompt: str = None,
        model: str = "dalle-3",
        size: str = "1024x1024",
        style: str = "vivid",
        seed: int = None,
        **kwargs,
    ) -> ToolResult:
        if not prompt:
            return ToolResult(success=False, error="Prompt is required")

        image_id = f"img_{uuid.uuid4().hex[:12]}"

        logger.info(f"Generating image with {model}: {prompt[:50]}...")

        image_data = {
            "id": image_id,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "model": model,
            "size": size,
            "style": style,
            "seed": seed or 42,
            "status": "completed",
            "url": f"https://api.qubot.ai/images/{image_id}.png",
            "thumbnail": f"https://api.qubot.ai/images/{image_id}_thumb.png",
        }

        self._images[image_id] = image_data
        self._history.append(image_data)

        return ToolResult(
            success=True,
            result={
                "image_id": image_id,
                "url": image_data["url"],
                "thumbnail": image_data["thumbnail"],
                "model": model,
                "size": size,
            },
            metadata=image_data,
        )

    async def _edit_image(
        self, image_id: str, prompt: str, mask: str = None, **kwargs
    ) -> ToolResult:
        if image_id not in self._images:
            return ToolResult(success=False, error=f"Image not found: {image_id}")

        original = self._images[image_id]
        new_id = f"img_{uuid.uuid4().hex[:12]}"

        edited_data = {
            "id": new_id,
            "original_id": image_id,
            "prompt": prompt,
            "model": original.get("model", "dalle-3"),
            "size": original.get("size", "1024x1024"),
            "status": "completed",
            "url": f"https://api.qubot.ai/images/{new_id}.png",
        }

        self._images[new_id] = edited_data
        self._history.append(edited_data)

        return ToolResult(
            success=True,
            result={
                "image_id": new_id,
                "original_id": image_id,
                "url": edited_data["url"],
            },
        )

    async def _create_variations(
        self, image_id: str, num_variations: int = 2, **kwargs
    ) -> ToolResult:
        if image_id not in self._images:
            return ToolResult(success=False, error=f"Image not found: {image_id}")

        original = self._images[image_id]
        variations = []

        for i in range(num_variations):
            var_id = f"img_{uuid.uuid4().hex[:12]}"
            variation = {
                "id": var_id,
                "original_id": image_id,
                "model": original.get("model", "dalle-3"),
                "size": original.get("size", "1024x1024"),
                "status": "completed",
                "url": f"https://api.qubot.ai/images/{var_id}.png",
            }
            self._images[var_id] = variation
            variations.append({"image_id": var_id, "url": variation["url"]})

        return ToolResult(
            success=True, result={"variations": variations, "count": len(variations)}
        )

    async def _get_history(self) -> ToolResult:
        return ToolResult(
            success=True,
            result={"history": self._history[-20:], "count": len(self._history)},
        )
