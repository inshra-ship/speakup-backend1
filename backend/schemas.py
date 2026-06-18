"""
SpeakUp — Schemas (Data Validation)
These classes define what data the API expects to receive and send back.
Think of them as contracts between the frontend and backend.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ── Auth Schemas ─────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    level: Optional[str] = "beginner"
    goal: Optional[str] = "Build general confidence"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict  # basic user info to store in frontend


# ── User Schemas ──────────────────────────────────────────────────────────────

class UserUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None
    goal: Optional[str] = None
    bio: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    level: str
    goal: str
    bio: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Practice Session Schemas ──────────────────────────────────────────────────

class SessionCreate(BaseModel):
    scenario_id: str
    scenario_name: str
    speech_text: str
    score_overall: float
    score_structure: float
    score_clarity: float
    score_delivery: float
    feedback_json: Optional[str] = "[]"
    duration_seconds: Optional[int] = 0
    word_count: Optional[int] = 0

class SessionResponse(BaseModel):
    id: int
    scenario_id: str
    scenario_name: str
    score_overall: float
    score_structure: float
    score_clarity: float
    score_delivery: float
    feedback_json: str
    duration_seconds: int
    word_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Stats Schema (for dashboard) ──────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_sessions: int
    avg_score: float
    current_streak: int
    scenarios_completed: int
    recent_sessions: List[SessionResponse]


# ── Settings Schema ───────────────────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    auto_timer: Optional[bool] = None
    show_guide: Optional[bool] = None
    word_count_toggle: Optional[bool] = None
    session_summary: Optional[bool] = None
    feedback_depth: Optional[int] = None
    strictness: Optional[int] = None
    font_size: Optional[int] = None
    reduced_motion: Optional[bool] = None
    email_reminders: Optional[bool] = None
    email_weekly_report: Optional[bool] = None

class SettingsResponse(BaseModel):
    auto_timer: bool
    show_guide: bool
    word_count_toggle: bool
    session_summary: bool
    feedback_depth: int
    strictness: int
    font_size: int
    reduced_motion: bool
    email_reminders: bool
    email_weekly_report: bool

    class Config:
        from_attributes = True
