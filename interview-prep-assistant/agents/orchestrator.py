import uuid
from agents import researcher, historical_fetcher, question_generator, company_insider
from agents.resume_parser import ResumeParserInput, run_resume_parser
from models.session import SessionState, ResearcherOutput, HistoricalQuestionsOutput, GeneratedQuestionsOutput
from models.schemas import ResumeParserOutput, CompanyInsiderOutput
from validation.gate import validate_researcher, validate_questions
from tools.cache import set_cache
from typing import Dict, Any, Optional, Callable
import concurrent.futures


def generate_question_set(
    company: str,
    role: str,
    resume_text: str = "",
    resume_path: str = "",
    progress_callback: Optional[Callable[[str], None]] = None,
) -> SessionState:
    """Generate a full question set using all agents. No Celery/Redis required.
    
    Args:
        progress_callback: Optional function called with status strings for UI updates.
    """
    def _status(msg: str):
        if progress_callback:
            progress_callback(msg)

    session_id = str(uuid.uuid4())
    session = SessionState(session_id=session_id, company=company, role=role)

    # --- Run Researcher, Historical Fetcher, and Company Insider in parallel ---
    _status("🔍 Researching company and role...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        future_res = pool.submit(researcher.execute, company, role)
        future_hist = pool.submit(historical_fetcher.execute, company, role)
        future_insider = pool.submit(
            _run_insider_safe, company, role
        )

        try:
            res_output = future_res.result(timeout=30)
        except Exception as e:
            print(f"Researcher error: {e}")
            res_output = ResearcherOutput(degraded=True)

        _status("📚 Fetching past interview questions...")

        try:
            hist_output = future_hist.result(timeout=30)
        except Exception as e:
            print(f"Historical fetcher error: {e}")
            hist_output = HistoricalQuestionsOutput(degraded=True)

        try:
            insider_output = future_insider.result(timeout=30)
        except Exception as e:
            print(f"Insider error: {e}")
            insider_output = CompanyInsiderOutput(degraded=True)

    session.researcher_output = res_output
    session.historical_output = hist_output
    session.insider_output = insider_output

    # Retry researcher if validation fails
    if not validate_researcher(session.researcher_output):
        _status("🔄 Retrying company research...")
        try:
            session.researcher_output = researcher.execute(company, role)
        except Exception:
            session.researcher_output = ResearcherOutput(degraded=True)

    # --- Run Question Generator ---
    _status("🧠 Generating interview questions...")

    try:
        qg_output = question_generator.execute(
            company,
            role,
            session.researcher_output,
            session.historical_output,
            None,  # resume_output — decoupled
            session.insider_output if session.insider_output else None,
        )
        session.generated_output = qg_output
    except Exception as e:
        print(f"Question generator error: {e}")
        session.generated_output = GeneratedQuestionsOutput(degraded=True)

    # Validation Gate
    is_valid, final_qs, error_msg = validate_questions(
        session.historical_output, session.generated_output
    )
    session.final_questions = final_qs
    session.status = "ready" if len(final_qs) > 0 else "error"

    _status("✅ Questions ready!")
    return session


def run_resume_review(resume_text: str, role: str, company: str) -> dict:
    """Run the resume parser/reviewer directly. Returns the review dict."""
    inp = ResumeParserInput(
        resume_text=resume_text,
        resume_path="",
        role=role,
        company=company,
        trace_id="streamlit",
    )
    output = run_resume_parser(inp)
    return output.model_dump()


def _run_insider_safe(company: str, role: str):
    """Run company insider agent with proper import."""
    from agents.company_insider import CompanyInsiderInput, run_company_insider as insider_execute
    inp = CompanyInsiderInput(company=company, role=role, trace_id="direct")
    return insider_execute(inp)
