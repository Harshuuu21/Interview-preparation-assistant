from task_queue.worker import run_researcher, run_historical, run_question_generator, run_company_insider, run_resume_parser
from models.session import SessionState, ResearcherOutput, HistoricalQuestionsOutput, GeneratedQuestionsOutput
from models.schemas import ResumeParserOutput, CompanyInsiderOutput
from validation.gate import validate_researcher, validate_questions
from celery import group
from typing import Dict, Any, Optional

def generate_question_set(company: str, role: str, resume_text: str = "", resume_path: str = "") -> SessionState:
    session = SessionState(session_id="new", company=company, role=role)
    
    # Run Researcher, Historical Fetcher, Insider, and Resume Parser in parallel
    tasks = [
        run_researcher.s(company, role),
        run_historical.s(company, role),
        run_company_insider.s(company, role)
    ]
    if resume_text or resume_path:
        tasks.append(run_resume_parser.s(resume_text, resume_path, role, company))
        
    job = group(*tasks)
    result = job.apply_async()
    
    # Wait for results (timeout 30s)
    try:
        results = result.get(timeout=30)
        res_dict = results[0]
        hist_dict = results[1]
        insider_dict = results[2]
        resume_dict = results[3] if len(results) > 3 else None
    except Exception as e:
        print(f"Error or timeout waiting for agents: {e}")
        res_dict = {"degraded": True}
        hist_dict = {"degraded": True}
        insider_dict = {"degraded": True}
        resume_dict = None
        
    session.researcher_output = ResearcherOutput(**res_dict) if res_dict else ResearcherOutput(degraded=True)
    session.historical_output = HistoricalQuestionsOutput(**hist_dict) if hist_dict else HistoricalQuestionsOutput(degraded=True)
    session.insider_output = CompanyInsiderOutput(**insider_dict) if insider_dict else CompanyInsiderOutput(degraded=True)
    if resume_dict:
        session.resume_output = ResumeParserOutput(**resume_dict)
    
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
            company, role, 
            session.researcher_output.model_dump(), 
            session.historical_output.model_dump(),
            session.resume_output.model_dump() if session.resume_output else None,
            session.insider_output.model_dump() if session.insider_output else None
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

