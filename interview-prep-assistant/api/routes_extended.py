from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import uuid

from models.schemas import (
    PeerComparisonOutput, ProgressTrackerOutput, ResumeParserOutput,
    CompanyInsiderOutput, RoadmapAgentOutput, SalaryNegotiatorOutput,
    MockConductorOutput, AnswerTemplateOutput
)
from models.question import Question
from models.feedback import Feedback
from task_queue.worker import run_resume_parser, run_company_insider, run_judge

from agents.peer_comparison import record_score, run_peer_comparison, PeerComparisonInput
from agents.progress_tracker import update as update_progress, run_progress_tracker, ProgressTrackerInput
from agents.roadmap import run_roadmap, RoadmapInput
from agents.salary_negotiator import run_salary_negotiator, SalaryNegotiatorInput
from agents.mock_conductor import run_mock_conductor, MockConductorInput
from agents.answer_template import run_answer_template, AnswerTemplateInput

extended_router = APIRouter()

# Temporary in-memory session storage since we don't have a full redis-backed session manager defined in API yet
SESSIONS = {}

@extended_router.post("/api/session/upload-resume")
async def upload_resume(resume: UploadFile = File(...)):
    if resume.content_type not in ["application/pdf", "text/plain"]:
        raise HTTPException(status_code=400, detail="Only PDF and TXT supported")
    
    contents = await resume.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 2MB)")

    # Extract text
    resume_path = ""
    if resume.filename.endswith(".pdf"):
        import fitz
        doc = fitz.open(stream=contents, filetype="pdf")
        resume_text = "\n".join(page.get_text() for page in doc)
    else:
        resume_text = contents.decode("utf-8", errors="ignore")

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    try:
        # Run Celery task
        result = run_resume_parser.apply_async((resume_text, resume_path, "", "")).get(timeout=30)
        return {"parsed": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MockStartRequest(BaseModel):
    pass # Currently just URL param or body

@extended_router.post("/api/session/{session_id}/mock/start")
def start_mock(session_id: str):
    # In a real app we'd fetch the session from DB/Redis
    return {"message": "Mock session started. Please send responses to /mock/respond", "mock_mode": True}

class MockRespondRequest(BaseModel):
    company: str
    question: dict
    answer: str
    conversation_history: List[Dict[str, str]]
    difficulty_level: int = 2

@extended_router.post("/api/session/{session_id}/mock/respond")
def mock_respond(session_id: str, req: MockRespondRequest):
    inp = MockConductorInput(
        session_id=session_id,
        company=req.company,
        question=Question(**req.question),
        user_answer=req.answer,
        conversation_history=req.conversation_history,
        difficulty_level=req.difficulty_level,
        trace_id="api"
    )
    return run_mock_conductor(inp)

@extended_router.post("/api/session/{session_id}/mock/end")
def mock_end(session_id: str, req: dict):
    # Triggers judge on full conversation history
    try:
        result = run_judge.apply_async((
            json.dumps(req.get('question', {})),
            req.get('answer', ''),
            req.get('role', ''),
            req.get('company', ''),
            len(req.get('conversation_history', []))
        )).get(timeout=30)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RoadmapRequest(BaseModel):
    judge_outputs: List[dict]
    resume_output: Optional[dict] = None
    company: str
    role: str
    days_until_interview: Optional[int] = None

@extended_router.post("/api/session/{session_id}/roadmap")
def get_roadmap(session_id: str, req: RoadmapRequest):
    judge_outputs = [Feedback(**j) for j in req.judge_outputs]
    resume_output = ResumeParserOutput(**req.resume_output) if req.resume_output else None
    inp = RoadmapInput(
        judge_outputs=judge_outputs,
        resume_output=resume_output,
        company=req.company,
        role=req.role,
        days_until_interview=req.days_until_interview,
        trace_id=session_id
    )
    return run_roadmap(inp)

class SalaryRequest(BaseModel):
    company: str
    role: str
    location: str
    experience_years: int
    user_expected_salary: Optional[str] = None

@extended_router.post("/api/session/{session_id}/salary")
def get_salary(session_id: str, req: SalaryRequest):
    inp = SalaryNegotiatorInput(
        company=req.company,
        role=req.role,
        location=req.location,
        experience_years=req.experience_years,
        user_expected_salary=req.user_expected_salary,
        trace_id=session_id
    )
    return run_salary_negotiator(inp)

@extended_router.post("/api/scores/record")
def api_record_score(req: dict):
    # Typically called automatically, but exposed just in case
    # Format: {"question_id": str, "company": str, "role": str, "judge_output": dict, "user_id": str, "question": dict}
    try:
        feedback = Feedback(**req['judge_output'])
        record_score(req['question_id'], req['company'], req['role'], feedback)
        
        if 'user_id' in req and 'question' in req:
            update_progress(req['user_id'], feedback, Question(**req['question']), req['company'], req['role'])
            
        return {"status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@extended_router.get("/api/scores/compare/{question_id}")
def api_compare_score(question_id: str, company: str, role: str, user_score: float, user_breakdown: str):
    breakdown_dict = json.loads(user_breakdown)
    inp = PeerComparisonInput(
        question_id=question_id,
        company=company,
        role=role,
        user_score=user_score,
        user_breakdown=breakdown_dict,
        trace_id="api"
    )
    return run_peer_comparison(inp)

@extended_router.get("/api/session/{session_id}/insider-tips")
def get_insider_tips(session_id: str, company: str, role: str):
    # Could trigger async celery or run sync. We'll run sync wrapper for now or async result if already computed
    try:
        result = run_company_insider.apply_async((company, role)).get(timeout=30)
        return result
    except Exception as e:
        return {"degraded": True}

class TemplateRequest(BaseModel):
    question: dict
    role: str
    company: str
    resume_output: Optional[dict] = None

@extended_router.post("/api/session/{session_id}/template/{question_id}")
def get_template(session_id: str, question_id: str, req: TemplateRequest):
    resume_out = ResumeParserOutput(**req.resume_output) if req.resume_output else None
    inp = AnswerTemplateInput(
        question=Question(**req.question),
        role=req.role,
        company=req.company,
        resume_output=resume_out,
        trace_id=session_id
    )
    return run_answer_template(inp)

@extended_router.get("/api/user/{user_id}/progress")
def get_progress(user_id: str):
    return run_progress_tracker(user_id)
