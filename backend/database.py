"""
SpeakUp — Database Setup
Uses SQLite (a simple file-based database, zero installation needed!)
The database file 'speakup.db' is created automatically on first run.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./speakup.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── TABLE 1: Users ──────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    email         = Column(String(200), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    level         = Column(String(50), default="beginner")
    goal          = Column(String(200), default="Build general confidence")
    bio           = Column(Text, default="")
    created_at    = Column(DateTime, default=datetime.utcnow)
    is_active     = Column(Boolean, default=True)
    is_admin      = Column(Boolean, default=False)   # ← NEW: admin flag

    sessions    = relationship("PracticeSession",    back_populates="user", cascade="all, delete")
    settings    = relationship("UserSettings",       back_populates="user", uselist=False, cascade="all, delete")
    streaks     = relationship("Streak",             back_populates="user", cascade="all, delete")
    completions = relationship("ScenarioCompletion", back_populates="user", cascade="all, delete")


# ── TABLE 2: Practice Sessions ───────────────────────────────────────────────
class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False)
    scenario_id      = Column(String(100), nullable=False)
    scenario_name    = Column(String(200), nullable=False)
    speech_text      = Column(Text, default="")
    score_overall    = Column(Float, default=0.0)
    score_structure  = Column(Float, default=0.0)
    score_clarity    = Column(Float, default=0.0)
    score_delivery   = Column(Float, default=0.0)
    feedback_json    = Column(Text, default="[]")
    duration_seconds = Column(Integer, default=0)
    word_count       = Column(Integer, default=0)
    created_at       = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")


# ── TABLE 3: Scenario Completions ────────────────────────────────────────────
class ScenarioCompletion(Base):
    __tablename__ = "scenario_completions"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    scenario_id  = Column(String(100), nullable=False)
    best_score   = Column(Float, default=0.0)
    attempts     = Column(Integer, default=1)
    completed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="completions")


# ── TABLE 4: User Settings ───────────────────────────────────────────────────
class UserSettings(Base):
    __tablename__ = "user_settings"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    auto_timer          = Column(Boolean, default=False)
    show_guide          = Column(Boolean, default=True)
    word_count_toggle   = Column(Boolean, default=True)
    session_summary     = Column(Boolean, default=True)
    feedback_depth      = Column(Integer, default=2)
    strictness          = Column(Integer, default=2)
    font_size           = Column(Integer, default=2)
    reduced_motion      = Column(Boolean, default=False)
    email_reminders     = Column(Boolean, default=True)
    email_weekly_report = Column(Boolean, default=True)

    user = relationship("User", back_populates="settings")


# ── TABLE 5: Daily Streaks ───────────────────────────────────────────────────
class Streak(Base):
    __tablename__ = "streaks"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_practice  = Column(DateTime, nullable=True)
    updated_at     = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="streaks")


# ── TABLE 6: Scenarios (admin-managed) ───────────────────────────────────────
class Scenario(Base):
    __tablename__ = "scenarios"

    id          = Column(Integer, primary_key=True, index=True)
    slug        = Column(String(100), unique=True, index=True, nullable=False)  # e.g. "team-meeting"
    title       = Column(String(200), nullable=False)
    description = Column(Text, default="")
    category    = Column(String(100), default="professional")
    difficulty  = Column(String(50), default="Beginner")
    duration    = Column(String(50), default="5 min")
    icon        = Column(String(20), default="&#9711;")
    is_active   = Column(Boolean, default=True)
    is_pro      = Column(Boolean, default=False)   # locked behind Pro plan
    guide_json  = Column(Text, default="[]")        # JSON array of guide steps
    sort_order  = Column(Integer, default=0)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow)


# ── TABLE 7: Categories (admin-managed) ──────────────────────────────────────
class Category(Base):
    __tablename__ = "categories"

    id          = Column(Integer, primary_key=True, index=True)
    slug        = Column(String(100), unique=True, nullable=False)
    name        = Column(String(100), nullable=False)
    description = Column(Text, default="")
    icon        = Column(String(20), default="&#9670;")
    is_active   = Column(Boolean, default=True)
    sort_order  = Column(Integer, default=0)
    created_at  = Column(DateTime, default=datetime.utcnow)


# ── TABLE 8: Site Features / Announcements (admin-managed) ───────────────────
class SiteFeature(Base):
    __tablename__ = "site_features"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    description = Column(Text, default="")
    feature_type = Column(String(50), default="announcement")  # announcement / feature / maintenance
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    expires_at  = Column(DateTime, nullable=True)


# ── TABLE 9: Admin Activity Log ───────────────────────────────────────────────
class AdminLog(Base):
    __tablename__ = "admin_logs"

    id         = Column(Integer, primary_key=True, index=True)
    admin_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    action     = Column(String(200), nullable=False)   # e.g. "Deleted user #42"
    target     = Column(String(200), nullable=True)    # e.g. "user:42"
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
