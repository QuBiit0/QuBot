from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: str

class LlmResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: List[ToolCall] = []
    raw_response: Any = None

class BaseLlmProvider(ABC):
    @abstractmethod
    async def complete(
        self, 
        messages: List[Message], 
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LlmResponse:
        pass

    @abstractmethod
    async def test_connectivity(self) -> bool:
        pass
