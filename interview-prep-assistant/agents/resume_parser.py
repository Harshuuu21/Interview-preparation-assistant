import os
import fitz
import json
from pydantic import BaseModel
from models.schemas import ResumeParserOutput
from tools.cache import get_cache, set_cache
import hashlib
from groq import Groq

class ResumeParserInput(BaseModel):
    resume_text: str = ""
    resume_path: str = ""
    role: str
    company: str
    trace_id: str

def run_resume_parser(input_data: ResumeParserInput) -> ResumeParserOutput:
    text_to_parse = input_data.resume_text
    
    if input_data.resume_path and not text_to_parse:
        try:
            doc = fitz.open(input_data.resume_path)
            for page in doc:
                text_to_parse += page.get_text()
        except Exception as e:
            print(f"Error reading PDF: {e}")
            
    if not text_to_parse:
        return ResumeParserOutput(degraded=True)
        
    cache_key = "resume:" + hashlib.md5((text_to_parse + input_data.role).encode()).hexdigest()
    cached = get_cache(cache_key)
    if cached:
        return ResumeParserOutput(**cached)
        
    prompt = f"""
    You are an expert technical recruiter and resume parser.
    Extract the following structured information from the resume text below for a {input_data.role} role at {input_data.company}.
    
    Resume Text:
    {text_to_parse}
    
    Return ONLY a valid JSON object matching this schema:
    {{
        "skills": ["skill1", "skill2"],
        "experience_years": 5,
        "past_roles": ["role1", "role2"],
        "projects": ["project1"],
        "education": "degree details",
        "gaps": ["missing skill 1"],
        "resume_summary": "2-3 sentence summary"
    }}
    """
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        result_json = json.loads(response.choices[0].message.content)
        output = ResumeParserOutput(**result_json)
        set_cache(cache_key, output.model_dump(), ttl_seconds=43200) # 12h
        return output
    except Exception as e:
        print(f"Resume parser LLM error: {e}")
        # Retry once
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            result_json = json.loads(response.choices[0].message.content)
            output = ResumeParserOutput(**result_json)
            set_cache(cache_key, output.model_dump(), ttl_seconds=43200)
            return output
        except Exception as retry_e:
            print(f"Resume parser LLM retry error: {retry_e}")
            return ResumeParserOutput(degraded=True)
