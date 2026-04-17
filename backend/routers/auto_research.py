"""
Auto-research control plane: start/stop a background runner that walks a paper
source (HuggingFace daily papers today) and pushes each paper through the full
parse → analyze → save-applications pipeline.
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.auto_research import SOURCES, runner


router = APIRouter()


class StartRequest(BaseModel):
    source: str = Field(default="huggingface", description="Paper source id")
    limit: int = Field(
        default=5, ge=1, le=50, description="Max papers per batch"
    )
    continuous: bool = Field(
        default=False,
        description="Keep looping after the batch instead of stopping.",
    )
    interval_seconds: int = Field(
        default=300,
        ge=10,
        description="Sleep between batches in continuous mode.",
    )
    generate_plans: bool = Field(
        default=False,
        description="If true, auto-generate codegen-ready SolutionPlans for each plan-worthy application derived from a paper.",
    )
    plan_min_confidence: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Plan-worthiness gate threshold (0-1).",
    )


class StatusResponse(BaseModel):
    success: bool
    status: dict
    error: Optional[str] = None


@router.get("/auto-research/sources")
async def list_sources():
    return {"success": True, "sources": [{"id": k, "label": v} for k, v in SOURCES.items()]}


@router.post("/auto-research/start", response_model=StatusResponse)
async def start_auto_research(req: StartRequest) -> StatusResponse:
    result = await runner.start(
        source=req.source,
        limit=req.limit,
        continuous=req.continuous,
        interval_seconds=req.interval_seconds,
        generate_plans=req.generate_plans,
        plan_min_confidence=req.plan_min_confidence,
    )
    return StatusResponse(
        success=result.get("success", False),
        status=runner.get_status(),
        error=result.get("error"),
    )


@router.post("/auto-research/stop", response_model=StatusResponse)
async def stop_auto_research() -> StatusResponse:
    result = await runner.stop()
    return StatusResponse(
        success=result.get("success", True),
        status=runner.get_status(),
        error=result.get("error"),
    )


@router.get("/auto-research/status", response_model=StatusResponse)
async def get_auto_research_status() -> StatusResponse:
    return StatusResponse(success=True, status=runner.get_status())
