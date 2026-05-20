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
}


# ─── Known providers ──────────────────────────────────────────────────────

PROVIDERS: Dict[str, Dict[str, Any]] = {
    "openai": {
        "label": "OpenAI",
        "env_keys": ["OPENAI_API_KEY"],
        "suggested_models": [
            "gpt-5.4",
            "gpt-5.4-nano",
            "gpt-5-mini",
            "gpt-5-nano",
            "gpt-4o-mini",
        ],
    },
    "anthropic": {
        "label": "Anthropic Claude",
        "env_keys": ["ANTHROPIC_API_KEY"],
        "suggested_models": [
            "claude-sonnet-4-5",
            "claude-opus-4-5",
            "claude-haiku-4-5",
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-latest",
        ],
    },
    "gemini": {
        "label": "Google Gemini",
        "env_keys": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "suggested_models": [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ],
    },
    "local_vllm": {
        "label": "Local vLLM",
        "env_keys": ["LOCAL_VLLM_BASE_URL"],
        "suggested_models": [
            "Qwen/Qwen3.6-35B-A3B-FP8",
            "local-qwen3.6",
        ],
    },
}


# ─── Defaults ─────────────────────────────────────────────────────────────
# These mirror the current hard-coded defaults so nothing changes unless the
# user picks a different provider in the UI.

DEFAULTS: Dict[str, Dict[str, str]] = {
    "deep_analysis":  {"provider": "openai", "model": "gpt-5.4"},
    "sections":       {"provider": "openai", "model": "gpt-5.4-nano"},
    "relevance":      {"provider": "openai", "model": "gpt-5.4-nano"},
    "plan_brief":     {"provider": "openai", "model": "gpt-5-mini"},
    "plan_synthesis": {"provider": "openai", "model": "gpt-5.4"},
    "plan_worthy":    {"provider": "openai", "model": "gpt-5.4-nano"},
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


def provider_health() -> Dict[str, Dict[str, Any]]:
    """Return per-provider availability info for the UI (API key present?)."""
    out: Dict[str, Dict[str, Any]] = {}
    for pid, meta in PROVIDERS.items():
        key_env: Optional[str] = None
        for env_key in meta["env_keys"]:
            if os.getenv(env_key):
                key_env = env_key
                break
        out[pid] = {
            "label": meta["label"],
            "suggested_models": meta["suggested_models"],
            "env_keys": meta["env_keys"],
            "key_present": key_env is not None,
            "active_env": key_env,
        }
    return out


def describe_roles() -> List[Dict[str, str]]:
    return [{"id": rid, "description": desc} for rid, desc in ROLES.items()]
