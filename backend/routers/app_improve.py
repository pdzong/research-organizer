"""
Ad-hoc app-improvement discovery API.

* ``POST /app-improve/discover`` — find papers and persist a run
* ``GET /app-improve/runs`` — list saved runs
* ``GET /app-improve/runs/{id}`` — full run JSON
* ``GET /app-improve/runs/{id}/markdown`` — markdown report
* ``DELETE /app-improve/runs/{id}`` — delete a saved run
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from services.app_improve import (
    AppImproveRun,
    AppImproveRunSummary,
    delete_run,
    discover_for_app,
    get_run,
    get_run_markdown,
    list_runs,
)

router = APIRouter()


class AppImproveRequest(BaseModel):
    app_description: str = Field(
        ...,
        min_length=8,
        description="What the app/product is and who it is for.",
    )
    improvement_direction: str = Field(
        ...,
        min_length=8,
        description="The capability, quality, or direction you want to improve.",
    )
    limit_per_topic: int = Field(5, ge=1, le=20)
    since: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Earliest publication date (YYYY-MM-DD)",
    )
    score_top: int = Field(
        5,
        ge=0,
        le=10,
        description="Run strategic-fit scoring on the N first results (costs LLM calls).",
    )
    topics: Optional[List[str]] = Field(
        None,
        description="Optional override for search topics (skips LLM topic derivation).",
    )


class AppImproveResponse(BaseModel):
    success: bool
    run_id: Optional[str] = None
    created_at: Optional[str] = None
    topics_searched: List[str]
    topics_rationale: Optional[str] = None
    papers: List[dict]
    count: int
    error: Optional[str] = None


class AppImproveRunListResponse(BaseModel):
    success: bool
    runs: List[AppImproveRunSummary]


class AppImproveRunResponse(BaseModel):
    success: bool
    run: AppImproveRun


@router.post("/app-improve/discover", response_model=AppImproveResponse)
async def discover_for_app_endpoint(body: AppImproveRequest):
    """
    Find papers that are a good fit for improving a described app.

    Successful runs are saved under ``backend/data/app_improve/{run_id}/``.
    """
    return await discover_for_app(
        app_description=body.app_description,
        improvement_direction=body.improvement_direction,
        limit_per_topic=body.limit_per_topic,
        since=body.since,
        score_top=body.score_top,
        topics=body.topics,
    )


@router.get("/app-improve/runs", response_model=AppImproveRunListResponse)
async def list_app_improve_runs():
    return {"success": True, "runs": list_runs()}


@router.get("/app-improve/runs/{run_id}", response_model=AppImproveRunResponse)
async def get_app_improve_run(run_id: str):
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return {"success": True, "run": run}


@router.get("/app-improve/runs/{run_id}/markdown", response_class=PlainTextResponse)
async def get_app_improve_run_markdown(run_id: str):
    markdown = get_run_markdown(run_id)
    if markdown is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return PlainTextResponse(
        markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{run_id}.md"'},
    )


@router.delete("/app-improve/runs/{run_id}")
async def delete_app_improve_run(run_id: str):
    if not delete_run(run_id):
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return {"success": True}
