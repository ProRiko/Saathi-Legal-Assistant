from pydantic import BaseModel, Field
from typing import List


class ClassifyRequest(BaseModel):
    request_id: str
    text: str = Field(min_length=1, max_length=4000)


class ClassifyResponse(BaseModel):
    intent: str
    confidence: float
    labels: List[str]
