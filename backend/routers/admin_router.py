"""
SpeakUp — Admin Routes
ALL routes here require is_admin=True on the user.
Normal users get 403 Forbidden on every single endpoint.

Prefix: /admin
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

from database import (
    get_db, User, PracticeSession, Scenario, Category,
    SiteFeature, AdminLog, UserSettings, Streak
)
from auth import get_current_admin, hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])


# ═══════════════════════════════════════════════════════════════
# SCHEMAS (request / response models for admin endpoints)
# ═══════════════════════════════════════════════════════════════

class UserAdminView(BaseModel):
    id: int
    name: str
    email: str
    level: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    session_count: int = 0
    class Config: from_attributes = True

class UserStatusUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    level: Optional[str] = None

class ScenarioCreate(BaseModel):
    slug: str
    title: str
    description: str
    category: str
    difficulty: str
    duration: str
    icon: Optional[str] = "&#9711;"
    is_pro: Optional[bool] = False
    guide_json: Optional[str] = "[]"
    sort_order: Optional[int] = 0

class ScenarioUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    duration: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    is_pro: Optional[bool] = None
    guide_json: Optional[str] = None
    sort_order: Optional[int] = None

class ScenarioOut(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    category: str
    difficulty: str
    duration: str
    icon: str
    is_active: bool
    is_pro: bool
    guide_json: str
    sort_order: int
    created_at: datetime
    class Config: from_attributes = True

class CategoryCreate(BaseModel):
    slug: str
    name: str
    description: Optional[str] = ""
    icon: Optional[str] = "&#9670;"
    sort_order: Optional[int] = 0

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class CategoryOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    icon: str
    is_active: bool
    sort_order: int
    class Config: from_attributes = True

class FeatureCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    feature_type: Optional[str] = "announcement"
    expires_at: Optional[datetime] = None

class FeatureUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    feature_type: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None

class FeatureOut(BaseModel):
    id: int
    title: str
    description: str
    feature_type: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    class Config: from_attributes = True

class AdminLogOut(BaseModel):
    id: int
    admin_id: int
    action: str
    target: Optional[str]
    created_at: datetime
    class Config: from_attributes = True

class SiteSummary(BaseModel):
    total_users: int
    active_users: int
    total_sessions: int
    total_scenarios: int
    total_categories: int
    new_users_today: int
    sessions_today: int
    avg_score_all_time: float


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def log_action(db: Session, admin: User, action: str, target: str = None):
    """Write an entry to the admin activity log."""
    entry = AdminLog(admin_id=admin.id, action=action, target=target)
    db.add(entry)
    # don't commit here — let the caller commit


# ═══════════════════════════════════════════════════════════════
# DASHBOARD — summary stats
# ═══════════════════════════════════════════════════════════════

@router.get("/dashboard", response_model=SiteSummary)
def admin_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """High-level site stats for the admin dashboard."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    total_users    = db.query(func.count(User.id)).scalar() or 0
    active_users   = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    total_sessions = db.query(func.count(PracticeSession.id)).scalar() or 0
    total_scenarios = db.query(func.count(Scenario.id)).scalar() or 0
    total_categories = db.query(func.count(Category.id)).scalar() or 0

    new_users_today = db.query(func.count(User.id)).filter(
        User.created_at >= today_start
    ).scalar() or 0

    sessions_today = db.query(func.count(PracticeSession.id)).filter(
        PracticeSession.created_at >= today_start
    ).scalar() or 0

    avg_score = db.query(func.avg(PracticeSession.score_overall)).scalar() or 0.0

    return SiteSummary(
        total_users=total_users,
        active_users=active_users,
        total_sessions=total_sessions,
        total_scenarios=total_scenarios,
        total_categories=total_categories,
        new_users_today=new_users_today,
        sessions_today=sessions_today,
        avg_score_all_time=round(avg_score, 1)
    )


# ═══════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@router.get("/users", response_model=List[UserAdminView])
def list_users(
    search: str = "",
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """List all users with their session counts. Supports search by name/email."""
    query = db.query(User)
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    result = []
    for u in users:
        count = db.query(func.count(PracticeSession.id)).filter(
            PracticeSession.user_id == u.id
        ).scalar() or 0
        result.append(UserAdminView(
            id=u.id, name=u.name, email=u.email, level=u.level,
            is_active=u.is_active, is_admin=u.is_admin,
            created_at=u.created_at, session_count=count
        ))
    return result


@router.patch("/users/{user_id}", response_model=UserAdminView)
def update_user(
    user_id: int,
    data: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Toggle a user's active status, admin flag, or level."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot modify your own admin account here.")

    changes = []
    if data.is_active is not None:
        user.is_active = data.is_active
        changes.append(f"set is_active={data.is_active}")
    if data.is_admin is not None:
        user.is_admin = data.is_admin
        changes.append(f"set is_admin={data.is_admin}")
    if data.level is not None:
        user.level = data.level
        changes.append(f"set level={data.level}")

    log_action(db, admin, f"Updated user: {', '.join(changes)}", f"user:{user_id}")
    db.commit()
    db.refresh(user)

    count = db.query(func.count(PracticeSession.id)).filter(
        PracticeSession.user_id == user.id
    ).scalar() or 0
    return UserAdminView(
        id=user.id, name=user.name, email=user.email, level=user.level,
        is_active=user.is_active, is_admin=user.is_admin,
        created_at=user.created_at, session_count=count
    )


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Permanently delete a user and all their data."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account from here.")

    log_action(db, admin, f"Deleted user: {user.name} ({user.email})", f"user:{user_id}")
    db.delete(user)
    db.commit()
    return None


# ═══════════════════════════════════════════════════════════════
# SCENARIO MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@router.get("/scenarios", response_model=List[ScenarioOut])
def list_scenarios(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(Scenario).order_by(Scenario.sort_order, Scenario.created_at).all()


@router.post("/scenarios", response_model=ScenarioOut, status_code=201)
def create_scenario(
    data: ScenarioCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    if db.query(Scenario).filter(Scenario.slug == data.slug).first():
        raise HTTPException(status_code=400, detail=f"Slug '{data.slug}' already exists.")

    s = Scenario(**data.model_dump())
    db.add(s)
    log_action(db, admin, f"Created scenario: {data.title}", f"scenario:{data.slug}")
    db.commit()
    db.refresh(s)
    return s


@router.patch("/scenarios/{scenario_id}", response_model=ScenarioOut)
def update_scenario(
    scenario_id: int,
    data: ScenarioUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    s = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found.")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(s, field, value)
    s.updated_at = datetime.utcnow()

    log_action(db, admin, f"Updated scenario: {s.title}", f"scenario:{scenario_id}")
    db.commit()
    db.refresh(s)
    return s


@router.delete("/scenarios/{scenario_id}", status_code=204)
def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    s = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    log_action(db, admin, f"Deleted scenario: {s.title}", f"scenario:{scenario_id}")
    db.delete(s)
    db.commit()
    return None


# ═══════════════════════════════════════════════════════════════
# CATEGORY MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@router.get("/categories", response_model=List[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(Category).order_by(Category.sort_order).all()


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    if db.query(Category).filter(Category.slug == data.slug).first():
        raise HTTPException(status_code=400, detail=f"Slug '{data.slug}' already exists.")
    c = Category(**data.model_dump())
    db.add(c)
    log_action(db, admin, f"Created category: {data.name}", f"category:{data.slug}")
    db.commit()
    db.refresh(c)
    return c


@router.patch("/categories/{cat_id}", response_model=CategoryOut)
def update_category(
    cat_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    c = db.query(Category).filter(Category.id == cat_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Category not found.")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(c, field, value)
    log_action(db, admin, f"Updated category: {c.name}", f"category:{cat_id}")
    db.commit()
    db.refresh(c)
    return c


@router.delete("/categories/{cat_id}", status_code=204)
def delete_category(
    cat_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    c = db.query(Category).filter(Category.id == cat_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Category not found.")
    log_action(db, admin, f"Deleted category: {c.name}", f"category:{cat_id}")
    db.delete(c)
    db.commit()
    return None


# ═══════════════════════════════════════════════════════════════
# SITE FEATURES / ANNOUNCEMENTS
# ═══════════════════════════════════════════════════════════════

@router.get("/features", response_model=List[FeatureOut])
def list_features(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(SiteFeature).order_by(SiteFeature.created_at.desc()).all()


@router.post("/features", response_model=FeatureOut, status_code=201)
def create_feature(
    data: FeatureCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    f = SiteFeature(**data.model_dump())
    db.add(f)
    log_action(db, admin, f"Created feature/announcement: {data.title}", "feature")
    db.commit()
    db.refresh(f)
    return f


@router.patch("/features/{feature_id}", response_model=FeatureOut)
def update_feature(
    feature_id: int,
    data: FeatureUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    f = db.query(SiteFeature).filter(SiteFeature.id == feature_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Feature not found.")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(f, field, value)
    log_action(db, admin, f"Updated feature: {f.title}", f"feature:{feature_id}")
    db.commit()
    db.refresh(f)
    return f


@router.delete("/features/{feature_id}", status_code=204)
def delete_feature(
    feature_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    f = db.query(SiteFeature).filter(SiteFeature.id == feature_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Feature not found.")
    log_action(db, admin, f"Deleted feature: {f.title}", f"feature:{feature_id}")
    db.delete(f)
    db.commit()
    return None


# ═══════════════════════════════════════════════════════════════
# ACTIVITY LOG
# ═══════════════════════════════════════════════════════════════

@router.get("/logs", response_model=List[AdminLogOut])
def get_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(AdminLog).order_by(AdminLog.created_at.desc()).limit(limit).all()
