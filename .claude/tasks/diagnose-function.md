# Task: Build `diagnose()` — Workflow Diagnosis Tool

## Goal
Implement the `diagnose(workflow_description)` function in `main.py`. It takes a free-text
description of an analyst's (the "student's") current manual workflow and returns a
**diagnosis plan** they can follow to build their first automation.

LLM: Groq Cloud, model `llama-3.1-8b-instant` (key already in `.env` as `GROQ_API_KEY`).

## Why
The student is an analyst who wants to start automating but doesn't know where to begin.
Given a plain description of what they do, the tool should diagnose the workflow and hand
back a concrete, beginner-friendly automation plan.

## MVP scope
- Single Python file (`main.py`), no framework, runnable from CLI.
- One LLM call to Groq, returning a structured-but-readable plan as text.
- Load API key from `.env` via `python-dotenv` (already installed).
- Use the `groq` SDK (already installed).

## Implementation steps
1. **Imports & setup**: `os`, `load_dotenv()`, `from groq import Groq`. Instantiate client
   with `GROQ_API_KEY`. Define `MODEL = "llama-3.1-8b-instant"`.
2. **System prompt**: Frame the model as an automation consultant for non-technical analysts.
   Ask it to produce a diagnosis plan with these sections:
   - Summary of the workflow it understood (so the student can confirm)
   - Pain points / what's worth automating (and what's not)
   - Recommended first automation (the single highest-leverage, lowest-effort one)
   - Suggested tools (beginner-friendly, e.g. spreadsheets, Zapier/Make, simple scripts)
   - Step-by-step build plan for that first automation
   - Quick win / success metric
3. **`diagnose(workflow_description)`**:
   - Guard against empty input.
   - Call `client.chat.completions.create(...)` with system + user messages,
     `temperature` modest (~0.4) for consistency.
   - Return `response.choices[0].message.content`.
4. **`__main__` block**: read a sample workflow description (or `input()` / sys.argv) and
   print the plan, so the file is runnable end-to-end for a quick demo.
5. **Manual test**: run `python3 main.py` with a sample analyst workflow and verify a
   sensible plan comes back.

## Out of scope (for MVP)
- Web UI / API server, streaming, retries/backoff, multi-turn conversation, persistence.

## Notes / handover (implementation complete)
Implemented in `main.py`:
- `load_dotenv()` reads `GROQ_API_KEY` from `.env`; `MODEL = "llama-3.1-8b-instant"`.
- Module-level `Groq` client.
- `SYSTEM_PROMPT` instructs the model to act as an automation consultant for non-technical
  analysts and to emit a fixed 6-section markdown plan (Workflow Summary, Pain Points &
  Automation Opportunities, Recommended First Automation, Suggested Tools, Step-by-Step
  Build Plan, Quick Win & Success Metric).
- `diagnose(workflow_description) -> str`: raises `ValueError` on empty input, makes one
  `chat.completions.create` call (`temperature=0.4`), returns the message content.
- `__main__` block: takes the workflow from CLI args (`python3 main.py "my workflow..."`),
  or falls back to a built-in sample analyst workflow and prints the plan.

Verified: `python3 main.py` runs against the live Groq API and returns a sensible,
well-structured plan.

Possible follow-ups (not done): structured JSON output, streaming, retries/backoff,
web/API wrapper, multi-turn refinement.
