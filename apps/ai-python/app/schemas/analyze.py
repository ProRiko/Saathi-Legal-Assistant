from pydantic import BaseModel, Field
from typing import List


class AnalyzeRequest(BaseModel):
    request_id: str
    document_text: str = Field(min_length=1, max_length=50000)
    analysis_type: str = 'contract_risk'


class AnalyzeResponse(BaseModel):
    summary: str
    key_clauses: List[str]
    risks: List[str]
    suggestions: List[str]
    lawyer_recommendation: str
