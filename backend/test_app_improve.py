"""Tests for ad-hoc app-improvement discovery and run persistence."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from services import app_improve
from services.app_improve import (
    AppImproveRun,
    SearchTopics,
    delete_run,
    derive_search_topics,
    discover_for_app,
    ephemeral_profile,
    get_run,
    get_run_markdown,
    list_runs,
    run_to_markdown,
    save_run,
)
from services.source_paper import SourcePaper
from services.strategic_fit import StrategicFitAssessment


def _with_temp_runs(fn):
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(app_improve, "RUNS_DIR", Path(tmp)):
            fn()


def test_ephemeral_profile_maps_description_and_direction():
    profile = ephemeral_profile(
        "Voice notes app for clinicians. Records visits and drafts SOAP notes.",
        "Reduce hallucination in generated clinical summaries",
        topics=["clinical note generation", "factuality in summarization"],
    )
    assert profile.id == "adhoc-app"
    assert "Voice notes app" in profile.name
    assert "SOAP notes" in (profile.description or "")
    assert profile.strategic_questions == ["Reduce hallucination in generated clinical summaries"]
    assert profile.watch_topics == ["clinical note generation", "factuality in summarization"]


def test_derive_search_topics_mocked_llm():
    fake = SearchTopics(
        topics=["clinical note generation", "hallucination mitigation summarization"],
        rationale="Covers the product and the quality goal.",
    )
    with patch(
        "services.app_improve.llm_clients.parse_structured",
        new=AsyncMock(return_value=(fake, {"model": "test"})),
    ):
        result = asyncio.run(
            derive_search_topics(
                "Voice notes for clinicians",
                "Cut hallucinations in SOAP notes",
            )
        )
    assert result.topics == fake.topics
    assert "quality goal" in result.rationale


def test_derive_search_topics_falls_back_when_llm_fails():
    with patch(
        "services.app_improve.llm_clients.parse_structured",
        new=AsyncMock(side_effect=RuntimeError("no key")),
    ):
        result = asyncio.run(
            derive_search_topics(
                "A recipe app",
                "personalized meal planning from pantry inventory",
            )
        )
    assert result.topics == ["personalized meal planning from pantry inventory"]
    assert "Fallback" in result.rationale


def test_discover_for_app_requires_both_fields():
    def run():
        result = asyncio.run(discover_for_app("only description", "   "))
        assert not result["success"]
        assert "required" in result["error"]
        assert result.get("run_id") is None
        assert list_runs() == []

    _with_temp_runs(run)


def test_discover_for_app_searches_scores_ranks_and_saves():
    papers = [
        SourcePaper(
            id="openalex:W1",
            source="openalex",
            source_record_id="W1",
            title="Low-fit paper",
            abstract="Unrelated work on astronomy.",
        ),
        SourcePaper(
            id="openalex:W2",
            source="openalex",
            source_record_id="W2",
            title="High-fit paper",
            abstract="Factuality metrics for clinical summarization.",
        ),
    ]

    async def fake_search(*, query, limit, since, open_access_only):
        return papers

    async def fake_score(paper, profile, cache_key=None, force_reload=False):
        score = 90 if paper["id"] == "openalex:W2" else 20
        assessment = StrategicFitAssessment(
            fit_score=score,
            relevance_summary="fit" if score > 50 else "weak",
            opportunities=[],
            threats=[],
            challenged_assumptions=[],
            recommended_action="analyze" if score > 50 else "ignore",
            reasoning="test",
        ).model_dump()
        assessment["profile_id"] = profile.id
        assessment["paper_id"] = paper["id"]
        return {"success": True, "assessment": assessment, "from_cache": False, "error": None}

    def run():
        with patch("services.app_improve.search_openalex_works", new=fake_search), patch(
            "services.app_improve.score_paper_for_profile", new=fake_score
        ):
            result = asyncio.run(
                discover_for_app(
                    "Voice notes for clinicians",
                    "Cut hallucinations in SOAP notes",
                    topics=["clinical summarization"],
                    score_top=2,
                )
            )

        assert result["success"]
        assert result["run_id"]
        assert result["topics_searched"] == ["clinical summarization"]
        assert result["count"] == 2
        assert result["papers"][0]["id"] == "openalex:W2"
        assert result["papers"][0]["strategic_fit"]["fit_score"] == 90
        assert result["papers"][1]["id"] == "openalex:W1"

        saved = get_run(result["run_id"])
        assert saved is not None
        assert saved.app_description == "Voice notes for clinicians"
        assert saved.improvement_direction == "Cut hallucinations in SOAP notes"
        assert saved.top_fit_score == 90
        assert saved.papers[0]["id"] == "openalex:W2"

        summaries = list_runs()
        assert len(summaries) == 1
        assert summaries[0].id == result["run_id"]
        assert summaries[0].count == 2

        markdown = get_run_markdown(result["run_id"])
        assert markdown and "High-fit paper" in markdown
        assert "analyze · 90/100" in markdown

    _with_temp_runs(run)


def test_save_list_get_delete_run():
    def run():
        artifact = AppImproveRun(
            id="demo-run",
            created_at="2026-08-13T12:00:00",
            app_description="A notes app",
            improvement_direction="Better search",
            topics_searched=["neural retrieval"],
            papers=[{"id": "openalex:W9", "title": "Dense retrieval", "strategic_fit": {"fit_score": 70, "recommended_action": "watch", "relevance_summary": "Useful."}}],
            count=1,
            top_fit_score=70,
        )
        save_run(artifact)
        assert list_runs()[0].id == "demo-run"
        loaded = get_run("demo-run")
        assert loaded and loaded.papers[0]["title"] == "Dense retrieval"
        md = run_to_markdown(loaded)
        assert "Better search" in md
        assert delete_run("demo-run")
        assert get_run("demo-run") is None
        assert list_runs() == []
        assert not delete_run("demo-run")

    _with_temp_runs(run)


if __name__ == "__main__":
    test_ephemeral_profile_maps_description_and_direction()
    test_derive_search_topics_mocked_llm()
    test_derive_search_topics_falls_back_when_llm_fails()
    test_discover_for_app_requires_both_fields()
    test_discover_for_app_searches_scores_ranks_and_saves()
    test_save_list_get_delete_run()
    print("All app-improve tests passed.")
