"""
Strategic-fit scoring (P2-002).

Scores a paper against a :class:`CompanyProfile`: how relevant is this
research to what the company builds, what opportunities or threats does it
create, and which strategic assumptions does it challenge?

Results are cached per (paper, profile) under the paper's cache directory:
``backend/data/cache/{cache_key}/strategic_fit_{profile_id}.json``
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from . import cache_service, llm_clients
from .company_profiles import CompanyProfile


class StrategicFitAssessment(BaseModel):
    """Structured verdict on how a paper matters to one company."""

    fit_score: int = Field(..., ge=0, le=100, description="0 = irrelevant, 100 = must act now")
    relevance_summary: str = Field(..., description="One or two sentences: why this paper matters (or not) to the company.")
    opportunities: List[str] = Field(default_factory=list, description="Concrete ways the company could exploit this research.")
    threats: List[str] = Field(default_factory=list, description="Ways this research could disrupt the company or its market.")
    challenged_assumptions: List[str] = Field(default_factory=list, description="Which of the company's stated assumptions this paper challenges, if any.")
    recommended_action: Literal["ignore", "watch", "analyze", "prototype"] = Field(
        ..., description="ignore = not relevant; watch = track the topic; analyze = read deeply; prototype = act on it now"
    )
    reasoning: str = Field(..., description="Short justification for the score and action.")


SYSTEM_PROMPT = """You are a research strategist working for a specific company.
Given a company profile and a research paper, assess the paper's strategic
relevance TO THIS COMPANY ONLY — not its general scientific merit.

Consider:
- Does it enable a product/feature the company could ship? (opportunity)
- Could it disrupt the company's market or make its approach obsolete? (threat)
- Does it challenge any of the company's stated strategic assumptions?
- Is it close enough to the company's tech stack to act on?

Be conservative: most papers deserve "ignore" or "watch". Reserve "analyze"
for papers with clear, direct relevance and "prototype" for papers whose
results the company should act on immediately."""


def _profile_block(profile: CompanyProfile) -> str:
    parts = [f"Company: {profile.name}"]
    if profile.industry:
        parts.append(f"Industry: {profile.industry}")
    if profile.description:
        parts.append(f"What they build: {profile.description}")
    if profile.tech_stack:
        parts.append("Tech stack: " + ", ".join(profile.tech_stack))
    if profile.strategic_questions:
        parts.append("Strategic questions:\n- " + "\n- ".join(profile.strategic_questions))
    if profile.watch_topics:
        parts.append("Watch topics: " + ", ".join(profile.watch_topics))
    if profile.assumptions:
        parts.append("Strategic assumptions:\n- " + "\n- ".join(profile.assumptions))
    return "\n".join(parts)


def _paper_block(paper: Dict[str, Any], cache_key: Optional[str]) -> str:
    parts = [f"Title: {paper.get('title', 'Unknown')}"]
    if paper.get("authors"):
        parts.append("Authors: " + ", ".join(paper["authors"][:8]))
    if paper.get("published_date"):
        parts.append(f"Published: {paper['published_date']}")
    meta = paper.get("source_metadata") or {}
    if meta.get("topics"):
        parts.append("Topics: " + ", ".join(meta["topics"]))
    if paper.get("abstract"):
        parts.append(f"Abstract:\n{paper['abstract']}")

    # Enrich with cached deep analysis when the paper was already analyzed.
    if cache_key:
        cached = cache_service.load_analysis(cache_key)
        analysis = (cached or {}).get("data") or {}
        summary = analysis.get("summary") or analysis.get("tldr")
        if summary:
            parts.append(f"Existing analysis summary:\n{summary}")
        novelty = analysis.get("novelty") or analysis.get("key_contributions")
        if novelty:
            parts.append(f"Novelty / contributions:\n{json.dumps(novelty, ensure_ascii=False)[:1500]}")
    return "\n".join(parts)


def _fit_cache_file(cache_key: str, profile_id: str):
    return cache_service.CACHE_DIR / cache_key / f"strategic_fit_{profile_id}.json"


def load_cached_fit(cache_key: str, profile_id: str) -> Optional[Dict[str, Any]]:
    path = _fit_cache_file(cache_key, profile_id)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_cached_fit(cache_key: str, profile_id: str, result: Dict[str, Any]) -> None:
    path = _fit_cache_file(cache_key, profile_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


async def score_paper_for_profile(
    paper: Dict[str, Any],
    profile: CompanyProfile,
    cache_key: Optional[str] = None,
    force_reload: bool = False,
) -> Dict[str, Any]:
    """
    Score one paper against one company profile.

    Returns ``{success, assessment, from_cache, error}`` where ``assessment``
    is a :class:`StrategicFitAssessment` dump plus scoring metadata.
    """
    if cache_key and not force_reload:
        cached = load_cached_fit(cache_key, profile.id)
        if cached:
            return {"success": True, "assessment": cached, "from_cache": True, "error": None}

    if not paper.get("abstract") and not (cache_key and cache_service.load_analysis(cache_key)):
        return {
            "success": False,
            "assessment": None,
            "from_cache": False,
            "error": "Paper has no abstract and no cached analysis; parse/analyze it first or add it from a source that provides an abstract.",
        }

    user_prompt = (
        f"## Company profile\n{_profile_block(profile)}\n\n"
        f"## Paper\n{_paper_block(paper, cache_key)}\n\n"
        "Assess the strategic fit of this paper for this company."
    )

    try:
        assessment, usage = await llm_clients.parse_structured(
            role="strategic_fit",
            schema=StrategicFitAssessment,
            system=SYSTEM_PROMPT,
            user=user_prompt,
        )
    except Exception as e:
        return {"success": False, "assessment": None, "from_cache": False, "error": str(e)}

    result = assessment.model_dump()
    result["profile_id"] = profile.id
    result["paper_id"] = paper.get("id")
    result["scored_at"] = datetime.now().isoformat()
    result["usage"] = usage

    if cache_key:
        save_cached_fit(cache_key, profile.id, result)

    return {"success": True, "assessment": result, "from_cache": False, "error": None}
