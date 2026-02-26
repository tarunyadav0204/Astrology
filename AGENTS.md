# AGENTS.md

## Cursor Cloud specific instructions

### Project Overview
AstroRoshni is a Vedic Astrology web application with a Python/FastAPI backend and React frontend. See `docs/README.md` for architecture overview and `docs/QUICKSTART.md` for astrology-specific context.

### Services

| Service | Port | Command | Notes |
|---------|------|---------|-------|
| Backend API | 8001 | `cd backend && python3 main.py` | FastAPI + Swiss Ephemeris |
| Frontend | 3001 | `cd frontend && npm start` | React dev server, proxies to backend |

### Non-obvious Setup Caveats

- **python3-dev required**: The `pyswisseph` package requires `python3-dev` to build from source. Install with `sudo apt-get install -y python3-dev` before `pip install`.
- **Database initialization**: The SQLite database (`backend/astrology.db`) is NOT auto-created by `main.py` — the `init_db()` function is commented out. You must create the tables manually (see `main_backup.py` lines 540-720 for the full schema) or copy an existing `astrology.db`. Key tables: `users`, `birth_charts`, `subscription_plans`, `user_subscriptions`, `password_reset_codes`, `nakshatras`, `planet_nakshatra_interpretations`.
- **Backend .env file**: Must exist at `backend/.env` with at minimum `JWT_SECRET` (required, server crashes without it) and `ENCRYPTION_KEY` (Fernet key, warns but continues without). See `backend/.env.example` for template. `GEMINI_API_KEY` is needed for AI chat features but the app runs without it.
- **PATH for pip binaries**: pip installs to `~/.local/bin` which may not be on PATH. Add `export PATH="$HOME/.local/bin:$PATH"` if `uvicorn` command is not found.
- **No ESLint config**: The frontend does not have an `.eslintrc` file. The lint check is effectively `npm run build` (CRA built-in ESLint).
- **Backend tests**: Individual test scripts in `backend/test_*.py` — run directly with `python3 test_chart_simple.py`. No test runner framework (pytest/unittest) is configured.
- **Frontend proxy**: The React dev server proxies API requests to `http://localhost:8001` (configured in `frontend/package.json` `"proxy"` field). Backend must be running first.
