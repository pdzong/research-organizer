"""Tests for curated & live LLM model catalog listing, pricing metadata, and fast caching."""

import asyncio
from types import SimpleNamespace
from unittest.mock import patch

from services import llm_clients
from services.llm_clients import (
    _keep_gemini_chat_model,
    _keep_openai_chat_model,
    _model_sort_key,
    _unique_sorted,
    clear_live_catalog_cache,
    list_all_provider_models,
)
from services.llm_config import (
    CURATED_MODELS,
    DEFAULTS,
    provider_health,
)


def test_defaults_use_modern_models():
    assert DEFAULTS["deep_analysis"]["model"] == "gpt-5.6"
    assert DEFAULTS["sections"]["model"] == "gpt-5.6-mini"
    assert DEFAULTS["plan_synthesis"]["model"] == "gpt-5.6"


def test_curated_models_include_gpt56_and_pricing():
    openai_models = {m["id"]: m for m in CURATED_MODELS["openai"]}
    assert "gpt-5.6" in openai_models
    assert openai_models["gpt-5.6"]["input_price_per_1m"] == 2.50
    assert openai_models["gpt-5.6"]["output_price_per_1m"] == 10.00
    assert "gpt-5.6-mini" in openai_models
    assert openai_models["gpt-5.6-mini"]["tier"] == "fast"

    anthropic_models = {m["id"]: m for m in CURATED_MODELS["anthropic"]}
    assert "claude-sonnet-4-6" in anthropic_models
    assert "claude-3-7-sonnet" in anthropic_models


def test_openai_filter_keeps_chat_drops_audio():
    assert _keep_openai_chat_model("gpt-5.6")
    assert _keep_openai_chat_model("gpt-5.6-turbo")
    assert _keep_openai_chat_model("gpt-5.4-nano")
    assert _keep_openai_chat_model("o3-mini")
    assert _keep_openai_chat_model("chatgpt-4o-latest")
    assert not _keep_openai_chat_model("whisper-1")
    assert not _keep_openai_chat_model("gpt-4o-mini-tts")
    assert not _keep_openai_chat_model("text-embedding-3-small")
    assert not _keep_openai_chat_model("dall-e-3")


def test_model_sort_key_prioritizes_modern_models():
    sorted_models = _unique_sorted(["gpt-4o", "gpt-5.6", "gpt-5.4", "gpt-5.6-turbo", "o3-mini"])
    assert sorted_models[0] in ("gpt-5.6", "gpt-5.6-turbo")
    assert sorted_models.index("gpt-5.6") < sorted_models.index("gpt-4o")


def test_gemini_filter_keeps_flash_drops_imagen():
    assert _keep_gemini_chat_model("gemini-3.7-flash")
    assert _keep_gemini_chat_model("gemini-2.5-pro")
    assert not _keep_gemini_chat_model("gemini-2.5-flash-image")
    assert not _keep_gemini_chat_model("text-embedding-004")
    assert not _keep_gemini_chat_model("imagen-4.0-generate")


def test_provider_health_merges_live_and_curated():
    health = provider_health(
        live_catalog={
            "openai": {
                "models": ["gpt-5.6-custom-run", "gpt-5.6"],
                "source": "live",
                "error": None,
            }
        }
    )
    # The live models should be present first
    assert health["openai"]["suggested_models"][0] == "gpt-5.6-custom-run"
    assert health["openai"]["suggested_models"][1] == "gpt-5.6"
    assert health["openai"]["models_source"] == "live"

    # Known model retains rich pricing
    models_by_id = {m["id"]: m for m in health["openai"]["models"]}
    assert models_by_id["gpt-5.6"]["input_price_per_1m"] == 2.50
    assert models_by_id["gpt-5.6"]["source"] == "live"
    assert models_by_id["gpt-5.6-custom-run"]["tier"] == "custom"

    # Curated models still available in fallback list
    assert "gpt-5.6-mini" in health["openai"]["suggested_models"]


def test_provider_health_curated_when_no_live_data():
    health = provider_health()
    assert health["openai"]["models_source"] == "curated"
    assert "gpt-5.6" in health["openai"]["suggested_models"]
    models_by_id = {m["id"]: m for m in health["openai"]["models"]}
    assert models_by_id["gpt-5.6"]["input_price_per_1m"] == 2.50


def test_list_all_provider_models_with_caching():
    clear_live_catalog_cache()
    call_count = 0

    def fake_list(provider: str):
        nonlocal call_count
        call_count += 1
        if provider == "openai":
            return ["gpt-5.6", "gpt-5.6-turbo"]
        raise RuntimeError("no key")

    with patch.object(llm_clients, "list_provider_models", side_effect=fake_list):
        # First call fetches live
        res1 = asyncio.run(list_all_provider_models(providers=["openai"], force_refresh=False))
        assert call_count == 1
        assert res1["openai"]["source"] == "live"
        assert res1["openai"]["models"] == ["gpt-5.6", "gpt-5.6-turbo"]

        # Second call should use cache without invoking fake_list again
        res2 = asyncio.run(list_all_provider_models(providers=["openai"], force_refresh=False))
        assert call_count == 1
        assert res2["openai"]["source"] == "live"

        # Force refresh should bypass cache
        res3 = asyncio.run(list_all_provider_models(providers=["openai"], force_refresh=True))
        assert call_count == 2
        assert res3["openai"]["source"] == "live"


def test_iter_openai_style_listing():
    listing = SimpleNamespace(
        data=[SimpleNamespace(id="gpt-5.6"), SimpleNamespace(id="whisper-1")]
    )
    ids = llm_clients._iter_model_ids(listing)
    assert ids == ["gpt-5.6", "whisper-1"]


if __name__ == "__main__":
    test_defaults_use_modern_models()
    test_curated_models_include_gpt56_and_pricing()
    test_openai_filter_keeps_chat_drops_audio()
    test_model_sort_key_prioritizes_modern_models()
    test_gemini_filter_keeps_flash_drops_imagen()
    test_provider_health_merges_live_and_curated()
    test_provider_health_curated_when_no_live_data()
    test_list_all_provider_models_with_caching()
    test_iter_openai_style_listing()
    print("All curated & live LLM model catalog tests passed.")
