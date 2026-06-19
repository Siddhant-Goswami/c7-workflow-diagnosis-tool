# Task: Eval Prompt + `evaluate()` Function

## Goal
Create a way to score the quality of the diagnosis plan produced by `diagnose()`, and expose
it as a reusable function.

## Why
A diagnosis plan is only useful if it's accurate, prioritized, beginner-feasible, and honest
about what NOT to automate. We need a repeatable rubric to grade outputs (for QA, regression
checks, and prompt iteration). Inspiration taken from an Ogilvy-style 15-principle ad-copy
scoring prompt, retargeted to automation-diagnosis quality.

## Deliverables
1. **`eval_prompt.md`** — the rubric / judge prompt:
   - 7-step task (read inputs → score → breakdown → top-3 → edits → rewrite).
   - 15 weighted principles (~6.7 pts each) adapted to automation advice:
     Workflow Understanding, Pain Point Identification, Automation Prioritization,
     Beginner Feasibility, Tool Appropriateness, Actionability, Step Sequencing,
     Scope Discipline, Clarity & Simplicity, Quick Win, Success Metric,
     Effort vs. Benefit Awareness, Risk & Edge-Case Awareness, Structure & Skimmability, Tone.
   - Output format: scored markdown table + top-3 fixes + suggested edits + 100/100 rewrite.
   - Takes TWO inputs (original workflow + plan), since a plan can't be judged in isolation.
2. **`evaluate(workflow_description, plan, structured=False)`** in `main.py`:
   - Loads the rubric from `eval_prompt.md` (single source of truth) via
     `_load_eval_instructions()`, stripping the trailing `### User Input:` placeholder section.
   - `structured=False` -> markdown report string.
   - `structured=True` -> appends a JSON-shape instruction, sets Groq
     `response_format={"type": "json_object"}`, returns a parsed dict
     (`overall_score`, 15-entry `breakdown`, `top_3_improvements`, `suggested_edits`, `rewrite`).
   - Validates both inputs non-empty.
3. **CLI `eval` mode** in `main.py`: `python3 main.py eval [workflow]` diagnoses then prints
   both the markdown report and the structured JSON scores.

## Handover notes (complete)
- Implemented in `main.py` (`evaluate`, `_load_eval_instructions`, `_STRUCTURED_INSTRUCTION`).
- Verified end-to-end against Groq: sample plan scored ~86/100 with full 15-row breakdown,
  and structured mode parses cleanly into a dict.
- Note: the CLI `eval` mode makes two separate `evaluate()` calls (markdown + JSON), so the two
  scorings are independent and may differ slightly. Possible follow-up: derive markdown from
  the JSON in a single call. For a deterministic judge, consider `temperature=0`.

## Committed in
- `d571f94` (initial commit, alongside diagnose + API).
