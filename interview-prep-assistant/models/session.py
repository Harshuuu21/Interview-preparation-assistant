from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from .question import Question

class ResearcherOutput(BaseModel):
    culture: List[str] = Field(default_factory=list)
    recentNews: List[str] = Field(default_factory=list)
    roleExpectations: List[str] = Field(default_factory=list)
    degraded: bool = Field(default=False)

class HistoricalQuestionsOutput(BaseModel):
    behavioural: List[Question] = Field(default_factory=list)
    technical: List[Question] = Field(default_factory=list)
    coding: List[Question] = Field(default_factory=list)
    source: List[str] = Field(default_factory=list)
    degraded: bool = Field(default=False)

class GeneratedQuestionsOutput(BaseModel):
    generated: List[Question] = Field(default_factory=list)
    rationale: List[str] = Field(default_factory=list)
    degraded: bool = Field(default=False)

class SessionState(BaseModel):
    session_id: str
    company: str
    role: str
    researcher_output: Optional[ResearcherOutput] = None
    historical_output: Optional[HistoricalQuestionsOutput] = None
    generated_output: Optional[GeneratedQuestionsOutput] = None
    
    # New agent outputs
    resume_output: Optional[Any] = None # Will be ResumeParserOutput, using Any to avoid circular import if needed, or import above
    insider_output: Optional[Any] = None
    roadmap_output: Optional[Any] = None
    mock_mode: bool = False
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    
    final_questions: List[Question] = Field(default_factory=list)
    status: str = Field(default="initializing", description="initializing, ready, error")
