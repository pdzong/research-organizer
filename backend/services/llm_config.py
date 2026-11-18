"""
Per-role LLM provider / model configuration.

The backend makes LLM calls for several *roles* (e.g. "deep analysis",
"section extraction", "relevance filter", "solution plan synthesis"). Each
role has a default provider + model, but users can override them at runtime
via ``PUT /api/config/llm`` from the UI.

Persistence model
-----------------
* Roles + defaults live in this file (code-level constants).
* User overrides are persisted to ``backend/data/llm_config.json``.
* On read we merge: ``defaults | persisted_overrides``.

Provider naming
---------------
* ``openai``   — OpenAI Platform (``OPENAI_API_KEY``).
* ``anthropic`` — Anthropic Claude (``ANTHROPIC_API_KEY``).
* ``gemini``   — Google Gemini (``GOOGLE_API_KEY`` or ``GEMINI_API_KEY``).
* ``local_vllm`` — Local vLLM OpenAI-compatible endpoint.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional


CONFIG_FILE = Path(__file__).parent.parent / "data" / "llm_config.json"


# ─── Roles ────────────────────────────────────────────────────────────────

ROLES: Dict[str, str] = {
    "deep_analysis": "Full paper analysis (novelty, benchmarks, applications).",
    "sections": "Cheap pass that segments raw OCR markdown into sections.",
    "relevance": "Yes/no filter that checks if a paper matches an application.",
    "plan_brief": "Cheap aggregation pass that drafts a brief before plan synthesis.",
    "plan_synthesis": "Structured SolutionPlan synthesis.",
    "plan_worthy": "Gate that decides whether an auto-derived application is worth turning into a full plan.",
    "strategic_fit": "Scores a paper against a company research profile (opportunities, threats, fit).",
    "app_improve_topics": "Derives academic search queries from an app description and improvement direction.",
}


# ─── Known providers & Curated Model Catalog ───────────────────────────────

CURATED_MODELS: Dict[str, List[Dict[str, Any]]] = {
    "openai": [
        {
            "id": "gpt-5.6",
            "name": "GPT-5.6 Flagship",
            "input_price_per_1m": 2.50,
            "output_price_per_1m": 10.00,
            "context_window": "1M tokens",
            "tier": "flagship",
            "description": "Frontier multimodal reasoning; highest accuracy for deep paper analysis and system synthesis.",
            "recommended_for": ["deep_analysis", "plan_synthesis"],
        },
        {
            "id": "gpt-5.6-turbo",
            "name": "GPT-5.6 Turbo",
            "input_price_per_1m": 1.50,
            "output_price_per_1m": 6.00,
            "context_window": "1M tokens",
            "tier": "balanced",
            "description": "High-throughput frontier model; great balance of depth and speed.",
            "recommended_for": ["deep_analysis", "plan_synthesis", "strategic_fit"],
        },
        {
            "id": "gpt-5.6-sol-medium",
            "name": "GPT-5.6 Sol Medium",
            "input_price_per_1m": 1.00,
            "output_price_per_1m": 4.00,
            "context_window": "500k tokens",
            "tier": "balanced",
            "description": "Efficient reasoning model with fast structured generation.",
            "recommended_for": ["plan_brief", "strategic_fit", "app_improve_topics"],
        },
        {
            "id": "gpt-5.6-mini",
            "name": "GPT-5.6 Mini",
            "input_price_per_1m": 0.15,
            "output_price_per_1m": 0.60,
            "context_window": "256k tokens",
            "tier": "fast",
            "description": "Ultra-fast and cost-effective; ideal for section extraction, relevance filtering, and topic derivation.",
            "recommended_for": ["sections", "relevance", "plan_worthy", "app_improve_topics"],
        },
        {
            "id": "gpt-5.5",
            "name": "GPT-5.5",
            "input_price_per_1m": 2.00,
            "output_price_per_1m": 8.00,
            "context_window": "500k tokens",
            "tier": "flagship",
            "description": "Powerful general-purpose intelligence.",
            "recommended_for": ["deep_analysis", "plan_synthesis"],
        },
        {
            "id": "gpt-5.4",
            "name": "GPT-5.4",
            "input_price_per_1m": 1.25,
            "output_price_per_1m": 5.00,
            "context_window": "256k tokens",
            "tier": "balanced",
            "description": "Reliable and high-performing previous-generation model.",
            "recommended_for": ["deep_analysis", "plan_synthesis"],
        },
        {
            "id": "gpt-5.4-nano",
            "name": "GPT-5.4 Nano",
            "input_price_per_1m": 0.05,
            "output_price_per_1m": 0.20,
            "context_window": "128k tokens",
            "tier": "fast",
            "description": "Lowest cost per token; high-speed binary classification and sectioning.",
            "recommended_for": ["sections", "relevance", "plan_worthy"],
        },
        {
            "id": "gpt-5-mini",
            "name": "GPT-5 Mini",
            "input_price_per_1m": 0.15,
            "output_price_per_1m": 0.60,
            "context_window": "128k tokens",
            "tier": "fast",
            "description": "Lightweight efficient model for high-volume tasks.",
            "recommended_for": ["strategic_fit", "plan_brief"],
        },
        {
            "id": "gpt-4o",
            "name": "GPT-4o",
            "input_price_per_1m": 2.50,
            "output_price_per_1m": 10.00,
            "context_window": "128k tokens",
            "tier": "balanced",
            "description": "Standard multimodal model with strong structured output support.",
            "recommended_for": ["deep_analysis"],
        },
        {
            "id": "gpt-4o-mini",
            "name": "GPT-4o Mini",
            "input_price_per_1m": 0.15,
            "output_price_per_1m": 0.60,
            "context_window": "128k tokens",
            "tier": "fast",
            "description": "Budget-friendly utility model.",
            "recommended_for": ["sections", "relevance"],
        },
        {
            "id": "o3",
            "name": "OpenAI o3",
            "input_price_per_1m": 5.00,
            "output_price_per_1m": 20.00,
            "context_window": "200k tokens",
            "tier": "reasoning",
            "description": "Deep chain-of-thought model for difficult scientific analysis.",
            "recommended_for": ["deep_analysis", "plan_synthesis"],
        },
        {
            "id": "o3-mini",
            "name": "OpenAI o3 Mini",
            "input_price_per_1m": 1.10,
            "output_price_per_1m": 4.40,
            "context_window": "200k tokens",
            "tier": "reasoning",
            "description": "Fast reasoning model for structured problem-solving.",
            "recommended_for": ["plan_brief", "strategic_fit"],
        },
        {
            "id": "o1",
            "name": "OpenAI o1",
            "input_price_per_1m": 15.00,
            "output_price_per_1m": 60.00,
            "context_window": "200k tokens",
            "tier": "reasoning",
            "description": "Flagship deep reasoning model.",
            "recommended_for": ["deep_analysis"],
        },
    ],
    "anthropic": [
        {
            "id": "claude-opus-4-6",
            "name": "Claude Opus 4.6",
            "input_price_per_1m": 15.00,
            "output_price_per_1m": 75.00,
            "context_window": "500k tokens",
            "tier": "flagship",
            "description": "Most intelligent model for nuanced scientific comprehension and plan generation.",
            "recommended_for": ["deep_analysis", "plan_synthesis"],
        },
        {
            "id": "claude-sonnet-4-6",
            "name": "Claude Sonnet 4.6",
            "input_price_per_1m": 3.00,
            "output_price_per_1m": 15.00,
            "context_window": "500k tokens",
            "tier": "balanced",
            "description": "Excellent speed/intelligence tradeoff; strong structured reasoning.",
            "recommended_for": ["deep_analysis", "plan_synthesis", "strategic_fit"],
        },
        {
            "id": "claude-haiku-4-5",
            "name": "Claude Haiku 4.5",
            "input_price_per_1m": 0.80,
            "output_price_per_1m": 4.00,
            "context_window": "200k tokens",
            "tier": "fast",
            "description": "Fast, responsive model for high-throughput filtering.",
            "recommended_for": ["sections", "relevance", "plan_brief"],
        },
        {
            "id": "claude-3-7-sonnet",
            "name": "Claude 3.7 Sonnet",
            "input_price_per_1m": 3.00,
            "output_price_per_1m": 15.00,
            "context_window": "200k tokens",
            "tier": "balanced",
            "description": "Hybrid reasoning and coding model.",
            "recommended_for": ["plan_synthesis", "strategic_fit"],
        },
        {
            "id": "claude-3-5-sonnet-latest",
            "name": "Claude 3.5 Sonnet",
            "input_price_per_1m": 3.00,
            "output_price_per_1m": 15.00,
            "context_window": "200k tokens",
            "tier": "balanced",
            "description": "Proven coding and analysis baseline.",
            "recommended_for": ["deep_analysis", "plan_synthesis"],
        },
        {
            "id": "claude-3-5-haiku-latest",
            "name": "Claude 3.5 Haiku",
            "input_price_per_1m": 0.80,
            "output_price_per_1m": 4.00,
            "context_window": "200k tokens",
            "tier": "fast",
            "description": "Quick and lightweight.",
            "recommended_for": ["sections", "relevance"],
        },
    ],
    "gemini": [
        {
            "id": "gemini-3.7-flash",
            "name": "Gemini 3.7 Flash",
            "input_price_per_1m": 0.075,
            "output_price_per_1m": 0.30,
            "context_window": "1M tokens",
            "tier": "fast",
            "description": "Extremely fast, low-cost frontier intelligence with large context.",
            "recommended_for": ["sections", "relevance", "plan_brief", "app_improve_topics"],
        },
        {
            "id": "gemini-3.7-flash-high",
            "name": "Gemini 3.7 Flash High",
            "input_price_per_1m": 0.15,
            "output_price_per_1m": 0.60,
            "context_window": "1M tokens",
            "tier": "balanced",
            "description": "High-reasoning budget mode with fast latency.",
            "recommended_for": ["strategic_fit", "plan_brief"],
        },
        {
            "id": "gemini-2.5-pro",
            "name": "Gemini 2.5 Pro",
            "input_price_per_1m": 1.25,
            "output_price_per_1m": 5.00,
            "context_window": "2M tokens",
            "tier": "flagship",
            "description": "Massive 2M context window for long-paper synthesis and deep cross-analysis.",
            "recommended_for": ["deep_analysis", "plan_synthesis"],
        },
        {
            "id": "gemini-2.5-flash",
            "name": "Gemini 2.5 Flash",
            "input_price_per_1m": 0.075,
            "output_price_per_1m": 0.30,
            "context_window": "1M tokens",
            "tier": "fast",
            "description": "High-throughput multimodal parsing and quick classification.",
            "recommended_for": ["sections", "relevance", "plan_worthy"],
        },
        {
            "id": "gemini-2.0-flash",
            "name": "Gemini 2.0 Flash",
            "input_price_per_1m": 0.10,
            "output_price_per_1m": 0.40,
            "context_window": "1M tokens",
            "tier": "fast",
            "description": "Fast general-purpose model.",
            "recommended_for": ["sections", "relevance"],
        },
        {
            "id": "gemini-1.5-pro",
            "name": "Gemini 1.5 Pro",
            "input_price_per_1m": 1.25,
            "output_price_per_1m": 5.00,
            "context_window": "2M tokens",
            "tier": "flagship",
            "description": "Long-context deep analysis.",
            "recommended_for": ["deep_analysis"],
        },
        {
            "id": "gemini-1.5-flash",
            "name": "Gemini 1.5 Flash",
            "input_price_per_1m": 0.075,
            "output_price_per_1m": 0.30,
            "context_window": "1M tokens",
            "tier": "fast",
            "description": "Low-latency processing.",
            "recommended_for": ["sections"],
        },
    ],
    "local_vllm": [
        {
            "id": "Qwen/Qwen3.6-35B-A3B-FP8",
            "name": "Qwen 3.6 35B MoE FP8",
            "input_price_per_1m": 0.0,
            "output_price_per_1m": 0.0,
            "context_window": "32k tokens",
            "tier": "local",
            "description": "High-efficiency local MoE model with native structured output; zero API cost.",
            "recommended_for": ["deep_analysis", "plan_synthesis", "sections", "relevance"],
        },
        {
            "id": "local-qwen3.6",
            "name": "Local Qwen 3.6",
            "input_price_per_1m": 0.0,
            "output_price_per_1m": 0.0,
            "context_window": "32k tokens",
            "tier": "local",
            "description": "Convenient local alias for the served vLLM container.",
            "recommended_for": ["deep_analysis", "plan_synthesis", "sections", "relevance"],
        },
        {
            "id": "meta-llama/Llama-3.3-70B-Instruct",
            "name": "Llama 3.3 70B Instruct",
            "input_price_per_1m": 0.0,
            "output_price_per_1m": 0.0,
            "context_window": "128k tokens",
            "tier": "local",
            "description": "Flagship open-weights instruct model.",
            "recommended_for": ["deep_analysis", "plan_synthesis"],
        },
        {
            "id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
            "name": "DeepSeek R1 Distill Qwen 32B",
            "input_price_per_1m": 0.0,
            "output_price_per_1m": 0.0,
            "context_window": "64k tokens",
            "tier": "local",
            "description": "High reasoning capacity distilled model.",
            "recommended_for": ["deep_analysis", "strategic_fit"],
        },
    ],
}

PROVIDERS: Dict[str, Dict[str, Any]] = {
    "openai": {
        "label": "OpenAI",
        "env_keys": ["OPENAI_API_KEY"],
        "suggested_models": [m["id"] for m in CURATED_MODELS["openai"]],
    },
    "anthropic": {
        "label": "Anthropic Claude",
        "env_keys": ["ANTHROPIC_API_KEY"],
        "suggested_models": [m["id"] for m in CURATED_MODELS["anthropic"]],
    },
    "gemini": {
        "label": "Google Gemini",
        "env_keys": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "suggested_models": [m["id"] for m in CURATED_MODELS["gemini"]],
    },
    "local_vllm": {
        "label": "Local vLLM",
        "env_keys": ["LOCAL_VLLM_BASE_URL"],
        "suggested_models": [m["id"] for m in CURATED_MODELS["local_vllm"]],
    },
}


# ─── Defaults ─────────────────────────────────────────────────────────────

DEFAULTS: Dict[str, Dict[str, str]] = {
    "deep_analysis":      {"provider": "openai", "model": "gpt-5.6"},
    "sections":           {"provider": "openai", "model": "gpt-5.6-mini"},
    "relevance":          {"provider": "openai", "model": "gpt-5.6-mini"},
    "plan_brief":         {"provider": "openai", "model": "gpt-5.6-mini"},
    "plan_synthesis":     {"provider": "openai", "model": "gpt-5.6"},
    "plan_worthy":        {"provider": "openai", "model": "gpt-5.6-mini"},
    "strategic_fit":      {"provider": "openai", "model": "gpt-5.6-mini"},
    "app_improve_topics": {"provider": "openai", "model": "gpt-5.6-mini"},
}


# ─── In-memory cache ──────────────────────────────────────────────────────

_config_cache: Optional[Dict[str, Dict[str, str]]] = None


def _ensure_dir() -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_from_disk() -> Dict[str, Dict[str, str]]:
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # pragma: no cover
        print(f"⚠️ llm_config: failed to read {CONFIG_FILE}: {e}")
        return {}


def _save_to_disk(cfg: Dict[str, Dict[str, str]]) -> None:
    _ensure_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def _merge_defaults(persisted: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    merged = deepcopy(DEFAULTS)
    for role, override in persisted.items():
        if role not in merged:
            continue  # drop unknown roles silently
        provider = override.get("provider") or merged[role]["provider"]
        model = override.get("model") or merged[role]["model"]
        if provider not in PROVIDERS:
            provider = merged[role]["provider"]
        merged[role] = {"provider": provider, "model": model}
    return merged


def get_full_config() -> Dict[str, Dict[str, str]]:
    """Return the effective config (defaults + persisted overrides)."""
    global _config_cache
    if _config_cache is None:
        _config_cache = _merge_defaults(_load_from_disk())
    return deepcopy(_config_cache)


def get_role(role: str) -> Dict[str, str]:
    """Return the effective ``{provider, model}`` for a role."""
    cfg = get_full_config()
    if role not in cfg:
        raise KeyError(f"unknown llm role: {role!r}")
    return cfg[role]


def update_config(updates: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """
    Merge ``updates`` into the persisted config and return the new effective
    config. Unknown roles are ignored. Unknown providers are rejected with a
    ``ValueError``.
    """
    global _config_cache
    current_persisted = _load_from_disk()
    for role, override in updates.items():
        if role not in DEFAULTS:
            continue
        provider = (override or {}).get("provider")
        model = (override or {}).get("model")
        if provider is not None and provider not in PROVIDERS:
            raise ValueError(f"unknown provider: {provider!r}")
        current_persisted.setdefault(role, {})
        if provider:
            current_persisted[role]["provider"] = provider
        if model:
            current_persisted[role]["model"] = model
    _save_to_disk(current_persisted)
    _config_cache = _merge_defaults(current_persisted)
    return deepcopy(_config_cache)


def reset_config() -> Dict[str, Dict[str, str]]:
    """Wipe persisted overrides, revert to defaults."""
    global _config_cache
    if CONFIG_FILE.exists():
        try:
            CONFIG_FILE.unlink()
        except Exception:  # pragma: no cover
            pass
    _config_cache = deepcopy(DEFAULTS)
    return deepcopy(_config_cache)


def _merge_provider_models(
    pid: str, live_meta: Optional[Dict[str, Any]]
) -> tuple[List[Dict[str, Any]], List[str], str, Optional[str]]:
    curated = deepcopy(CURATED_MODELS.get(pid, []))
    curated_map = {m["id"]: m for m in curated}

    live_meta = live_meta or {}
    live_ids = live_meta.get("models") or []
    live_error = live_meta.get("error")

    if not live_ids:
        source = "fallback" if live_error else "curated"
        for m in curated:
            m["source"] = "curated"
        return curated, [m["id"] for m in curated], source, live_error

    merged: List[Dict[str, Any]] = []
    seen = set()

    # 1. Add all live models (enrich with curated metadata if available)
    for mid in live_ids:
        if mid in seen:
            continue
        seen.add(mid)
        if mid in curated_map:
            item = deepcopy(curated_map[mid])
            item["source"] = "live"
            merged.append(item)
        else:
            merged.append({
                "id": mid,
                "name": mid,
                "input_price_per_1m": None,
                "output_price_per_1m": None,
                "context_window": "Discovered",
                "tier": "custom",
                "description": "Live model discovered from provider API",
                "recommended_for": [],
                "source": "live",
            })

    # 2. Append curated models that were not in live list (so user still has rich list)
    for m in curated:
        if m["id"] not in seen:
            seen.add(m["id"])
            item = deepcopy(m)
            item["source"] = "curated"
            merged.append(item)

    suggested = [m["id"] for m in merged]
    return merged, suggested, "live", live_error


def provider_health(live_catalog: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
    """Return per-provider availability info for the UI (API key present?, rich model catalog, pricing).

    ``live_catalog`` is ``{provider: {models, source, error}}`` from
    :func:`services.llm_clients.list_all_provider_models`. Discovered live ids
    are enriched with pricing and metadata from the curated catalog.
    """
    catalog = live_catalog or {}
    out: Dict[str, Dict[str, Any]] = {}
    for pid, meta in PROVIDERS.items():
        key_env: Optional[str] = None
        for env_key in meta["env_keys"]:
            if os.getenv(env_key):
                key_env = env_key
                break

        live_meta = catalog.get(pid)
        models_list, suggested_models, source, error = _merge_provider_models(pid, live_meta)

        out[pid] = {
            "label": meta["label"],
            "models": models_list,
            "suggested_models": suggested_models,
            "env_keys": meta["env_keys"],
            "key_present": key_env is not None,
            "active_env": key_env,
            "models_source": source,
            "models_error": error,
        }
    return out


def describe_roles() -> List[Dict[str, str]]:
    return [{"id": rid, "description": desc} for rid, desc in ROLES.items()]
