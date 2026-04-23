import os
import json
from typing import Dict, Any, List
from models.session import HistoricalQuestionsOutput
from models.question import Question
from tools.web_search import perform_search
from tools.cache import get_cache, set_cache
from tools.deduplicator import deduplicate_questions
from groq import Groq
import datetime

def execute(company: str, role: str) -> HistoricalQuestionsOutput:
    cache_key = f"historical:{company.lower().replace(' ', '_')}:{role.lower().replace(' ', '_')}"
    cached = get_cache(cache_key)
    if cached:
        return HistoricalQuestionsOutput(**cached)

    current_year = datetime.datetime.now().year
    
    # Fallback search since we don't have direct Glassdoor/Leetcode APIs
    search_q = perform_search(f"{company} {role} interview questions {current_year} glassdoor leetcode blind", max_results=5)
    
    prompt = f"""
    You are an expert technical interviewer.
    Based on the following search results about past interview questions for the role '{role}' at '{company}', extract the questions.
    Categorize them into 'behavioural', 'technical', and 'coding' (DSA/System Design).
    Provide a frequency score (1-5) based on how commonly such questions appear.
    
    Respond with a JSON object with keys: "behavioural", "technical", "coding", and "source".
    Each category key should contain a list of objects with "text", "frequency", "difficulty", "year", and "source".
    "source" at the root should be a list of domain names the questions were found on.
    
    Search Results:
    {json.dumps(search_q)}
    """

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        result_json = json.loads(response.choices[0].message.content)
        
        raw_behavioural = [Question(**q) for q in result_json.get("behavioural", [])]
        raw_technical = [Question(**q) for q in result_json.get("technical", [])]
        raw_coding = [Question(**q) for q in result_json.get("coding", [])]
        
        # Deduplicate
        dedup_b = deduplicate_questions(raw_behavioural, threshold=85)
        dedup_t = deduplicate_questions(raw_technical, threshold=85)
        dedup_c = deduplicate_questions(raw_coding, threshold=85)
        
        # Sort by frequency descending and limit to top 20
        dedup_b = sorted(dedup_b, key=lambda x: x.frequency, reverse=True)[:20]
        dedup_t = sorted(dedup_t, key=lambda x: x.frequency, reverse=True)[:20]
        dedup_c = sorted(dedup_c, key=lambda x: x.frequency, reverse=True)[:20]
        
        output = HistoricalQuestionsOutput(
            behavioural=dedup_b,
            technical=dedup_t,
            coding=dedup_c,
            source=result_json.get("source", ["Web Search Fallback"])
        )
        set_cache(cache_key, output.model_dump(), ttl_seconds=24 * 3600) # 24 hours TTL
        return output
    except Exception as e:
        print(f"Historical Fetcher LLM error: {e}")
        return HistoricalQuestionsOutput(degraded=True)
