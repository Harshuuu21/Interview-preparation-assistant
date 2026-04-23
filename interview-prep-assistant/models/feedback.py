from pydantic import BaseModel, Field
from typing import List

class FeedbackBreakdown(BaseModel):
    clarity: float = Field(..., ge=0, le=10)
    depth: float = Field(..., ge=0, le=10)
    relevance: float = Field(..., ge=0, le=10)
    starFormat: float = Field(..., ge=0, le=10, description="Situation, Task, Action, Result adherence")
    roleFit: float = Field(..., ge=0, le=10)

class Feedback(BaseModel):
    score: float = Field(..., ge=0, le=10, description="Overall score out of 10")
    breakdown: FeedbackBreakdown
    gaps: List[str] = Field(..., description="What's missing from the answer")
    improvedAnswer: str = Field(..., description="Rewritten version of the user answer")
    tips: List[str] = Field(..., description="2-3 actionable suggestions")
