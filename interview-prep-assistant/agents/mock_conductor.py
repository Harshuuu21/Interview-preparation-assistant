import json
import os
from pydantic import BaseModel
from typing import List, Dict, Optional
from models.schemas import MockConductorOutput
from models.question import Question
from groq import Groq

class MockConductorInput(BaseModel):
    session_id: str
    company: str
    question: Question
    user_answer: str
    conversation_history: List[Dict[str, str]]
    difficulty_level: int
    trace_id: str

def run_mock_conductor(input_data: MockConductorInput) -> MockConductorOutput:
    turn_count = len(input_data.conversation_history) // 2 + 1
    
    # Simple heuristic to save tokens
    if len(input_data.user_answer.split()) < 30 and turn_count < 3:
        return MockConductorOutput(
            follow_up_question="Could you elaborate on that?",
            interviewer_reaction="I see.",
            should_move_on=False,
            adjusted_difficulty=max(1, input_data.difficulty_level - 1),
            turn_count=turn_count
        )
        
    if turn_count >= 4:
        return MockConductorOutput(
            follow_up_question=None,
            interviewer_reaction="Thank you, that gives me a good understanding.",
            should_move_on=True,
            adjusted_difficulty=input_data.difficulty_level,
            turn_count=turn_count
        )
        
    # Heuristic for difficulty
    adjusted_diff = input_data.difficulty_level
    word_count = len(input_data.user_answer.split())
    if word_count > 80 and any(char.isdigit() for char in input_data.user_answer):
        adjusted_diff = min(5, adjusted_diff + 1)
    elif word_count < 40:
        adjusted_diff = max(1, adjusted_diff - 1)
        
    history_context = ""
    for msg in input_data.conversation_history[-4:]: # Only last 4 messages for context window
        history_context += f"{msg['role'].capitalize()}: {msg['content']}\n"
        
    prompt = f"""
    You are a senior interviewer at {input_data.company}. We are doing a mock interview.
    Original Question: {input_data.question.text}
    
    Conversation History:
    {history_context}
    
    Candidate's Latest Answer:
    {input_data.user_answer}
    
    Current Difficulty Level (1-5): {adjusted_diff}
    
    Ask a natural follow-up question based on the candidate's answer. Do NOT give feedback yet.
    Keep the interviewer reaction short (e.g. "Interesting, tell me more about...").
    If the topic is sufficiently covered, set should_move_on to true and follow_up_question to null.
    
    Return ONLY a valid JSON object matching this schema:
    {{
        "follow_up_question": "Your follow up question here",
        "interviewer_reaction": "Ah, that makes sense.",
        "should_move_on": false,
        "adjusted_difficulty": {adjusted_diff},
        "turn_count": {turn_count}
    }}
    """
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        result_json = json.loads(response.choices[0].message.content)
        return MockConductorOutput(**result_json)
    except Exception as e:
        print(f"Mock conductor LLM error: {e}")
        return MockConductorOutput(
            follow_up_question=None,
            interviewer_reaction="Let's move on to the next topic.",
            should_move_on=True,
            adjusted_difficulty=adjusted_diff,
            turn_count=turn_count
        )
