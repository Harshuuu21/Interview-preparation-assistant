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
    """Run a comprehensive resume review using the LLM. Returns a rich review dict
    with overall_score, ats_score, verdict, strengths, improvements, etc."""
    import os
    import json
    import hashlib
    from tools.cache import get_cache, set_cache

    cache_key = "resume_review:" + hashlib.md5(
        (resume_text + role + company).encode()
    ).hexdigest()
    cached = get_cache(cache_key)
    if cached:
        return cached

    prompt = f"""You are an expert resume reviewer and career coach.
Analyze the following resume for a **{role}** position at **{company}**.

Resume Text:
{resume_text}

Return ONLY a valid JSON object with this exact schema:
{{
    "overall_score": <int 0-100>,
    "overall_grade": "<string, e.g. 'Strong Match', 'Good Match', 'Needs Work'>",
    "ats_score": <int 0-100, how well this resume would pass ATS systems>,
    "keyword_match_score": <int 0-100, how many relevant keywords for the role are present>,
    "verdict": "<2-3 sentence professional summary of the resume's fit for this role>",
    "score_breakdown": {{
        "experience": {{"label": "Experience", "score": <int 0-25>, "max": 25}},
        "skills": {{"label": "Skills Match", "score": <int 0-25>, "max": 25}},
        "education": {{"label": "Education", "score": <int 0-25>, "max": 25}},
        "presentation": {{"label": "Presentation", "score": <int 0-25>, "max": 25}}
    }},
    "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "improvements": [
        {{"section": "<resume section>", "priority": "<high|medium|low>", "issue": "<what's wrong>", "suggestion": "<how to fix>"}},
        {{"section": "<resume section>", "priority": "<high|medium|low>", "issue": "<what's wrong>", "suggestion": "<how to fix>"}}
    ],
    "missing_for_role": ["<missing skill/keyword 1>", "<missing skill/keyword 2>"]
}}
"""

    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        review = json.loads(response.choices[0].message.content)

        # Ensure required keys exist with defaults
        review.setdefault("overall_score", 0)
        review.setdefault("overall_grade", "Unknown")
        review.setdefault("ats_score", 0)
        review.setdefault("keyword_match_score", 0)
        review.setdefault("verdict", "")
        review.setdefault("score_breakdown", {})
        review.setdefault("strengths", [])
        review.setdefault("improvements", [])
        review.setdefault("missing_for_role", [])

        set_cache(cache_key, review, ttl_seconds=43200)
        return review

    except Exception as e:
        print(f"Resume review LLM error: {e}")
        # Return a minimal valid structure so the UI doesn't crash
        return {
            "overall_score": 0,
            "overall_grade": "Error",
            "ats_score": 0,
            "keyword_match_score": 0,
            "verdict": f"Resume review could not be completed: {e}",
            "score_breakdown": {},
            "strengths": [],
            "improvements": [],
            "missing_for_role": [],
        }


def _run_insider_safe(company: str, role: str):
    """Run company insider agent with proper import."""
    from agents.company_insider import CompanyInsiderInput, run_company_insider as insider_execute
    inp = CompanyInsiderInput(company=company, role=role, trace_id="direct")
    return insider_execute(inp)
