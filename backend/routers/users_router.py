"""
SpeakUp — User Routes
Handles: GET /users/me, PUT /users/me, DELETE /users/me
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, User
from schemas import UserResponse, UserUpdate
from auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Return the logged-in user's profile data."""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update profile fields. Only sends fields that were changed."""
    if data.name is not None:
        current_user.name = data.name
    if data.level is not None:
        current_user.level = data.level
    if data.goal is not None:
        current_user.goal = data.goal
    if data.bio is not None:
        current_user.bio = data.bio

    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=204)
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permanently delete the user's account and all their data."""
    db.delete(current_user)
    db.commit()
    return None
