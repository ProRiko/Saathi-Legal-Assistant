from pydantic import BaseModel, Field
from typing import List, Dict, Any


class ChatMessage(BaseModel):
    role: str = Field(min_length=1, max_length=16)
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    request_id: str
    user_ref: str
    conversation_ref: str
    language: str = 'english'
    messages: List[ChatMessage]
    options: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    reply: str
    intent: str | None = None
    provider: str
    model: str
    guardrails: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
