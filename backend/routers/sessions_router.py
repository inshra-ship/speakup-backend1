"""
SpeakUp — Practice Session Routes
Handles: POST /sessions, GET /sessions, GET /sessions/dashboard
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, date
from database import get_db, User, PracticeSession, ScenarioCompletion, Streak
from schemas import SessionCreate, SessionResponse, DashboardStats
from auth import get_current_user

router = APIRouter(prefix="/sessions", tags=["Practice Sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
def save_session(
    data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save a completed practice session.
    Also updates the user's streak and scenario completion record.
    """
    # Save the session
    session = PracticeSession(
        user_id=current_user.id,
        scenario_id=data.scenario_id,
        scenario_name=data.scenario_name,
        speech_text=data.speech_text,
        score_overall=data.score_overall,
        score_structure=data.score_structure,
        score_clarity=data.score_clarity,
        score_delivery=data.score_delivery,
        feedback_json=data.feedback_json,
        duration_seconds=data.duration_seconds,
        word_count=data.word_count
    )
    db.add(session)

    # Update or create scenario completion record
    completion = db.query(ScenarioCompletion).filter(
        ScenarioCompletion.user_id == current_user.id,
        ScenarioCompletion.scenario_id == data.scenario_id
    ).first()

    if completion:
        completion.attempts += 1
        if data.score_overall > completion.best_score:
            completion.best_score = data.score_overall
    else:
        completion = ScenarioCompletion(
            user_id=current_user.id,
            scenario_id=data.scenario_id,
            best_score=data.score_overall,
            attempts=1
        )
        db.add(completion)

    # Update streak
    streak_record = db.query(Streak).filter(Streak.user_id == current_user.id).first()
    if streak_record:
        today = date.today()
        last = streak_record.last_practice
        if last is None or last.date() < today:
            # First practice today — increment streak
            if last and (today - last.date()).days == 1:
                streak_record.current_streak += 1
            elif last and (today - last.date()).days > 1:
                streak_record.current_streak = 1  # streak broken
            else:
                streak_record.current_streak = max(1, streak_record.current_streak)
            streak_record.last_practice = datetime.utcnow()
            streak_record.longest_streak = max(
                streak_record.longest_streak,
                streak_record.current_streak
            )
            streak_record.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=List[SessionResponse])
def get_my_sessions(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the user's practice history, newest first."""
    sessions = db.query(PracticeSession).filter(
        PracticeSession.user_id == current_user.id
    ).order_by(
        PracticeSession.created_at.desc()
    ).offset(offset).limit(limit).all()

    return sessions


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    All the stats needed for the dashboard page in one request:
    - total sessions, average score, current streak, scenarios completed
    - 5 most recent sessions
    """
    # Count total sessions
    total = db.query(func.count(PracticeSession.id)).filter(
        PracticeSession.user_id == current_user.id
    ).scalar() or 0

    # Average score
    avg = db.query(func.avg(PracticeSession.score_overall)).filter(
        PracticeSession.user_id == current_user.id
    ).scalar() or 0.0

    # Current streak
    streak_record = db.query(Streak).filter(Streak.user_id == current_user.id).first()
    current_streak = streak_record.current_streak if streak_record else 0

    # Number of unique scenarios completed
    scenarios_done = db.query(func.count(ScenarioCompletion.id)).filter(
        ScenarioCompletion.user_id == current_user.id
    ).scalar() or 0

    # 5 most recent sessions
    recent = db.query(PracticeSession).filter(
        PracticeSession.user_id == current_user.id
    ).order_by(PracticeSession.created_at.desc()).limit(5).all()

    return DashboardStats(
        total_sessions=total,
        avg_score=round(avg, 1),
        current_streak=current_streak,
        scenarios_completed=scenarios_done,
        recent_sessions=recent
    )


@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific session (only the owner can do this)."""
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    db.delete(session)
    db.commit()
    return None
