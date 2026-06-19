# Task: Dependency Manifest + Render Deployment

## Goal
Make the project installable and deployable on Render.

## Why
The first Render deploy failed: no dependency manifest existed, so the build couldn't install
groq/fastapi/uvicorn/etc.

## Deliverables
1. **`requirements.txt`** — pinned to installed versions:
   - Runtime: `groq`, `python-dotenv`, `fastapi`, `uvicorn`, `pydantic`.
   - Tests: `httpx`, `pytest`.
   - Verified: clean-venv `pip install -r requirements.txt` + all 10 tests pass.
2. **`.gitignore`** — excludes secrets (`.env`, `Untitled`) and Python cruft
   (`__pycache__/`, `.pytest_cache/`, venvs).
3. **`.env.example`** — template documenting the required `GROQ_API_KEY`.

## Render setup (manual, on dashboard)
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
  (must bind `$PORT` and reference `main:app` — see [[render-deploy-fix]]).
- Health check path: `/health`.
- Env var: set `GROQ_API_KEY` in the dashboard (never committed). Without it, `/diagnose`
  returns 502.

## Security note
- `.env` and `Untitled` held a live `GROQ_API_KEY`; both are gitignored and were never pushed.
  Recommend rotating that key since it was shared in chat.

## Committed in
- `8c8d69c` (requirements.txt). `.gitignore` + `.env.example` in `d571f94`.
- A `render.yaml` blueprint was added (`19fe914`) then removed (`3793a2d`) in favor of
  dashboard-configured start command.
