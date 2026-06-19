import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from groq import Groq
from pydantic import BaseModel, Field

load_dotenv()

MODEL = "llama-3.1-8b-instant"

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# The eval rubric lives in eval_prompt.md (single source of truth). We use the
# instructions portion (everything before the "### User Input:" marker) as the
# system prompt and supply the actual workflow + plan ourselves.
EVAL_PROMPT_PATH = Path(__file__).with_name("eval_prompt.md")

SYSTEM_PROMPT = """You are an automation consultant for non-technical business analysts.
A student (an analyst) will describe their current manual workflow. Your job is to diagnose
that workflow and hand back a clear, beginner-friendly plan they can follow to build their
FIRST automation. Keep it practical and encouraging. Avoid jargon; when you must use a tool
name, explain why in one line.

Structure your answer in exactly these sections, using markdown headings:

## Workflow Summary
Restate the workflow in 2-3 sentences so the student can confirm you understood it.

## Pain Points & Automation Opportunities
Bullet the repetitive, error-prone, or time-consuming steps. Mark which are worth
automating and which are NOT (and why).

## Recommended First Automation
Pick the SINGLE highest-leverage, lowest-effort automation to start with. One short paragraph.

## Suggested Tools
2-4 beginner-friendly options (e.g. spreadsheets/Google Sheets, Zapier/Make, a small Python
script). One line each on why it fits.

## Step-by-Step Build Plan
A numbered list the student can literally follow to build the recommended first automation.

## Quick Win & Success Metric
The fastest visible result they'll get, plus one metric to measure success (e.g. hours saved/week).
"""


def diagnose(workflow_description: str) -> str:
    """Diagnose an analyst's manual workflow and return a first-automation plan.

    Args:
        workflow_description: Free-text description of the student's current workflow.

    Returns:
        A markdown diagnosis plan the student can follow to build their first automation.
    """
    if not workflow_description or not workflow_description.strip():
        raise ValueError("workflow_description must be a non-empty string.")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": workflow_description.strip()},
        ],
    )

    return response.choices[0].message.content


def _load_eval_instructions() -> str:
    """Load the eval rubric, stripping the trailing placeholder input section."""
    text = EVAL_PROMPT_PATH.read_text(encoding="utf-8")
    marker = "### User Input:"
    return text.split(marker, 1)[0].strip()


# JSON Schema-ish description appended when structured output is requested.
_STRUCTURED_INSTRUCTION = """
Return ONLY a JSON object (no markdown, no prose) with this exact shape:
{
  "overall_score": <number 0-100>,
  "workflow_analyzed": "<one-line summary of the input workflow>",
  "breakdown": [
    {"principle": "<name>", "score": <number 0-6.7>, "comments": "<short>"}
    // exactly 15 entries, one per principle, in order
  ],
  "top_3_improvements": ["<...>", "<...>", "<...>"],
  "suggested_edits": ["<...>", "..."],
  "rewrite": "<full rewritten diagnosis plan scoring 100/100>"
}
"""


def evaluate(workflow_description: str, plan: str, structured: bool = False):
    """Evaluate a diagnosis plan against the 15-principle rubric in eval_prompt.md.

    Args:
        workflow_description: The original workflow text passed to diagnose().
        plan: The diagnosis plan returned by diagnose() (the output to score).
        structured: If True, return a parsed dict of scores; otherwise return
            the markdown evaluation report as a string.

    Returns:
        A markdown report (str) when structured is False, or a dict matching the
        schema in _STRUCTURED_INSTRUCTION when structured is True.
    """
    if not workflow_description or not workflow_description.strip():
        raise ValueError("workflow_description must be a non-empty string.")
    if not plan or not plan.strip():
        raise ValueError("plan must be a non-empty string.")

    system_prompt = _load_eval_instructions()
    if structured:
        system_prompt += "\n" + _STRUCTURED_INSTRUCTION

    user_content = (
        "**Original Workflow Description:**\n"
        f"{workflow_description.strip()}\n\n"
        "**Diagnosis Plan to Evaluate:**\n"
        f"{plan.strip()}"
    )

    kwargs = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }
    if structured:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content

    return json.loads(content) if structured else content


# ---------------------------------------------------------------------------
# FastAPI app (deployed as `uvicorn main:app`)
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Workflow Diagnosis Tool",
    description="Diagnose an analyst's manual workflow and return a first-automation plan.",
    version="1.0.0",
)


class DiagnoseRequest(BaseModel):
    workflow_description: str = Field(
        ...,
        min_length=1,
        description="Free-text description of the analyst's current manual workflow.",
        examples=[
            "Every morning I download a CSV sales report, remove duplicates in Excel, "
            "calculate totals per region, and email a summary to my manager."
        ],
    )


class DiagnoseResponse(BaseModel):
    plan: str = Field(..., description="Markdown diagnosis plan for building the first automation.")


class EvaluateRequest(BaseModel):
    workflow_description: str = Field(
        ..., min_length=1, description="The original workflow text passed to diagnose()."
    )
    plan: str = Field(..., min_length=1, description="The diagnosis plan to score.")
    structured: bool = Field(
        False, description="If true, return parsed JSON scores instead of a markdown report."
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/diagnose", response_model=DiagnoseResponse)
def diagnose_endpoint(req: DiagnoseRequest):
    try:
        plan = diagnose(req.workflow_description)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")
    return DiagnoseResponse(plan=plan)


@app.post("/evaluate")
def evaluate_endpoint(req: EvaluateRequest):
    try:
        result = evaluate(req.workflow_description, req.plan, structured=req.structured)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")
    return result if req.structured else {"report": result}


SAMPLE_WORKFLOW = (
    "Every morning I download a CSV sales report from our dashboard, open it in Excel, "
    "remove duplicate rows, calculate totals per region, paste the summary into a fresh "
    "spreadsheet, and email it to my manager. It takes about an hour each day."
)


if __name__ == "__main__":
    # Usage:
    #   python3 main.py "my workflow..."   -> diagnose a workflow
    #   python3 main.py eval               -> diagnose the sample, then score the plan
    if len(sys.argv) > 1 and sys.argv[1] == "eval":
        workflow = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else SAMPLE_WORKFLOW
        print("WORKFLOW:\n" + workflow + "\n" + "=" * 70 + "\n")
        plan = diagnose(workflow)
        print("DIAGNOSIS PLAN:\n" + plan + "\n" + "=" * 70 + "\n")
        print("EVALUATION (report):\n" + evaluate(workflow, plan) + "\n" + "=" * 70 + "\n")
        print("EVALUATION (scores):")
        print(json.dumps(evaluate(workflow, plan, structured=True), indent=2))
    else:
        if len(sys.argv) > 1:
            workflow = " ".join(sys.argv[1:])
        else:
            workflow = SAMPLE_WORKFLOW
            print("No workflow provided. Using sample workflow:\n")
            print(workflow + "\n")
            print("=" * 70 + "\n")
        print(diagnose(workflow))
