"""
SpeakUp — Main Backend Server
Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, SessionLocal, User, UserSettings, Streak
from auth import hash_password
from routers.auth_router import router as auth_router
from routers.users_router import router as users_router
from routers.sessions_router import router as sessions_router
from routers.settings_router import router as settings_router
from routers.admin_router import router as admin_router

app = FastAPI(
    title="SpeakUp API",
    description="Backend for the SpeakUp public speaking simulator",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(sessions_router)
app.include_router(settings_router)
app.include_router(admin_router)   # ← admin routes, all protected server-side


def seed_admin():
    """Create the default admin account if it doesn't exist yet."""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "admin@speakup.com").first()
        if not existing:
            admin = User(
                name="Admin",
                email="admin@speakup.com",
                password_hash=hash_password("admin1234"),
                level="advanced",
                is_admin=True,
                is_active=True
            )
            db.add(admin)
            db.flush()
            db.add(UserSettings(user_id=admin.id))
            db.add(Streak(user_id=admin.id))
            db.commit()
            print("👤 Default admin created — email: admin@speakup.com  password: admin1234")
            print("   ⚠️  Change this password immediately in production!")
        else:
            print("👤 Admin account already exists.")
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    init_db()
    seed_admin()
    print("🚀 SpeakUp API is running!")
    print("📖 Docs: http://localhost:8000/docs")


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "SpeakUp API is running!"}
