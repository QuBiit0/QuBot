from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str
    name: str | None = None


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: str


class LlmResponse(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCall] = []
    raw_response: Any = None


class BaseLlmProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LlmResponse:
        pass

    @abstractmethod
    async def test_connectivity(self) -> bool:
        pass
