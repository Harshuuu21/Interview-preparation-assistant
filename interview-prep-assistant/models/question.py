from pydantic import BaseModel, Field
from typing import Optional

class Question(BaseModel):
    text: str = Field(..., description="The content of the interview question")
    frequency: int = Field(default=1, description="How often this question appears")
    difficulty: Optional[str] = Field(None, description="Difficulty: easy, medium, or hard")
    year: Optional[int] = Field(None, description="Year this question was reported")
    category: Optional[str] = Field(None, description="E.g., behavioural, technical, coding")
    source: Optional[str] = Field(None, description="Where this question was sourced from (e.g., Glassdoor)")
