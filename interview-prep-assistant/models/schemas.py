from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from models.question import Question
from models.feedback import FeedbackBreakdown

class PeerComparisonOutput(BaseModel):
    percentile: Optional[int]
    avg_score: Optional[float]
    avg_breakdown: Optional[FeedbackBreakdown]
    sample_size: int
    top_gap: Optional[str]
    insufficient_data: bool = False

class ProgressTrackerOutput(BaseModel):
    all_time_avg: float
    trend: str
    category_trends: Dict[str, str]
    sessions_completed: int
    streak_days: int
    milestone: Optional[str]

class ResumeParserOutput(BaseModel):
    skills: List[str] = Field(default_factory=list)
    experience_years: int = 0
    past_roles: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    education: str = ""
    gaps: List[str] = Field(default_factory=list)
    resume_summary: str = ""
    degraded: bool = False

class CompanyInsiderOutput(BaseModel):
    interview_process: List[str] = Field(default_factory=list)
    known_focus_areas: List[str] = Field(default_factory=list)
    common_mistakes: List[str] = Field(default_factory=list)
    culture_signals: List[str] = Field(default_factory=list)
    insider_tips: List[str] = Field(default_factory=list)
    degraded: bool = False

class RoadmapItem(BaseModel):
    day: int
    topic: str
    action: str
    resource_type: str
    estimated_minutes: int

class RoadmapAgentOutput(BaseModel):
    weak_areas: List[str] = Field(default_factory=list)
    roadmap: List[RoadmapItem] = Field(default_factory=list)
    estimated_hours: int = 0
    priority_questions: List[str] = Field(default_factory=list)

class NegotiationScript(BaseModel):
    scenario: str
    suggested_response: str

class SalaryNegotiatorOutput(BaseModel):
    market_range: Dict[str, str] = Field(default_factory=dict)
    company_typical_range: str = ""
    negotiation_scripts: List[NegotiationScript] = Field(default_factory=list)
    dos: List[str] = Field(default_factory=list)
    donts: List[str] = Field(default_factory=list)
    degraded: bool = False

class MockConductorOutput(BaseModel):
    follow_up_question: Optional[str]
    interviewer_reaction: str
    should_move_on: bool
    adjusted_difficulty: int
    turn_count: int

class AnswerTemplateOutput(BaseModel):
    template: str
    key_points_to_hit: List[str]
    what_to_avoid: List[str]
    word_count_target: int
