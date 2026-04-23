import os
import json
from pydantic import BaseModel
from typing import List, Optional
from models.schemas import RoadmapAgentOutput, ResumeParserOutput
from models.feedback import Feedback
from tools.cache import get_cache, set_cache
import hashlib
from groq import Groq

class RoadmapInput(BaseModel):
    judge_outputs: List[Feedback]
    resume_output: Optional[ResumeParserOutput] = None
    company: str
    role: str
    days_until_interview: Optional[int] = None
    trace_id: str

def run_roadmap(input_data: RoadmapInput) -> RoadmapAgentOutput:
    if not input_data.judge_outputs:
        return RoadmapAgentOutput()
        
    last_score = input_data.judge_outputs[-1].score
    # Hash session + score for caching
    cache_str = f"{input_data.trace_id}:{last_score}"
    cache_key = "roadmap:" + hashlib.md5(cache_str.encode()).hexdigest()
    
    cached = get_cache(cache_key)
    if cached:
        return RoadmapAgentOutput(**cached)
        
    # Compile judge output summaries
    feedbacks = []
    for idx, j in enumerate(input_data.judge_outputs):
        feedbacks.append(f"Answer {idx+1} Score: {j.score}, Gaps: {j.gaps}, Breakdown: {j.breakdown.model_dump()}")
        
    feedback_context = "\n".join(feedbacks)
    days = input_data.days_until_interview or 7
    
    prompt = f"""
    You are an expert technical interview coach. Generate a {days}-day study roadmap based on the user's interview performance gaps.
    
    Company: {input_data.company}
    Role: {input_data.role}
    
    Performance Feedback:
    {feedback_context}
    
    Based on the lowest breakdown scores, map them to topics (e.g. low clarity -> "communication", low depth -> "domain knowledge").
    Distribute the roadmap across {days} days, front-loading the weakest areas.
    
    Return ONLY a valid JSON object matching this schema:
    {{
        "weak_areas": ["area 1", "area 2"],
        "roadmap": [
            {{
                "day": 1,
                "topic": "STAR method practice",
                "action": "Practice 2 STAR answers on leadership",
                "resource_type": "practice",
                "estimated_minutes": 30
            }}
        ],
        "estimated_hours": 10,
        "priority_questions": ["question_id_1"]
    }}
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
        output = RoadmapAgentOutput(**result_json)
        set_cache(cache_key, output.model_dump(), ttl_seconds=21600) # 6h
        return output
    except Exception as e:
        print(f"Roadmap LLM error: {e}")
        return RoadmapAgentOutput()
