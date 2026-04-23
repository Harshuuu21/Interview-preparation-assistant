import os
import json
from pydantic import BaseModel
from models.schemas import CompanyInsiderOutput
from tools.web_search import perform_search
from tools.cache import get_cache, set_cache
from groq import Groq

class CompanyInsiderInput(BaseModel):
    company: str
    role: str
    trace_id: str

def run_company_insider(input_data: CompanyInsiderInput) -> CompanyInsiderOutput:
    cache_key = f"insider:{input_data.company}:{input_data.role}"
    cached = get_cache(cache_key)
    if cached:
        return CompanyInsiderOutput(**cached)
        
    try:
        # Perform searches
        q1 = f"{input_data.company} interview process {input_data.role}"
        q2 = f"{input_data.company} interview experience Glassdoor"
        q3 = f"{input_data.company} interview tips Reddit"
        
        r1 = perform_search(q1)
        r2 = perform_search(q2)
        r3 = perform_search(q3)
        
        search_context = f"Process Info:\n{r1}\n\nExperiences:\n{r2}\n\nTips:\n{r3}"
        
        prompt = f"""
        You are an expert tech career coach. Analyze the following search results about interviewing for a {input_data.role} role at {input_data.company}.
        
        Search Results:
        {search_context}
        
        Synthesize the information into a structured summary.
        Return ONLY a valid JSON object matching this schema:
        {{
            "interview_process": ["stage 1", "stage 2"],
            "known_focus_areas": ["focus 1", "focus 2"],
            "common_mistakes": ["mistake 1", "mistake 2"],
            "culture_signals": ["signal 1", "signal 2"],
            "insider_tips": ["tip 1", "tip 2"]
        }}
        """
        
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        result_json = json.loads(response.choices[0].message.content)
        
        output = CompanyInsiderOutput(**result_json)
        set_cache(cache_key, output.model_dump(), ttl_seconds=43200) # 12h
        return output
    except Exception as e:
        print(f"Company insider LLM error: {e}")
        return CompanyInsiderOutput(degraded=True)
