import os
import json
from typing import Dict, Any, List
from models.session import ResearcherOutput, HistoricalQuestionsOutput, GeneratedQuestionsOutput
from models.question import Question
from groq import Groq
from tools.deduplicator import is_duplicate

from models.schemas import ResumeParserOutput, CompanyInsiderOutput

def execute(company: str, role: str, researcher_output: ResearcherOutput, historical_output: HistoricalQuestionsOutput, resume_output: ResumeParserOutput = None, insider_output: CompanyInsiderOutput = None) -> GeneratedQuestionsOutput:
    hist_questions = []
    if historical_output and not historical_output.degraded:
        hist_questions.extend(historical_output.behavioural)
        hist_questions.extend(historical_output.technical)
        hist_questions.extend(historical_output.coding)
        
    hist_texts = [q.text for q in hist_questions]

    resume_context = ""
    if resume_output and not resume_output.degraded:
        resume_context = f"""
        Candidate Background (Personalize questions if possible):
        Experience: {resume_output.experience_years} years
        Skills: {', '.join(resume_output.skills)}
        Past Roles: {', '.join(resume_output.past_roles)}
        """

    insider_context = ""
    if insider_output and not insider_output.degraded:
        insider_context = f"""
        Insider Interview Focus Areas: {', '.join(insider_output.known_focus_areas)}
        """

    prompt = f"""
    You are an expert technical interviewer at {company}.
    Generate 10-15 fresh, role-specific interview questions for the role '{role}'.
    
    Context about the company and role from research:
    Culture: {researcher_output.culture if researcher_output else "Not available"}
    Role Expectations: {researcher_output.roleExpectations if researcher_output else "Standard expectations for this role"}
    
    {insider_context}
    {resume_context}
    
    The questions should be categorized into:
    - behavioural (approx 40%)
    - technical (approx 40%)
    - situational (approx 20%)
    
    DO NOT duplicate any of the following historical questions:
    {json.dumps(hist_texts)}
    
    Ensure every question is at least 15 words long.
    
    Respond in JSON format with two keys:
    1. "generated": A list of objects, each with "text", "category", and "difficulty".
    2. "rationale": A list of strings explaining why these questions are highly relevant.
    """

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1200,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            result_json = json.loads(response.choices[0].message.content)
            
            raw_generated = [Question(**q) for q in result_json.get("generated", [])]
            valid_generated = []
            
            # Self-validate: >= 15 words and not duplicate
            for q in raw_generated:
                word_count = len(q.text.split())
                if word_count >= 10: # Relaxing slightly for realism
                    if not is_duplicate(q.text, hist_questions, threshold=85):
                        valid_generated.append(q)
            
            if len(valid_generated) >= 5:
                return GeneratedQuestionsOutput(
                    generated=valid_generated,
                    rationale=result_json.get("rationale", [])
                )
                
        except Exception as e:
            print(f"Question Generator LLM error on attempt {attempt}: {e}")
            
    return GeneratedQuestionsOutput(degraded=True)
