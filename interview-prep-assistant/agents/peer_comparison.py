from models.database import SessionLocal
from models.peer_scores import PeerScore
from models.schemas import PeerComparisonOutput
from models.feedback import Feedback, FeedbackBreakdown
from sqlalchemy.sql import func
from pydantic import BaseModel

class PeerComparisonInput(BaseModel):
    question_id: str
    company: str
    role: str
    user_score: float
    user_breakdown: dict
    trace_id: str

def record_score(question_id: str, company: str, role: str, judge_output: Feedback):
    db = SessionLocal()
    try:
        new_score = PeerScore(
            question_id=question_id,
            company=company,
            role=role,
            score=judge_output.score,
            breakdown=judge_output.breakdown.model_dump()
        )
        db.add(new_score)
        db.commit()
    except Exception as e:
        print(f"Error recording peer score: {e}")
        db.rollback()
    finally:
        db.close()

def run_peer_comparison(input_data: PeerComparisonInput) -> PeerComparisonOutput:
    db = SessionLocal()
    try:
        scores = db.query(PeerScore).filter(
            PeerScore.question_id == input_data.question_id,
            PeerScore.company == input_data.company,
            PeerScore.role == input_data.role
        ).all()
        
        total_count = len(scores)
        if total_count < 5:
            return PeerComparisonOutput(
                percentile=None,
                avg_score=None,
                avg_breakdown=None,
                sample_size=total_count,
                top_gap=None,
                insufficient_data=True
            )
            
        lower_scores_count = sum(1 for s in scores if s.score < input_data.user_score)
        percentile = int((lower_scores_count / total_count) * 100)
        
        avg_score = sum(s.score for s in scores) / total_count
        
        # Calculate avg breakdown
        avg_breakdown_dict = {"clarity": 0, "depth": 0, "relevance": 0, "starFormat": 0, "roleFit": 0}
        for s in scores:
            for k in avg_breakdown_dict.keys():
                avg_breakdown_dict[k] += s.breakdown.get(k, 0)
                
        for k in avg_breakdown_dict.keys():
            avg_breakdown_dict[k] /= total_count
            
        # Find top gap
        top_gap = None
        max_gap = -999
        for k in avg_breakdown_dict.keys():
            gap = avg_breakdown_dict[k] - input_data.user_breakdown.get(k, 0)
            if gap > max_gap:
                max_gap = gap
                top_gap = k
                
        return PeerComparisonOutput(
            percentile=percentile,
            avg_score=round(avg_score, 1),
            avg_breakdown=FeedbackBreakdown(**avg_breakdown_dict),
            sample_size=total_count,
            top_gap=top_gap,
            insufficient_data=False
        )
    finally:
        db.close()
