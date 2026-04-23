from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uvicorn
from agents.orchestrator import generate_question_set
from agents.judge import execute as judge_execute
from task_queue.worker import run_judge
from models.session import SessionState
from observability.tracing import tracer
import json

app = FastAPI(title="Interview Prep Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StartSessionRequest(BaseModel):
    company: str
    role: str

class EvaluateAnswerRequest(BaseModel):
    question: str
    user_answer: str
    role_context: str
    company_context: str
    iteration_count: int

@app.post("/api/start_session")
def start_session(req: StartSessionRequest):
    with tracer.start_as_current_span("start_session"):
        session = generate_question_set(req.company, req.role)
        if session.status == "error":
            raise HTTPException(status_code=500, detail="Failed to generate questions")
        return session.model_dump()

@app.post("/api/evaluate_answer")
def evaluate_answer(req: EvaluateAnswerRequest):
    with tracer.start_as_current_span("evaluate_answer"):
        try:
            # We use apply_async to route through Celery
            result = run_judge.apply_async((
                req.question,
                req.user_answer,
                req.role_context,
                req.company_context,
                req.iteration_count
            )).get(timeout=30)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# Mount UI
if os.path.exists("ui"):
    from fastapi.responses import FileResponse
    
    app.mount("/static", StaticFiles(directory="ui"), name="static")

    @app.get("/")
    def read_index():
        return FileResponse("ui/index.html")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
