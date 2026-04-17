"""
Agentic pipeline that turns an `application` (a domain + utility + a set of
related papers) into a concrete, codegen-ready `SolutionPlan`.

Design notes
------------
The pipeline mirrors the rest of the codebase:

* Multi-step prompting (gather → synthesize → harden) using the same
  ``client.responses.parse`` Structured Outputs interface as
  ``openai_service.summarize_paper``.
* Re-uses *cached* paper analyses / metadata when available so the planner
  stays cheap. If a paper's cache is missing we fall back to its title /
  abstract from Semantic Scholar (best-effort).
* Same model names already in use in the project (``gpt-5.2`` for synthesis,
  ``gpt-5-mini`` for the cheaper aggregation step). We deliberately do not
  introduce new model names.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import cache_service
from .models import (
    ApplicationIdea,
    SolutionPlan,
)
from .openai_service import get_openai_client
from .semantic_scholar import get_paper_metadata


# ─── Context assembly ────────────────────────────────────────────────────────


def _summarise_paper_context(arxiv_id: str, title: str) -> Dict[str, Any]:
    """Pull whatever rich context we already have cached for a paper."""
    out: Dict[str, Any] = {"arxiv_id": arxiv_id, "title": title}

    analysis = cache_service.load_analysis(arxiv_id) if arxiv_id else None
    if analysis and analysis.get("data"):
        data = analysis["data"]
        out["main_contribution"] = (
            data.get("summary", {}).get("main_contribution") or ""
        )
        out["methodology"] = data.get("summary", {}).get("methodology") or ""
        out["novelty"] = (
            data.get("novelty", {}).get("novelty_summary") or ""
        )
        out["github_repo"] = data.get("github_repo") or ""

    metadata = cache_service.load_metadata(arxiv_id) if arxiv_id else None
    if metadata:
        out.setdefault("abstract", metadata.get("abstract") or "")
        out.setdefault("tldr", metadata.get("tldr") or "")
        out.setdefault("year", metadata.get("year"))

    return out


async def _ensure_paper_context(
    arxiv_id: Optional[str], title: str
) -> Dict[str, Any]:
    """Like ``_summarise_paper_context`` but tries Semantic Scholar if cache is empty."""
    if not arxiv_id:
        return {"title": title, "arxiv_id": None, "abstract": ""}

    ctx = _summarise_paper_context(arxiv_id, title)
    if ctx.get("abstract") or ctx.get("main_contribution"):
        return ctx

    try:
        meta = await get_paper_metadata(arxiv_id, include_related=False)
        if meta.get("success"):
            cache_service.save_metadata(arxiv_id, meta)
            ctx["abstract"] = meta.get("abstract") or ""
            ctx["tldr"] = meta.get("tldr") or ""
            ctx["year"] = meta.get("year")
    except Exception as e:  # pragma: no cover - best effort
        print(f"⚠️ planner: could not enrich {arxiv_id}: {e}")

    return ctx


def _format_paper_context(ctx: Dict[str, Any]) -> str:
    parts = [f"### {ctx.get('title', 'Untitled')}"]
    if ctx.get("arxiv_id"):
        parts.append(f"_arxiv: {ctx['arxiv_id']}_")
    if ctx.get("tldr"):
        parts.append(f"**TLDR:** {ctx['tldr']}")
    if ctx.get("main_contribution"):
        parts.append(f"**Main contribution:** {ctx['main_contribution']}")
    if ctx.get("novelty"):
        parts.append(f"**Novelty:** {ctx['novelty']}")
    if ctx.get("methodology"):
        parts.append(f"**Methodology:** {ctx['methodology']}")
    if ctx.get("abstract"):
        parts.append(f"**Abstract:** {ctx['abstract'][:1500]}")
    if ctx.get("github_repo"):
        parts.append(f"**Code:** {ctx['github_repo']}")
    return "\n\n".join(parts)


# ─── Agentic steps ───────────────────────────────────────────────────────────


_BRIEF_SYSTEM_PROMPT = """
You are a Principal Engineer + Product Lead. From the supplied scientific
context, write a tight technical brief (max ~300 words) that frames an
end-user product / system. Focus on:

1. The concrete problem solved.
2. Which scientific results from the supplied papers make this *now*
   feasible (cite them by title or arxiv id).
3. The 1-3 most differentiating capabilities the product should expose.

Be specific. Avoid corporate fluff. Output plain markdown — no headings.
""".strip()


_PLAN_SYSTEM_PROMPT = """
You are a Principal Solutions Architect. You receive:

1. A target Application (domain + specific utility).
2. Rich context for the source paper and related papers.
3. A short technical brief.

Produce a complete, codegen-ready `SolutionPlan`. Constraints:

* Be **specific and concrete**: pick a real tech stack, name modules with
  real responsibilities, give APIs concrete paths and methods.
* Tie every architectural choice back to the supplied papers — populate the
  `paper_grounding` field of each module with the papers whose results
  justify it.
* The `code_generation_prompt` must be a self-contained instruction set a
  downstream code-gen agent could execute without seeing this conversation:
  restate scope, tech stack, APIs, data models, and acceptance criteria.
* Keep `architecture_diagram` as plain ASCII or mermaid (no surrounding
  fences) so it can be embedded later.
* Prefer 3-7 modules, 2-5 milestones, 3-6 success metrics.

Quality bar: the result should be good enough that a senior engineer can
start building from it without asking clarifying questions about the
*scope*.
""".strip()


async def _draft_brief(
    application: ApplicationIdea,
    paper_contexts: List[Dict[str, Any]],
    model_id: str = "gpt-5-mini",
) -> str:
    """Step 1: cheap pass that turns raw paper context into a tight brief."""
    client = get_openai_client()

    user_prompt = (
        f"## Target application\n"
        f"- Domain: {application.domain}\n"
        f"- Utility: {application.specific_utility}\n\n"
        f"## Scientific context\n\n"
        + "\n\n---\n\n".join(_format_paper_context(c) for c in paper_contexts)
    )

    response = client.responses.create(
        model=model_id,
        input=[
            {"role": "system", "content": _BRIEF_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    # The Responses API exposes the aggregated text via ``output_text``.
    return getattr(response, "output_text", "") or ""


async def _draft_plan(
    application: ApplicationIdea,
    paper_contexts: List[Dict[str, Any]],
    brief: str,
    model_id: str = "gpt-5.2",
) -> SolutionPlan:
    """Step 2: synthesize the structured `SolutionPlan`."""
    client = get_openai_client()

    user_prompt = (
        f"## Target application\n"
        f"- Domain: {application.domain}\n"
        f"- Specific utility: {application.specific_utility}\n\n"
        f"## Technical brief (drafted in step 1)\n{brief}\n\n"
        f"## Scientific context\n\n"
        + "\n\n---\n\n".join(_format_paper_context(c) for c in paper_contexts)
    )

    response = client.responses.parse(
        model=model_id,
        input=[
            {"role": "system", "content": _PLAN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        text_format=SolutionPlan,
    )
    plan: SolutionPlan = response.output_parsed
    return plan


# ─── Public API ──────────────────────────────────────────────────────────────


async def generate_solution_plan(
    application_entry: Dict[str, Any],
    brief_model_id: str = "gpt-5-mini",
    plan_model_id: str = "gpt-5.2",
) -> Dict[str, Any]:
    """
    Generate a SolutionPlan from an application entry stored in
    ``applications.json``.

    Parameters
    ----------
    application_entry: the JSON entry as returned by ``cache_service.load_applications()``.

    Returns
    -------
    A dict with keys: ``success``, ``plan`` (dict), ``markdown`` (str),
    ``usage``, ``error``.
    """
    try:
        app = ApplicationIdea(**application_entry["application"])
        current_paper = application_entry.get("current_paper") or {}
        related_papers = application_entry.get("related_papers") or []

        print(
            f"\n🧠 Generating solution plan for application "
            f"'{app.domain}' (source paper: {current_paper.get('arxiv_id')})"
        )

        # Build context (current paper first — it carries the most weight)
        ctxs: List[Dict[str, Any]] = []
        ctxs.append(
            await _ensure_paper_context(
                current_paper.get("arxiv_id"),
                current_paper.get("title", ""),
            )
        )
        for rp in related_papers:
            ctxs.append(
                await _ensure_paper_context(
                    rp.get("arxiv_id"), rp.get("title", "")
                )
            )

        brief = await _draft_brief(app, ctxs, model_id=brief_model_id)
        print(f"📝 Brief drafted ({len(brief)} chars)")

        plan = await _draft_plan(app, ctxs, brief, model_id=plan_model_id)
        markdown = plan.to_markdown()
        print(f"✅ Plan generated: {plan.name}")

        return {
            "success": True,
            "plan": plan.model_dump(),
            "markdown": markdown,
            "brief": brief,
            "error": None,
        }

    except Exception as e:
        print(f"❌ Solution planner failed: {e}")
        return {
            "success": False,
            "plan": None,
            "markdown": None,
            "brief": None,
            "error": str(e),
        }
