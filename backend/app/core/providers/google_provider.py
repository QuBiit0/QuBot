"""
Google/Gemini Provider - Implementation for Google AI API
"""

import os
import time
from collections.abc import AsyncGenerator

import google.generativeai as genai

from .base import BaseLlmProvider, FinishReason, LlmResponse, ToolCall, ToolDefinition
from .registry import register_provider


@register_provider("google")
class GoogleProvider(BaseLlmProvider):
    """Google Gemini API provider with tool-calling support"""

    # Pricing per 1K tokens (as of 2024)
    PRICING = {
        "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
        "gemini-1.5-flash": {"input": 0.00035, "output": 0.00105},
        "gemini-1.0-pro": {"input": 0.0005, "output": 0.0015},
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Configure API key
        api_key = self.api_key or os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)

        # Create model
        self._model = genai.GenerativeModel(
            model_name=self.model,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "top_p": self.top_p,
            },
        )

    @property
    def provider_name(self) -> str:
        return "google"

    def prepare_tools(self, tools: list[ToolDefinition]) -> list:
        """Convert to Gemini FunctionDeclaration format"""
        declarations = []
        for tool in tools:
            from google.generativeai.types import FunctionDeclaration

            declaration = FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
            )
            declarations.append(declaration)
        return declarations

    def format_messages(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> tuple:
        """
        Format messages for Gemini API.
        Gemini uses a different format: user/model alternation.
        Returns (contents, system_instruction)
        """
        contents = []

        for msg in messages:
            role = msg["role"]
            # Gemini uses 'user' and 'model'
            if role == "assistant":
                role = "model"

            contents.append(
                {
                    "role": role,
                    "parts": [{"text": msg["content"]}],
                }
            )

        return contents, system_prompt

    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> LlmResponse:
        """Generate completion using Gemini API"""
        start_time = time.time()

        # Format messages
        contents, system = self.format_messages(messages, system_prompt)

        # Start chat
        chat = self._model.start_chat(
            history=contents[:-1] if len(contents) > 1 else []
        )

        # Prepare generation config
        generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

        # Add tools if provided
        tool_config = None
        if tools:
            from google.generativeai.types import Tool

            tool_declarations = self.prepare_tools(tools)
            gemini_tools = Tool(function_declarations=tool_declarations)
            tool_config = {
                "function_calling_config": {
                    "mode": "AUTO",
                }
            }
        else:
            gemini_tools = None

        # Get last message
        last_message = contents[-1]["parts"][0]["text"] if contents else ""

        # Make request
        response = await chat.send_message_async(
            last_message,
            generation_config=generation_config,
            tools=gemini_tools,
            tool_config=tool_config,
        )

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Parse response
        content_text = None
        tool_calls = []

        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.text:
                    content_text = part.text
                elif part.function_call:
                    tool_calls.append(
                        ToolCall.from_google(
                            {
                                "id": f"call_{time.time()}",
                                "name": part.function_call.name,
                                "args": dict(part.function_call.args),
                            }
                        )
                    )

        # Get token counts
        usage = response.usage_metadata
        input_tokens = usage.prompt_token_count if usage else 0
        output_tokens = usage.candidates_token_count if usage else 0

        # Map finish reason
        finish_reason_map = {
            1: FinishReason.STOP,  # STOP
            2: FinishReason.LENGTH,  # MAX_TOKENS
            3: FinishReason.CONTENT_FILTER,  # SAFETY
            4: FinishReason.STOP,  # RECITATION
            5: FinishReason.STOP,  # OTHER
        }

        # Determine finish reason from candidate
        finish_reason = FinishReason.STOP
        if response.candidates:
            finish_reason_code = response.candidates[0].finish_reason.value
            finish_reason = finish_reason_map.get(
                finish_reason_code, FinishReason.ERROR
            )

        return LlmResponse(
            content=content_text if not tool_calls else None,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            provider=self.provider_name,
            latency_ms=latency_ms,
            raw_response={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": p.text}
                                if p.text
                                else {
                                    "function_call": {
                                        "name": p.function_call.name,
                                        "args": dict(p.function_call.args),
                                    }
                                }
                                for p in c.content.parts
                            ],
                            "role": c.content.role,
                        },
                        "finish_reason": c.finish_reason.name
                        if c.finish_reason
                        else None,
                    }
                    for c in response.candidates
                ],
                "usage": {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                }
                if usage
                else None,
            },
        )

    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        tools: list[ToolDefinition] | None = None,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming completion"""
        contents, system = self.format_messages(messages, system_prompt)

        chat = self._model.start_chat(
            history=contents[:-1] if len(contents) > 1 else []
        )
        last_message = contents[-1]["parts"][0]["text"] if contents else ""

        # Note: Gemini streaming doesn't support tools well
        if tools:
            raise ValueError("Gemini streaming with tools not fully supported")

        response = await chat.send_message_async(
            last_message,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "top_p": self.top_p,
            },
            stream=True,
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def get_token_count(self, text: str) -> int:
        """Estimate token count for Gemini"""
        try:
            response = await self._model.count_tokens_async(text)
            return response.total_tokens
        except Exception:
            # Fallback
            return len(text) // 4

    async def test_connection(self) -> bool:
        """Test API connectivity"""
        try:
            await self._model.generate_content_async(
                "Hi",
                generation_config={"max_output_tokens": 1},
            )
            return True
        except Exception:
            return False

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on model pricing"""
        pricing = self.PRICING.get(self.model, {"input": 0, "output": 0})

        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]

        return round(input_cost + output_cost, 6)
