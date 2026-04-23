from models.database import SessionLocal
from models.user_progress import UserProgress
from models.schemas import ProgressTrackerOutput
from models.feedback import Feedback
from models.question import Question
from pydantic import BaseModel
from datetime import datetime, timedelta

class ProgressTrackerInput(BaseModel):
    user_id: str
    new_judge_output: Feedback
    question: Question
    company: str
    role: str
    trace_id: str

def update(user_id: str, judge_output: Feedback, question: Question, company: str, role: str):
    db = SessionLocal()
    try:
        new_progress = UserProgress(
            user_id=user_id,
            question_id=question.id,
            company=company,
            role=role,
            score=judge_output.score,
            breakdown=judge_output.breakdown.model_dump()
        )
        db.add(new_progress)
        db.commit()
    except Exception as e:
        print(f"Error updating progress: {e}")
        db.rollback()
    finally:
        db.close()

def run_progress_tracker(user_id: str) -> ProgressTrackerOutput:
    db = SessionLocal()
    try:
        # Get all sessions for this user, ordered by created_at desc
        sessions = db.query(UserProgress).filter(UserProgress.user_id == user_id).order_by(UserProgress.created_at.desc()).all()
        sessions_completed = len(sessions)
        
        if sessions_completed == 0:
            return ProgressTrackerOutput(all_time_avg=0.0, trend="stagnating", category_trends={}, sessions_completed=0, streak_days=0, milestone=None)
            
        all_time_avg = sum(s.score for s in sessions) / sessions_completed
        
        last_10 = sessions[:10]
        if len(last_10) >= 4:
            recent_avg = sum(s.score for s in last_10[:3]) / 3
            older_avg = sum(s.score for s in last_10[3:]) / len(last_10[3:])
            delta = recent_avg - older_avg
            if delta > 0.5:
                trend = "improving"
            elif delta < -0.5:
                trend = "declining"
            else:
                trend = "stagnating"
        else:
            trend = "stagnating"
            
        # Calculate streak
        streak_days = 0
        current_date = datetime.utcnow().date()
        date_set = {s.created_at.date() for s in sessions}
        
        while current_date in date_set:
            streak_days += 1
            current_date -= timedelta(days=1)
            
        # Optional: check if yesterday was the last streak day to not break it if they haven't played today yet
        if streak_days == 0 and (datetime.utcnow().date() - timedelta(days=1)) in date_set:
            current_date = datetime.utcnow().date() - timedelta(days=1)
            while current_date in date_set:
                streak_days += 1
                current_date -= timedelta(days=1)
                
        # Milestones
        milestone = None
        if sessions_completed == 10:
            milestone = "10 sessions completed!"
        elif sessions_completed > 0 and sessions[0].score >= 7.0 and (sessions_completed == 1 or sessions[1].score < 7.0):
            milestone = "First 7.0+ score!"
            
        return ProgressTrackerOutput(
            all_time_avg=round(all_time_avg, 1),
            trend=trend,
            category_trends={}, # Simplified for now
            sessions_completed=sessions_completed,
            streak_days=streak_days,
            milestone=milestone
        )
    finally:
        db.close()
