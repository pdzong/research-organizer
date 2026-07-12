"""Tests for company profiles (P2-001) and strategic-fit plumbing (P2-002)."""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from services import company_profiles
from services.company_profiles import CompanyProfile, CompanyProfileInput
from services.strategic_fit import (
    StrategicFitAssessment,
    _paper_block,
    _profile_block,
    score_paper_for_profile,
)

SAMPLE_INPUT = CompanyProfileInput(
    name="Acme Conversational AI",
    industry="Customer support software",
    description="Builds chat-based customer support bots for e-commerce.",
    tech_stack=["Python", "RAG pipelines", "fine-tuned small LLMs"],
    strategic_questions=["Will on-device LLMs make our cloud offering obsolete?"],
    watch_topics=["retrieval augmented generation", "small language models"],
    assumptions=["Customers will keep paying for cloud-hosted inference"],
)


def _with_temp_store(fn):
    """Run ``fn`` with PROFILES_FILE pointed at a temp file."""
    with tempfile.TemporaryDirectory() as tmp:
        store_file = Path(tmp) / "company_profiles.json"
        with patch.object(company_profiles, "PROFILES_FILE", store_file):
            fn()


def test_create_and_activate_profile():
    def run():
        profile = company_profiles.create_profile(SAMPLE_INPUT)
        assert profile.id == "acme-conversational-ai"
        assert profile.created_at

        # First profile becomes active automatically
        assert company_profiles.get_active_profile_id() == profile.id
        active = company_profiles.get_active_profile()
        assert active and active.name == SAMPLE_INPUT.name

        # Second profile with same name gets a suffixed id
        second = company_profiles.create_profile(SAMPLE_INPUT)
        assert second.id == "acme-conversational-ai-2"
        assert company_profiles.get_active_profile_id() == profile.id

        assert company_profiles.set_active_profile(second.id)
        assert company_profiles.get_active_profile_id() == second.id

    _with_temp_store(run)


def test_update_and_delete_profile():
    def run():
        profile = company_profiles.create_profile(SAMPLE_INPUT)

        updated_input = SAMPLE_INPUT.model_copy(update={"industry": "Fintech"})
        updated = company_profiles.update_profile(profile.id, updated_input)
        assert updated and updated.industry == "Fintech"
        assert updated.created_at == profile.created_at

        assert company_profiles.delete_profile(profile.id)
        assert company_profiles.get_profile(profile.id) is None
        assert company_profiles.get_active_profile_id() is None
        assert not company_profiles.delete_profile("nope")

    _with_temp_store(run)


def test_prompt_blocks_include_profile_and_paper_fields():
    profile = CompanyProfile(id="acme", created_at="", updated_at="", **SAMPLE_INPUT.model_dump())
    block = _profile_block(profile)
    assert "Acme Conversational AI" in block
    assert "on-device LLMs" in block
    assert "cloud-hosted inference" in block

    paper = {
        "id": "openalex:W123",
        "title": "Tiny RAG on the Edge",
        "authors": ["A", "B"],
        "abstract": "We run retrieval-augmented generation fully on-device.",
        "source_metadata": {"topics": ["Language models"]},
    }
    pblock = _paper_block(paper, cache_key=None)
    assert "Tiny RAG on the Edge" in pblock
    assert "fully on-device" in pblock


def test_score_paper_for_profile_mocked_llm():
    profile = CompanyProfile(id="acme", created_at="", updated_at="", **SAMPLE_INPUT.model_dump())
    paper = {
        "id": "openalex:W123",
        "title": "Tiny RAG on the Edge",
        "abstract": "On-device retrieval-augmented generation.",
    }
    fake = StrategicFitAssessment(
        fit_score=85,
        relevance_summary="Directly challenges the cloud-inference assumption.",
        opportunities=["Ship an on-device tier"],
        threats=["Cloud offering becomes obsolete"],
        challenged_assumptions=["Customers will keep paying for cloud-hosted inference"],
        recommended_action="analyze",
        reasoning="High overlap with the company's core product.",
    )

    with patch(
        "services.strategic_fit.llm_clients.parse_structured",
        new=AsyncMock(return_value=(fake, {"model": "test"})),
    ):
        result = asyncio.run(score_paper_for_profile(paper, profile, cache_key=None))

    assert result["success"], result.get("error")
    assessment = result["assessment"]
    assert assessment["fit_score"] == 85
    assert assessment["recommended_action"] == "analyze"
    assert assessment["profile_id"] == "acme"
    assert assessment["paper_id"] == "openalex:W123"


def test_score_requires_abstract_or_analysis():
    profile = CompanyProfile(id="acme", created_at="", updated_at="", **SAMPLE_INPUT.model_dump())
    result = asyncio.run(
        score_paper_for_profile({"id": "x", "title": "No abstract"}, profile, cache_key=None)
    )
    assert not result["success"]
    assert "abstract" in result["error"]


if __name__ == "__main__":
    test_create_and_activate_profile()
    test_update_and_delete_profile()
    test_prompt_blocks_include_profile_and_paper_fields()
    test_score_paper_for_profile_mocked_llm()
    test_score_requires_abstract_or_analysis()
    print("All company profile tests passed.")
