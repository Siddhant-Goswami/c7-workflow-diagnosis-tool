# Task: API Test Suite

## Goal
Test the FastAPI endpoints without hitting the live Groq API.

## Why
Tests must be fast, deterministic, and runnable in CI/offline. We test the API contract
(status codes, response shapes, validation, error mapping) — not LLM output quality, which
the eval rubric handles separately ([[eval-prompt-and-evaluate]]).

## Approach
- `test_api.py` uses FastAPI `TestClient` and `unittest.mock.patch.object` to stub
  `main.diagnose` / `main.evaluate`.
- 10 tests covering:
  - `/health` -> 200 ok.
  - `/diagnose`: success shape + arg, empty string -> 422, missing field -> 422,
    `ValueError` -> 422, generic failure -> 502.
  - `/evaluate`: markdown default (`{"report": ...}`), `structured=true` returns dict,
    missing `plan` -> 422, generic failure -> 502.

## Handover notes (complete)
- Run: `python3 -m pytest test_api.py -v`. All 10 pass in <0.3s, no network.
- Patch targets are `main.diagnose` / `main.evaluate` because the app now lives in `main.py`
  (was `api.*` before the consolidation — see [[render-deploy-fix]]).
- Possible follow-up: an opt-in `@pytest.mark.integration` test that hits real Groq.

## Committed in
- `d571f94` (initial), repointed to `main` in `3793a2d`.
