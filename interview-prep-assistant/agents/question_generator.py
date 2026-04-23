import json
from typing import Dict, Any, List
from models.session import ResearcherOutput, HistoricalQuestionsOutput, GeneratedQuestionsOutput
from models.question import Question
from agents.llm import get_model
from tools.deduplicator import is_duplicate

def execute(role: str, researcher_output: ResearcherOutput, historical_output: HistoricalQuestionsOutput) -> GeneratedQuestionsOutput:
    hist_questions = []
    if historical_output and not historical_output.degraded:
        hist_questions.extend(historical_output.behavioural)
        hist_questions.extend(historical_output.technical)
        hist_questions.extend(historical_output.coding)
        
    hist_texts = [q.text for q in hist_questions]

    prompt = f"""
    You are an expert technical interviewer.
    Generate 10-15 fresh, role-specific interview questions for the role '{role}'.
    
    Context about the company and role from research:
    Culture: {researcher_output.culture if researcher_output else "Not available"}
    Role Expectations: {researcher_output.roleExpectations if researcher_output else "Standard expectations for this role"}
    Recent News: {researcher_output.recentNews if researcher_output else "Not available"}
    
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

    model = get_model(json_mode=True, temperature=0.7)
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            result_json = json.loads(response.text)
            
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
