# Task: Fix Render Deploy ("app not found in module main")

## Problem
Render build succeeded but the service crashed on start:

```
Running 'uvicorn main:app --host 0.0.0.0 --port $PORT'
ERROR: Error loading ASGI app. Attribute "app" not found in module "main".
Exited with status 1
```

Render's start command referenced `main:app`, but the FastAPI `app` lived in `api.py`.

## Decision
Rather than change the Render start command, consolidate the API into `main.py` so
`main:app` resolves. This keeps a single entry module and matches the deploy command.

## Changes
1. Moved the FastAPI `app` + pydantic models + endpoints (`/health`, `/diagnose`,
   `/evaluate`) from `api.py` into `main.py`. Added `fastapi` / `pydantic` imports there.
2. Deleted `api.py` (merged) and `render.yaml` (user opted for dashboard config).
3. Repointed `test_api.py` to `main.app` and `patch.object(main, ...)`.

## Verification (complete)
- `uvicorn main:app` boots: "Application startup complete"; `/health` -> `{"status":"ok"}`.
- All 10 tests pass (`python3 -m pytest test_api.py -q`).

## Still required on Render
- Set `GROQ_API_KEY` env var in the dashboard.
- Rotate the previously-shared key.

## Committed in
- `3793a2d`.
