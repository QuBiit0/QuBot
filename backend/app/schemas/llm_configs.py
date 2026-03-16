"""
Pydantic request schemas for LLM config endpoints.
"""

from pydantic import BaseModel, Field

from ..models.enums import LlmProviderEnum


class LlmConfigCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider: LlmProviderEnum
    model_name: str = Field(..., min_length=1, max_length=100)
    api_key_ref: str | None = None
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(4096, ge=1, le=200000)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    extra_config: dict = Field(default_factory=dict)


class LlmConfigUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    model_name: str | None = Field(None, min_length=1, max_length=100)
    api_key_ref: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1, le=200000)
    top_p: float | None = Field(None, ge=0.0, le=1.0)
    extra_config: dict | None = None


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant|tool)$")
    content: str


class ChatToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict


class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    system_prompt: str | None = None
    tools: list[ChatToolDefinition] | None = None
