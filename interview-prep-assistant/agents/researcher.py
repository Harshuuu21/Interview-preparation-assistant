import json
from typing import Dict, Any, List
from models.session import ResearcherOutput
from tools.web_search import perform_search
from tools.cache import get_cache, set_cache
from agents.llm import get_model

def execute(company: str, role: str) -> ResearcherOutput:
    cache_key = f"researcher:{company.lower().replace(' ', '_')}:{role.lower().replace(' ', '_')}"
    cached = get_cache(cache_key)
    if cached:
        return ResearcherOutput(**cached)

    culture_search = perform_search(f"{company} company culture values", max_results=3)
    expectations_search = perform_search(f"{company} {role} job expectations requirements", max_results=3)
    news_search = perform_search(f"{company} recent news 2024", max_results=3)

    search_context = f"""
    Culture Search Results:
    {json.dumps(culture_search)}
    
    Role Expectations Search Results:
    {json.dumps(expectations_search)}
    
    News Search Results:
    {json.dumps(news_search)}
    """

    prompt = f"""
    You are an expert tech recruiter and researcher. 
    Based on the following web search results for the company '{company}' and the role '{role}', extract and synthesize the information into exactly three lists:
    1. culture: Company values, work style, notable culture signals.
    2. recentNews: Recent news relevant to the company or role (last 6 months).
    3. roleExpectations: Typical responsibilities and required skills for the role '{role}'.
    
    Filter the search results for recency and relevance (keep only points you'd score >= 3 out of 5).
    
    Return the response as a JSON object with exactly the keys: "culture", "recentNews", "roleExpectations", each containing a list of strings.
    
    Search Context:
    {search_context}
    """

    model = get_model(json_mode=True, temperature=0.2)
    try:
        response = model.generate_content(prompt)
        result_json = json.loads(response.text)
        output = ResearcherOutput(
            culture=result_json.get("culture", []),
            recentNews=result_json.get("recentNews", []),
            roleExpectations=result_json.get("roleExpectations", [])
        )
        set_cache(cache_key, output.model_dump(), 6 * 3600) # 6 hours TTL
        return output
    except Exception as e:
        print(f"Researcher LLM error: {e}")
        return ResearcherOutput(degraded=True)
