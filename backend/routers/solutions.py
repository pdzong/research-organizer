"""
Endpoints that turn a saved `application` (domain + utility + papers) into a
codegen-ready Markdown system / solution plan.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services import cache_service
from services.solution_planner import generate_solution_plan


router = APIRouter()


class GeneratePlanResponse(BaseModel):
    success: bool
    application_id: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None
    markdown: Optional[str] = None
    brief: Optional[str] = None
    generated_at: Optional[str] = None
    from_cache: bool = False
    error: Optional[str] = None


class ListPlansResponse(BaseModel):
    success: bool
    plans: List[Dict[str, Any]] = []
    error: Optional[str] = None


@router.post(
    "/applications/{application_id:path}/plan",
    response_model=GeneratePlanResponse,
)
async def generate_plan_for_application(
    application_id: str,
    force_reload: bool = Query(False, description="Regenerate even if cached"),
) -> GeneratePlanResponse:
    """Run the agentic planner against a saved application entry."""
    try:
        if not force_reload:
            cached = cache_service.load_solution_plan(application_id)
            if cached:
                return GeneratePlanResponse(
                    success=True,
                    application_id=application_id,
                    plan=cached.get("plan"),
                    markdown=cached.get("markdown"),
                    brief=cached.get("brief"),
                    generated_at=cached.get("generated_at"),
                    from_cache=True,
                )

        application = cache_service.load_application(application_id)
        if application is None:
            raise HTTPException(
                status_code=404,
                detail=f"Application '{application_id}' not found",
            )

        result = await generate_solution_plan(application)
        if not result.get("success"):
            return GeneratePlanResponse(
                success=False,
                application_id=application_id,
                error=result.get("error"),
            )

        cache_service.save_solution_plan(application_id, result)
        cached = cache_service.load_solution_plan(application_id) or {}
        return GeneratePlanResponse(
            success=True,
            application_id=application_id,
            plan=result.get("plan"),
            markdown=result.get("markdown"),
            brief=result.get("brief"),
            generated_at=cached.get("generated_at"),
            from_cache=False,
        )
    except HTTPException:
        raise
    except Exception as e:
        return GeneratePlanResponse(
            success=False, application_id=application_id, error=str(e)
        )


@router.get(
    "/applications/{application_id:path}/plan",
    response_model=GeneratePlanResponse,
)
async def get_plan_for_application(application_id: str) -> GeneratePlanResponse:
    cached = cache_service.load_solution_plan(application_id)
    if not cached:
        return GeneratePlanResponse(
            success=False,
            application_id=application_id,
            error="No plan generated yet for this application.",
        )
    return GeneratePlanResponse(
        success=True,
        application_id=application_id,
        plan=cached.get("plan"),
        markdown=cached.get("markdown"),
        brief=cached.get("brief"),
        generated_at=cached.get("generated_at"),
        from_cache=True,
    )


@router.get("/solutions", response_model=ListPlansResponse)
async def list_solutions() -> ListPlansResponse:
    try:
        plans = cache_service.list_solution_plans()
        return ListPlansResponse(success=True, plans=plans)
    except Exception as e:
        return ListPlansResponse(success=False, plans=[], error=str(e))
