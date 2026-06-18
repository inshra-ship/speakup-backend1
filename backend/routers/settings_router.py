"""
SpeakUp — Settings Routes
Handles: GET /settings, PUT /settings
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, User, UserSettings
from schemas import SettingsUpdate, SettingsResponse
from auth import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's settings."""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()

    if not settings:
        # Create defaults if somehow they don't exist
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


@router.put("", response_model=SettingsResponse)
def update_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update one or many settings at once. Only sent fields are changed."""
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()

    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)

    # Update only the fields that were actually sent
    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return settings
