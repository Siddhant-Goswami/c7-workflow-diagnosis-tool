from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from main import diagnose, evaluate

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
