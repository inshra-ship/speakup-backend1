"""
SpeakUp — Auth Routes
Handles: POST /auth/signup, POST /auth/login, GET /auth/verify
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, User, UserSettings, Streak
from schemas import SignupRequest, LoginRequest, TokenResponse
from auth import hash_password, verify_password, create_access_token
from email_utils import generate_token, send_verification_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Try logging in instead."
        )

    # Create the user
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        level=data.level or "beginner",
        goal=data.goal or "Build general confidence",
        is_verified=False
    )
    db.add(user)
    db.flush()

    # Create default settings and streak
    db.add(UserSettings(user_id=user.id))
    db.add(Streak(user_id=user.id, current_streak=0, longest_streak=0))

    # Generate email verification token
    verify_token = generate_token()
    user.verify_token = verify_token

    db.commit()
    db.refresh(user)

    # Send verification email (non-blocking — if it fails, signup still works)
    send_verification_email(data.email, data.name, verify_token)

    # Return JWT so user is logged in immediately
    access_token = create_access_token(user.id, user.email)
    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "level": user.level
        }
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated."
        )

    token = create_access_token(user.id, user.email)
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "level": user.level
        }
    )


@router.get("/verify")
def verify_email(token: str, db: Session = Depends(get_db)):
    """Called when user clicks the link in their email."""
    user = db.query(User).filter(User.verify_token == token).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification link."
        )

    user.is_verified = True
    user.verify_token = None
    db.commit()

    return {"message": "Email verified successfully! You can now log in."}
