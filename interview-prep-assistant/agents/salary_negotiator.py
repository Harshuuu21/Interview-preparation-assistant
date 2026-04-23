import os
import json
from pydantic import BaseModel
from typing import Optional
from models.schemas import SalaryNegotiatorOutput
from tools.web_search import perform_search
from tools.cache import get_cache, set_cache
from groq import Groq

class SalaryNegotiatorInput(BaseModel):
    company: str
    role: str
    location: str
    experience_years: int
    user_expected_salary: Optional[str] = None
    trace_id: str

def run_salary_negotiator(input_data: SalaryNegotiatorInput) -> SalaryNegotiatorOutput:
    cache_key = f"salary:{input_data.company}:{input_data.role}:{input_data.location}"
    cached = get_cache(cache_key)
    if cached:
        return SalaryNegotiatorOutput(**cached)
        
    try:
        q1 = f"{input_data.role} at {input_data.company} {input_data.location} salary levels.fyi glassdoor"
        r1 = perform_search(q1)
        
        prompt = f"""
        You are an expert salary negotiation coach. Analyze the following search results for compensation.
        
        Company: {input_data.company}
        Role: {input_data.role}
        Location: {input_data.location}
        Experience: {input_data.experience_years} years
        User Expectation: {input_data.user_expected_salary or 'Not provided'}
        
        Search Results:
        {r1}
        
        Synthesize the market range and generate 3 negotiation scripts covering:
        1. Offer below expectation
        2. Offer meets expectation but benefits are lacking
        3. Exploding offer pressure
        
        Return ONLY a valid JSON object matching this schema:
        {{
            "market_range": {{"low": "$100k", "mid": "$130k", "high": "$160k"}},
            "company_typical_range": "$120k - $150k",
            "negotiation_scripts": [
                {{"scenario": "Offer below expectation", "suggested_response": "..."}}
            ],
            "dos": ["Do this"],
            "donts": ["Don't do this"],
            "degraded": false
        }}
        """
        
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        result_json = json.loads(response.choices[0].message.content)
        
        output = SalaryNegotiatorOutput(**result_json)
        set_cache(cache_key, output.model_dump(), ttl_seconds=172800) # 48h
        return output
    except Exception as e:
        print(f"Salary negotiator LLM error: {e}")
        return SalaryNegotiatorOutput(degraded=True)
