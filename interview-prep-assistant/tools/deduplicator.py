from thefuzz import fuzz
from typing import List, Dict, Any
from models.question import Question

def is_duplicate(new_text: str, existing_questions: List[Question], threshold: int = 85) -> bool:
    """
    Checks if new_text is a duplicate of any question in existing_questions.
    Uses fuzzy matching. Threshold is out of 100.
    """
    for q in existing_questions:
        ratio = fuzz.token_sort_ratio(new_text.lower(), q.text.lower())
        if ratio >= threshold:
            return True
    return False

def deduplicate_questions(questions: List[Question], threshold: int = 85) -> List[Question]:
    """
    Deduplicates a list of questions.
    Keeps the first occurrence (usually the most frequent if sorted).
    """
    unique_questions = []
    for q in questions:
        if not is_duplicate(q.text, unique_questions, threshold):
            unique_questions.append(q)
    return unique_questions
