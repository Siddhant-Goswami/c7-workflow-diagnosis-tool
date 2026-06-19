# Task: FastAPI Endpoints for diagnose/evaluate

## Goal
Expose `diagnose()` (and `evaluate()`) over HTTP so the tool can be consumed by a frontend or
other services.

## Why
The CLI is fine for local use, but students/integrations need an API. FastAPI gives typed
request/response validation and auto-generated docs with minimal code.

## Deliverables (in `main.py` as `app`)
- `app = FastAPI(...)` — deployable via `uvicorn main:app`.
- Pydantic models: `DiagnoseRequest`, `DiagnoseResponse`, `EvaluateRequest`
  (`workflow_description`/`plan` enforced `min_length=1`).
- Endpoints:
  - `GET /health` -> `{"status": "ok"}` (liveness / Render health check).
  - `POST /diagnose` -> `{"plan": "...markdown..."}`.
  - `POST /evaluate` -> `{"report": "..."}` (markdown) or raw JSON scores when
    `structured: true`.
- Error mapping: `ValueError` -> `422`; any other LLM/runtime error -> `502`
  (no stack-trace leak). Validation failures -> `422` via pydantic.
- Interactive Swagger docs auto-served at `/docs`.

## History / important note
- Originally implemented in a separate `api.py` (`uvicorn api:app`).
- Render's start command was `uvicorn main:app`, which failed with
  "Attribute 'app' not found in module 'main'". The app was therefore consolidated into
  `main.py`. See [[render-deploy-fix]].

## Handover notes (complete)
- Verified locally: health, diagnose (happy path), and validation (empty -> 422) all work.
- Port 8000 is occupied on the dev machine by another process; use another port locally.

## Committed in
- `d571f94` (initial, as `api.py`), then `3793a2d` (moved into `main.py`).
