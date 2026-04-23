import json
from models.feedback import Feedback, FeedbackBreakdown
from agents.llm import get_model

def execute(question: str, user_answer: str, role_context: str, company_context: str, iteration_count: int) -> Feedback:
    prompt = f"""
    You are an expert technical interviewer evaluating a candidate's answer.
    
    Question: {question}
    Candidate's Answer: {user_answer}
    
    Role Context: {role_context}
    Company Context: {company_context}
    
    Evaluate the answer based on these criteria (score 0-10):
    - clarity: How clear and articulate is the answer?
    - depth: Does it show deep understanding or just surface level?
    - relevance: Does it actually answer the question asked?
    - starFormat: How well does it follow Situation, Task, Action, Result (if applicable)?
    - roleFit: Does this answer demonstrate fitness for the specific role?
    
    Provide the overall score as an average of these.
    Also identify "gaps" (what is missing), an "improvedAnswer" (a rewritten, excellent version of their answer), and "tips" (2-3 actionable suggestions).
    
    Respond in JSON format exactly matching this structure:
    {{
        "score": 8.5,
        "breakdown": {{
            "clarity": 8.0,
            "depth": 9.0,
            "relevance": 8.5,
            "starFormat": 7.0,
            "roleFit": 9.0
        }},
        "gaps": ["Did not mention specific metrics"],
        "improvedAnswer": "Here is how I would answer...",
        "tips": ["Quantify your results"]
    }}
    """

    model = get_model(json_mode=True, temperature=0.3)
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            result_json = json.loads(response.text)
            
            return Feedback(
                score=result_json.get("score", 0),
                breakdown=FeedbackBreakdown(**result_json.get("breakdown", {})),
                gaps=result_json.get("gaps", []),
                improvedAnswer=result_json.get("improvedAnswer", ""),
                tips=result_json.get("tips", [])
            )
        except Exception as e:
            print(f"Judge LLM error on attempt {attempt}: {e}")
            if attempt == max_retries - 1:
                # Return generic fallback on total failure
                return Feedback(
                    score=0,
                    breakdown=FeedbackBreakdown(clarity=0, depth=0, relevance=0, starFormat=0, roleFit=0),
                    gaps=["Error evaluating answer"],
                    improvedAnswer="Error evaluating answer.",
                    tips=["Please try again."]
                )
