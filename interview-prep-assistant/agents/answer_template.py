import json
from pydantic import BaseModel
import os
from typing import Optional
from models.schemas import AnswerTemplateOutput, ResumeParserOutput
from models.question import Question
from tools.cache import get_cache, set_cache
import hashlib
from groq import Groq

class AnswerTemplateInput(BaseModel):
    question: Question
    role: str
    company: str
    resume_output: Optional[ResumeParserOutput] = None
    trace_id: str

def run_answer_template(input_data: AnswerTemplateInput) -> AnswerTemplateOutput:
    resume_context = ""
    if input_data.resume_output and not input_data.resume_output.degraded:
        resume_context = f"""
        Personalize the template placeholders using the candidate's actual background:
        Past Roles: {', '.join(input_data.resume_output.past_roles)}
        Skills: {', '.join(input_data.resume_output.skills)}
        """
        
    prompt = f"""
    You are an expert technical interview coach. Generate a skeleton answer template for the following question.
    
    Question: {input_data.question.text}
    Category: {input_data.question.category}
    Company: {input_data.company}
    Role: {input_data.role}
    
    {resume_context}
    
    Instructions:
    1. If behavioural, use the STAR format.
    2. If technical, use concept + example + trade-off format.
    3. If coding, use clarify + approach + complexity format.
    4. Provide placeholders in [BRACKETS] for the user to fill in.
    
    Return ONLY a valid JSON object matching this schema:
    {{
        "template": "The skeleton template text...",
        "key_points_to_hit": ["point 1", "point 2"],
        "what_to_avoid": ["avoid 1", "avoid 2"],
        "word_count_target": 200
    }}
    """
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        result_json = json.loads(response.choices[0].message.content)
        return AnswerTemplateOutput(**result_json)
    except Exception as e:
        print(f"Answer template LLM error: {e}")
        # Fallback template
        return AnswerTemplateOutput(
            template="In my previous role, I encountered [SITUATION]. My task was to [TASK]. I took action by [ACTION]. As a result, [RESULT].",
            key_points_to_hit=["Clear situation", "Specific action taken"],
            what_to_avoid=["Being too vague"],
            word_count_target=150
        )
