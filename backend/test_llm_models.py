"""Tests for live LLM model catalog listing and fallback."""

import asyncio
from types import SimpleNamespace
from unittest.mock import patch

from services import llm_clients
from services.llm_clients import (
    _keep_gemini_chat_model,
    _keep_openai_chat_model,
    list_all_provider_models,
)
from services.llm_config import provider_health


def test_openai_filter_keeps_chat_drops_audio():
    assert _keep_openai_chat_model("gpt-5.6-sol")
    assert _keep_openai_chat_model("gpt-5.4-nano")
    assert _keep_openai_chat_model("o3-mini")
    assert not _keep_openai_chat_model("whisper-1")
    assert not _keep_openai_chat_model("gpt-4o-mini-tts")
    assert not _keep_openai_chat_model("text-embedding-3-small")
    assert not _keep_openai_chat_model("dall-e-3")


def test_gemini_filter_keeps_flash_drops_imagen():
    assert _keep_gemini_chat_model("gemini-3.6-flash")
    assert _keep_gemini_chat_model("gemini-2.5-pro")
    assert not _keep_gemini_chat_model("gemini-2.5-flash-image")
    assert not _keep_gemini_chat_model("text-embedding-004")
    assert not _keep_gemini_chat_model("imagen-4.0-generate")


def test_provider_health_uses_live_catalog_when_present():
    health = provider_health(
        live_catalog={
            "openai": {
                "models": ["gpt-5.6-sol", "gpt-5.6-luna"],
                "source": "live",
                "error": None,
            }
        }
    )
    assert health["openai"]["suggested_models"] == ["gpt-5.6-sol", "gpt-5.6-luna"]
    assert health["openai"]["models_source"] == "live"
    assert health["anthropic"]["models_source"] == "fallback"
    assert "claude-sonnet-4-5" in health["anthropic"]["suggested_models"]


def test_provider_health_falls_back_on_empty_live_list():
    health = provider_health(
        live_catalog={"openai": {"models": [], "source": "fallback", "error": "timeout"}}
    )
    assert health["openai"]["models_source"] == "fallback"
    assert health["openai"]["models_error"] == "timeout"
    assert "gpt-5.4" in health["openai"]["suggested_models"]


def test_list_all_provider_models_live_and_error():
    def fake_list(provider: str):
        if provider == "openai":
            return ["gpt-5.6-sol", "gpt-5.4"]
        raise RuntimeError("no key")

    with patch.object(llm_clients, "list_provider_models", side_effect=fake_list):
        result = asyncio.run(list_all_provider_models(providers=["openai", "anthropic"]))

    assert result["openai"]["source"] == "live"
    assert result["openai"]["models"][0] == "gpt-5.6-sol"
    assert result["anthropic"]["source"] == "fallback"
    assert "no key" in result["anthropic"]["error"]


def test_iter_openai_style_listing():
    listing = SimpleNamespace(
        data=[SimpleNamespace(id="gpt-5.6-sol"), SimpleNamespace(id="whisper-1")]
    )
    ids = llm_clients._iter_model_ids(listing)
    assert ids == ["gpt-5.6-sol", "whisper-1"]


if __name__ == "__main__":
    test_openai_filter_keeps_chat_drops_audio()
    test_gemini_filter_keeps_flash_drops_imagen()
    test_provider_health_uses_live_catalog_when_present()
    test_provider_health_falls_back_on_empty_live_list()
    test_list_all_provider_models_live_and_error()
    test_iter_openai_style_listing()
    print("All llm model catalog tests passed.")
