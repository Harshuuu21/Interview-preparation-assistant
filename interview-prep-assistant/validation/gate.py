from models.session import ResearcherOutput, HistoricalQuestionsOutput, GeneratedQuestionsOutput
from tools.deduplicator import is_duplicate
from typing import Tuple, List
from models.question import Question

def validate_researcher(output: ResearcherOutput) -> bool:
    if output.degraded: return False
    non_empty_fields = 0
    if output.culture: non_empty_fields += 1
    if output.recentNews: non_empty_fields += 1
    if output.roleExpectations: non_empty_fields += 1
    return non_empty_fields >= 2

def validate_questions(historical: HistoricalQuestionsOutput, generated: GeneratedQuestionsOutput) -> Tuple[bool, List[Question], str]:
    all_questions = []
    
    if historical and not historical.degraded:
        all_questions.extend(historical.behavioural)
        all_questions.extend(historical.technical)
        all_questions.extend(historical.coding)
        
    if generated and not generated.degraded:
        all_questions.extend(generated.generated)
        
    if len(all_questions) < 5:
        return False, [], "Less than 5 questions total."
        
    # Check for duplicates across the final merged set
    unique_questions = []
    for q in all_questions:
        if not is_duplicate(q.text, unique_questions, threshold=85):
            unique_questions.append(q)
            
    if len(unique_questions) < 5:
        return False, [], "Less than 5 unique questions after deduplication."
        
    return True, unique_questions, ""
