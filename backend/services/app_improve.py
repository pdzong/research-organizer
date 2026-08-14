"""
Ad-hoc app-improvement discovery.

Takes a product description and an intended improvement direction, derives
OpenAlex search topics, then reuses company-profile discovery + strategic-fit
scoring so the caller gets a ranked list of papers that fit the product —
without creating a persisted CompanyProfile.
"""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from . import llm_clients
from .company_profiles import CompanyProfile
from .sources.openalex import search_openalex_works
from .strategic_fit import score_paper_for_profile

ADHOC_PROFILE_ID = "adhoc-app"
RUNS_DIR = Path(__file__).parent.parent / "data" / "app_improve"


class SearchTopics(BaseModel):
    """LLM-derived OpenAlex queries for an app-improvement brief."""

    topics: List[str] = Field(
        ...,
        min_length=1,
        max_length=8,
        description="3–6 short academic search phrases (not marketing slogans).",
    )
    rationale: str = Field(
        default="",
        description="One sentence on why these queries cover the improvement goal.",
    )


class AppImproveRunSummary(BaseModel):
    id: str
    created_at: str
    app_description: str
    improvement_direction: str
    count: int
    topics_searched: List[str] = Field(default_factory=list)
    top_fit_score: Optional[int] = None


class AppImproveRun(AppImproveRunSummary):
    since: Optional[str] = None
    limit_per_topic: int = 5
    score_top: int = 5
    topics_rationale: Optional[str] = None
    papers: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


TOPIC_SYSTEM_PROMPT = """You turn a product description and an improvement goal into
academic search queries. Return 3–6 short phrases a researcher would type into
OpenAlex or Google Scholar. Prefer established research terms over marketing
language. Do not repeat the same idea with different wording. Each topic should
be 2–8 words."""


def ephemeral_profile(
    app_description: str,
    improvement_direction: str,
    topics: Optional[List[str]] = None,
) -> CompanyProfile:
    """Build a throwaway CompanyProfile so strategic-fit scoring can be reused."""
    description = app_description.strip()
    direction = improvement_direction.strip()
    name = description.split(".")[0].strip()[:80] or "This product"
    return CompanyProfile(
        id=ADHOC_PROFILE_ID,
        name=name,
        description=description,
        strategic_questions=[direction] if direction else [],
        watch_topics=topics or [],
        created_at="",
        updated_at="",
    )


def _fallback_topics(improvement_direction: str) -> List[str]:
    topic = " ".join(improvement_direction.strip().split())
    return [topic] if topic else []


def _index_path() -> Path:
    return RUNS_DIR / "index.json"


def _run_dir(run_id: str) -> Path:
    return RUNS_DIR / run_id


def _run_json_path(run_id: str) -> Path:
    return _run_dir(run_id) / "run.json"


def _run_md_path(run_id: str) -> Path:
    return _run_dir(run_id) / "report.md"


def _top_fit_score(papers: List[Dict[str, Any]]) -> Optional[int]:
    scores = []
    for paper in papers:
        fit = paper.get("strategic_fit") or {}
        score = fit.get("fit_score")
        if isinstance(score, int):
            scores.append(score)
    return max(scores) if scores else None


def _summary_from_run(run: AppImproveRun) -> AppImproveRunSummary:
    return AppImproveRunSummary(
        id=run.id,
        created_at=run.created_at,
        app_description=run.app_description,
        improvement_direction=run.improvement_direction,
        count=run.count,
        topics_searched=run.topics_searched,
        top_fit_score=run.top_fit_score,
    )


def _load_index() -> List[Dict[str, Any]]:
    path = _index_path()
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as exc:
        print(f"app_improve: failed to read index: {exc}")
        return []


def _save_index(entries: List[Dict[str, Any]]) -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    with open(_index_path(), "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def run_to_markdown(run: AppImproveRun) -> str:
    lines = [
        "# App improvement report",
        "",
        f"**Run id:** `{run.id}`",
        f"**Generated:** {run.created_at}",
        f"**Papers:** {run.count}",
    ]
    if run.top_fit_score is not None:
        lines.append(f"**Top fit score:** {run.top_fit_score}/100")
    if run.since:
        lines.append(f"**Published since:** {run.since}")
    lines.extend(["", "## App", "", run.app_description.strip(), "", "## Intended improvement", "", run.improvement_direction.strip(), ""])
    if run.topics_searched:
        lines.extend(["## Search topics", ""])
        for topic in run.topics_searched:
            lines.append(f"- {topic}")
        if run.topics_rationale:
            lines.extend(["", run.topics_rationale])
        lines.append("")
    if run.error:
        lines.extend(["## Notes", "", run.error, ""])
    lines.extend([f"## Papers ({run.count})", ""])
    if not run.papers:
        lines.append("_No papers returned._")
        return "\n".join(lines) + "\n"

    for i, paper in enumerate(run.papers, start=1):
        title = paper.get("title") or paper.get("id") or "Untitled"
        fit = paper.get("strategic_fit") or {}
        badge = ""
        if fit.get("fit_score") is not None:
            action = fit.get("recommended_action") or "unscored"
            badge = f" — {action} · {fit['fit_score']}/100"
        lines.append(f"### {i}. {title}{badge}")
        lines.append("")
        authors = paper.get("authors") or []
        if authors:
            lines.append(", ".join(authors[:8]) + (" et al." if len(authors) > 8 else ""))
            lines.append("")
        meta = []
        if paper.get("published_date"):
            meta.append(paper["published_date"])
        if paper.get("matched_topic"):
            meta.append(f"topic: {paper['matched_topic']}")
        if paper.get("landing_url"):
            meta.append(paper["landing_url"])
        if meta:
            lines.append(" · ".join(str(m) for m in meta))
            lines.append("")
        if fit.get("relevance_summary"):
            lines.append(fit["relevance_summary"])
            lines.append("")
        for label, key in (("Opportunities", "opportunities"), ("Threats", "threats")):
            items = fit.get(key) or []
            if items:
                lines.append(f"**{label}:**")
                for item in items:
                    lines.append(f"- {item}")
                lines.append("")
        abstract = (paper.get("abstract") or "").strip()
        if abstract:
            snippet = abstract if len(abstract) <= 600 else abstract[:597] + "..."
            lines.append(snippet)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def save_run(run: AppImproveRun) -> AppImproveRun:
    directory = _run_dir(run.id)
    directory.mkdir(parents=True, exist_ok=True)
    payload = run.model_dump()
    with open(_run_json_path(run.id), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    with open(_run_md_path(run.id), "w", encoding="utf-8") as f:
        f.write(run_to_markdown(run))

    summary = _summary_from_run(run).model_dump()
    index = [e for e in _load_index() if e.get("id") != run.id]
    index.insert(0, summary)
    _save_index(index)
    return run


def list_runs() -> List[AppImproveRunSummary]:
    return [AppImproveRunSummary(**e) for e in _load_index()]


def get_run(run_id: str) -> Optional[AppImproveRun]:
    path = _run_json_path(run_id)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return AppImproveRun(**json.load(f))
    except Exception as exc:
        print(f"app_improve: failed to read run {run_id}: {exc}")
        return None


def get_run_markdown(run_id: str) -> Optional[str]:
    path = _run_md_path(run_id)
    if path.exists():
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            pass
    run = get_run(run_id)
    return run_to_markdown(run) if run else None


def delete_run(run_id: str) -> bool:
    directory = _run_dir(run_id)
    existed = directory.exists() or any(e.get("id") == run_id for e in _load_index())
    if directory.exists():
        shutil.rmtree(directory, ignore_errors=True)
    index = [e for e in _load_index() if e.get("id") != run_id]
    _save_index(index)
    return existed


def persist_discovery(
    *,
    app_description: str,
    improvement_direction: str,
    since: Optional[str],
    limit_per_topic: int,
    score_top: int,
    topics_searched: List[str],
    topics_rationale: Optional[str],
    papers: List[Dict[str, Any]],
    error: Optional[str],
) -> AppImproveRun:
    created_at = datetime.now().isoformat()
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    run = AppImproveRun(
        id=run_id,
        created_at=created_at,
        app_description=app_description,
        improvement_direction=improvement_direction,
        since=since,
        limit_per_topic=limit_per_topic,
        score_top=score_top,
        topics_searched=topics_searched,
        topics_rationale=topics_rationale,
        papers=papers,
        count=len(papers),
        error=error,
        top_fit_score=_top_fit_score(papers),
    )
    return save_run(run)


async def derive_search_topics(
    app_description: str,
    improvement_direction: str,
) -> SearchTopics:
    """Ask the LLM for OpenAlex queries; fall back to the improvement text."""
    user_prompt = (
        f"## Product / app\n{app_description.strip()}\n\n"
        f"## Intended improvement\n{improvement_direction.strip()}\n\n"
        "Propose academic search queries that would surface papers useful for this improvement."
    )
    try:
        topics, _usage = await llm_clients.parse_structured(
            role="app_improve_topics",
            schema=SearchTopics,
            system=TOPIC_SYSTEM_PROMPT,
            user=user_prompt,
        )
        cleaned = [t.strip() for t in topics.topics if t and t.strip()]
        if cleaned:
            return SearchTopics(topics=cleaned[:6], rationale=topics.rationale)
    except Exception as exc:
        print(f"app_improve: topic derivation failed, using fallback: {exc}")

    fallback = _fallback_topics(improvement_direction)
    if not fallback:
        fallback = _fallback_topics(app_description)
    return SearchTopics(
        topics=fallback,
        rationale="Fallback: used the improvement direction as a single search query.",
    )


async def discover_for_app(
    app_description: str,
    improvement_direction: str,
    limit_per_topic: int = 5,
    since: Optional[str] = None,
    score_top: int = 5,
    topics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Derive topics (unless provided), search OpenAlex, optionally score the
    top results against an ephemeral product profile, and rank by fit.
    """
    app_description = app_description.strip()
    improvement_direction = improvement_direction.strip()
    if not app_description or not improvement_direction:
        return {
            "success": False,
            "run_id": None,
            "created_at": None,
            "topics_searched": [],
            "topics_rationale": None,
            "papers": [],
            "count": 0,
            "error": "Both app_description and improvement_direction are required.",
        }

    if topics:
        derived = SearchTopics(topics=[t.strip() for t in topics if t.strip()][:6], rationale="")
    else:
        derived = await derive_search_topics(app_description, improvement_direction)

    if not derived.topics:
        return {
            "success": False,
            "run_id": None,
            "created_at": None,
            "topics_searched": [],
            "topics_rationale": derived.rationale or None,
            "papers": [],
            "count": 0,
            "error": "Could not derive search topics from the description.",
        }

    profile = ephemeral_profile(app_description, improvement_direction, derived.topics)

    seen: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []
    for topic in derived.topics:
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

    merged = list(seen.values())

    if score_top > 0:
        for record in merged[:score_top]:
            fit = await score_paper_for_profile(record, profile, cache_key=None)
            if fit.get("success"):
                record["strategic_fit"] = fit["assessment"]
            else:
                record["strategic_fit_error"] = fit.get("error")

        def _rank_key(rec: Dict[str, Any]) -> tuple:
            fit = rec.get("strategic_fit") or {}
            score = fit.get("fit_score")
            if score is None:
                return (1, 0)
            return (0, -int(score))

        merged.sort(key=_rank_key)

    run = persist_discovery(
        app_description=app_description,
        improvement_direction=improvement_direction,
        since=since,
        limit_per_topic=limit_per_topic,
        score_top=score_top,
        topics_searched=derived.topics,
        topics_rationale=derived.rationale or None,
        papers=merged,
        error="; ".join(errors) if errors else None,
    )

    return {
        "success": True,
        "run_id": run.id,
        "created_at": run.created_at,
        "topics_searched": run.topics_searched,
        "topics_rationale": run.topics_rationale,
        "papers": run.papers,
        "count": run.count,
        "error": run.error,
    }
