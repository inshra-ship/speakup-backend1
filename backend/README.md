# SpeakUp Backend — Setup Guide

## What's in this folder?

```
speakup-backend/
├── main.py              ← Entry point — start the server from here
├── database.py          ← Database tables (Users, Sessions, Settings, Streaks)
├── schemas.py           ← Data validation (what the API expects/returns)
├── auth.py              ← JWT tokens & password hashing
├── requirements.txt     ← Python packages to install
├── api.js               ← Frontend connector — add this to all HTML pages
├── routers/
│   ├── auth_router.py   ← POST /auth/signup, POST /auth/login
│   ├── users_router.py  ← GET/PUT /users/me
│   ├── sessions_router.py ← GET/POST /sessions, GET /sessions/dashboard
│   └── settings_router.py ← GET/PUT /settings
└── speakup.db           ← SQLite database file (created automatically on first run)
```

## Step 1 — Install Python (if you don't have it)
Download from https://python.org — version 3.10 or higher.

## Step 2 — Install dependencies
Open a terminal in this folder and run:
```bash
pip install -r requirements.txt
```

## Step 3 — Start the server
```bash
uvicorn main:app --reload --port 8000
```

You should see:
```
✅ Database tables created successfully!
🚀 SpeakUp API is running!
📖 API docs: http://localhost:8000/docs
INFO: Uvicorn running on http://0.0.0.0:8000
```

The database file `speakup.db` is created automatically the first time you run.

## Step 4 — Add api.js to your HTML files

Copy `api.js` to your HTML project folder. Then add it to every page
BEFORE `main.js`:

```html
<!-- Add BEFORE main.js on every page -->
<script src="api.js"></script>
<script src="main.js"></script>
```

The files already updated are:
- login.html    ✅ — real login
- signup.html   ✅ — real signup
- practice.html ✅ — saves sessions to database
- account.html  ✅ — loads real profile

## API Endpoints

| Method | URL                    | What it does                          | Auth required? |
|--------|------------------------|---------------------------------------|----------------|
| POST   | /auth/signup           | Create account, returns JWT token     | No             |
| POST   | /auth/login            | Log in, returns JWT token             | No             |
| GET    | /users/me              | Get your profile                      | Yes            |
| PUT    | /users/me              | Update your profile                   | Yes            |
| DELETE | /users/me              | Delete your account                   | Yes            |
| POST   | /sessions              | Save a practice session               | Yes            |
| GET    | /sessions              | Get your session history              | Yes            |
| GET    | /sessions/dashboard    | Get all dashboard stats               | Yes            |
| DELETE | /sessions/{id}         | Delete a session                      | Yes            |
| GET    | /settings              | Get your settings                     | Yes            |
| PUT    | /settings              | Update settings                       | Yes            |

## Interactive API Docs

Once the server is running, visit:
  http://localhost:8000/docs

This is a built-in Swagger UI where you can test every endpoint directly
in your browser without writing any code!

## How authentication works

1. User signs up or logs in → backend returns a JWT token
2. Frontend stores the token in localStorage as `sps_token`
3. Every subsequent request sends the token in the Authorization header
4. Backend verifies the token and identifies the user

## Database

The database is a single file: `speakup.db`

You can open and inspect it with:
- DB Browser for SQLite (free app): https://sqlitebrowser.org
- Or run: `sqlite3 speakup.db` in the terminal

Tables:
- users               — accounts
- practice_sessions   — every submitted speech
- scenario_completions — which scenarios each user finished
- user_settings       — per-user settings
- streaks             — daily practice streaks
