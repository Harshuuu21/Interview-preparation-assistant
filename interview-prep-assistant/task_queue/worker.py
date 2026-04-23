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
def run_question_generator(role: str, researcher_dict: dict, historical_dict: dict):
    from models.session import ResearcherOutput, HistoricalQuestionsOutput
    r_out = ResearcherOutput(**researcher_dict) if researcher_dict else None
    h_out = HistoricalQuestionsOutput(**historical_dict) if historical_dict else None
    output = question_generator.execute(role, r_out, h_out)
    return output.model_dump()

@celery_app.task(time_limit=30)
def run_judge(question: str, user_answer: str, role_context: str, company_context: str, iteration_count: int):
    output = judge.execute(question, user_answer, role_context, company_context, iteration_count)
    return output.model_dump()
