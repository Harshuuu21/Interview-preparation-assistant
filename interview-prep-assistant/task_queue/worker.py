import os
from celery import Celery
from agents import researcher, historical_fetcher, question_generator, judge
from dotenv import load_dotenv

load_dotenv()

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

celery_app = Celery("interview_prep_queue", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@celery_app.task(time_limit=30)
def run_researcher(company: str, role: str):
    output = researcher.execute(company, role)
    return output.model_dump()

@celery_app.task(time_limit=30)
def run_historical(company: str, role: str):
    output = historical_fetcher.execute(company, role)
    return output.model_dump()

@celery_app.task(time_limit=30)
def run_question_generator(company: str, role: str, researcher_dict: dict, historical_dict: dict, resume_dict: dict = None, insider_dict: dict = None):
    from models.session import ResearcherOutput, HistoricalQuestionsOutput
    from models.schemas import ResumeParserOutput, CompanyInsiderOutput
    r_out = ResearcherOutput(**researcher_dict) if researcher_dict else None
    h_out = HistoricalQuestionsOutput(**historical_dict) if historical_dict else None
    res_out = ResumeParserOutput(**resume_dict) if resume_dict else None
    ins_out = CompanyInsiderOutput(**insider_dict) if insider_dict else None
    output = question_generator.execute(company, role, r_out, h_out, res_out, ins_out)
    return output.model_dump()

@celery_app.task(time_limit=30)
def run_judge(question: str, user_answer: str, role_context: str, company_context: str, iteration_count: int):
    output = judge.execute(question, user_answer, role_context, company_context, iteration_count)
    return output.model_dump()

@celery_app.task(time_limit=30)
def run_company_insider(company: str, role: str):
    from agents.company_insider import CompanyInsiderInput, run_company_insider as insider_execute
    inp = CompanyInsiderInput(company=company, role=role, trace_id="celery")
    output = insider_execute(inp)
    return output.model_dump()

@celery_app.task(time_limit=30)
def run_resume_parser(resume_text: str, resume_path: str, role: str, company: str):
    from agents.resume_parser import ResumeParserInput, run_resume_parser as parser_execute
    inp = ResumeParserInput(resume_text=resume_text, resume_path=resume_path, role=role, company=company, trace_id="celery")
    output = parser_execute(inp)
    return output.model_dump()
