from task_queue.worker import run_researcher, run_historical, run_question_generator
from models.session import SessionState, ResearcherOutput, HistoricalQuestionsOutput, GeneratedQuestionsOutput
from validation.gate import validate_researcher, validate_questions
from celery import group
from typing import Dict, Any

def generate_question_set(company: str, role: str) -> SessionState:
    session = SessionState(session_id="new", company=company, role=role)
    
    # Run Researcher and Historical Fetcher in parallel
    job = group(
        run_researcher.s(company, role),
        run_historical.s(company, role)
    )
    result = job.apply_async()
    
    # Wait for results (timeout 30s)
    try:
        results = result.get(timeout=30)
        res_dict = results[0]
        hist_dict = results[1]
    except Exception as e:
        print(f"Error or timeout waiting for R & H agents: {e}")
        res_dict = {"degraded": True}
        hist_dict = {"degraded": True}
        
    session.researcher_output = ResearcherOutput(**res_dict) if res_dict else ResearcherOutput(degraded=True)
    session.historical_output = HistoricalQuestionsOutput(**hist_dict) if hist_dict else HistoricalQuestionsOutput(degraded=True)
    
    # Retry logic for researcher
    if not validate_researcher(session.researcher_output):
        print("Researcher validation failed. Retrying once...")
        try:
            res_dict = run_researcher.apply_async((company, role)).get(timeout=30)
            session.researcher_output = ResearcherOutput(**res_dict)
        except Exception:
            session.researcher_output = ResearcherOutput(degraded=True)

    # Now run Question Generator
    try:
        qg_result = run_question_generator.apply_async((
            role, 
            session.researcher_output.model_dump(), 
            session.historical_output.model_dump()
        )).get(timeout=30)
        session.generated_output = GeneratedQuestionsOutput(**qg_result)
    except Exception as e:
        print(f"Error or timeout waiting for QG agent: {e}")
        session.generated_output = GeneratedQuestionsOutput(degraded=True)
        
    # Validation Gate
    is_valid, final_qs, error_msg = validate_questions(session.historical_output, session.generated_output)
    
    session.final_questions = final_qs
    session.status = "ready" if len(final_qs) > 0 else "error"
    
    return session
