"""
Company research profile API routes (P2-001/P2-002/P2-005).

* CRUD for company profiles + active-profile selection
* ``POST /profiles/{id}/score/{paper_id}`` — strategic-fit scoring of a
  library paper against a profile
* ``GET /profiles/{id}/discover`` — profile-driven OpenAlex discovery from
  the profile's watch topics, with optional strategic-fit scoring of the
  top results
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services import company_profiles
from services.company_profiles import CompanyProfile, CompanyProfileInput
from services.huggingface import load_papers
from services.source_paper import find_paper_by_id, resolve_cache_key_for_paper_id
from services.sources.openalex import search_openalex_works
from services.strategic_fit import score_paper_for_profile

router = APIRouter()


class ProfileListResponse(BaseModel):
    success: bool
    profiles: List[CompanyProfile]
    active_profile_id: Optional[str] = None


class ProfileResponse(BaseModel):
    success: bool
    profile: Optional[CompanyProfile] = None
    error: Optional[str] = None


class StrategicFitResponse(BaseModel):
    success: bool
    assessment: Optional[Dict[str, Any]] = None
    from_cache: bool = False
    error: Optional[str] = None


class DiscoverResponse(BaseModel):
    success: bool
    profile_id: str
    topics_searched: List[str]
    papers: List[Dict[str, Any]]
    count: int
    error: Optional[str] = None


def _require_profile(profile_id: str) -> CompanyProfile:
    profile = company_profiles.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile not found: {profile_id}")
    return profile


@router.get("/profiles", response_model=ProfileListResponse)
async def get_profiles():
    """List all company profiles and the active profile id."""
    return {
        "success": True,
        "profiles": company_profiles.list_profiles(),
        "active_profile_id": company_profiles.get_active_profile_id(),
    }


@router.post("/profiles", response_model=ProfileResponse)
async def create_profile(data: CompanyProfileInput):
    """Create a new company profile. The first profile becomes active."""
    profile = company_profiles.create_profile(data)
    return {"success": True, "profile": profile}


@router.get("/profiles/active", response_model=ProfileResponse)
async def get_active_profile():
    """Return the currently active profile (404 if none is set)."""
    profile = company_profiles.get_active_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="No active profile set")
    return {"success": True, "profile": profile}


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: str):
    return {"success": True, "profile": _require_profile(profile_id)}


@router.put("/profiles/{profile_id}", response_model=ProfileResponse)
async def update_profile(profile_id: str, data: CompanyProfileInput):
    profile = company_profiles.update_profile(profile_id, data)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile not found: {profile_id}")
    return {"success": True, "profile": profile}


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    if not company_profiles.delete_profile(profile_id):
        raise HTTPException(status_code=404, detail=f"Profile not found: {profile_id}")
    return {"success": True}


@router.post("/profiles/{profile_id}/activate")
async def activate_profile(profile_id: str):
    if not company_profiles.set_active_profile(profile_id):
        raise HTTPException(status_code=404, detail=f"Profile not found: {profile_id}")
    return {"success": True, "active_profile_id": profile_id}


@router.post("/profiles/{profile_id}/score/{paper_id}", response_model=StrategicFitResponse)
async def score_paper(
    profile_id: str,
    paper_id: str,
    force_reload: bool = Query(False, description="Re-run scoring even if cached"),
):
    """
    Score a library paper against a company profile (P2-002).

    The paper must exist in the library. Uses the paper's abstract plus any
    cached deep analysis as scoring context; results are cached per
    (paper, profile).
    """
    profile = _require_profile(profile_id)

    papers = load_papers()
    paper = find_paper_by_id(papers, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper not found in library: {paper_id}")

    cache_key = resolve_cache_key_for_paper_id(papers, paper_id)
    return await score_paper_for_profile(
        paper, profile, cache_key=cache_key, force_reload=force_reload
    )


@router.get("/profiles/{profile_id}/discover", response_model=DiscoverResponse)
async def discover_for_profile(
    profile_id: str,
    limit_per_topic: int = Query(5, ge=1, le=20, description="Max results per watch topic"),
    since: Optional[str] = Query(
        None,
        description="Earliest publication date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    score_top: int = Query(
        0,
        ge=0,
        le=10,
        description="Run strategic-fit scoring on the N most recent results (costs LLM calls)",
    ),
):
    """
    Profile-driven discovery (P2-005, simple version): search OpenAlex for
    each of the profile's watch topics, merge and dedupe the results, and
    optionally score the most recent ones for strategic fit.
    """
    profile = _require_profile(profile_id)
    if not profile.watch_topics:
        return {
            "success": False,
            "profile_id": profile_id,
            "topics_searched": [],
            "papers": [],
            "count": 0,
            "error": "Profile has no watch_topics; add topics to enable discovery.",
        }

    seen: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []
    for topic in profile.watch_topics:
        try:
            results = await search_openalex_works(
                query=topic, limit=limit_per_topic, since=since, open_access_only=True
            )
        except Exception as exc:
            errors.append(f"{topic}: {exc}")
            continue
        for paper in results:
            record = paper.to_storage_dict()
            record["matched_topic"] = topic
            seen.setdefault(record["id"], record)

    # Keep provider relevance order (grouped by topic); date-sorting would
    # float junk records with bogus future dates to the top.
    merged = list(seen.values())

    if score_top > 0:
        for record in merged[:score_top]:
            fit = await score_paper_for_profile(record, profile, cache_key=None)
            if fit.get("success"):
                record["strategic_fit"] = fit["assessment"]
            else:
                record["strategic_fit_error"] = fit.get("error")

    return {
        "success": True,
        "profile_id": profile_id,
        "topics_searched": list(profile.watch_topics),
        "papers": merged,
        "count": len(merged),
        "error": "; ".join(errors) if errors else None,
    }
