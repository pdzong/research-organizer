"""
Thin multi-provider LLM adapter.

Exposes two async helpers that every other backend service calls through:

* ``parse_structured(role, schema, system, user, ...)`` — returns a validated
  Pydantic instance + usage dict. Dispatches to the provider configured for
  the role via :mod:`services.llm_config`.
* ``generate_text(role, system, user, ...)`` — returns a plain ``str``.

Supported providers
-------------------
* ``openai``    — uses ``client.responses.parse`` (native Structured Outputs).
* ``anthropic`` — uses forced tool-use to coerce JSON matching a Pydantic
  schema.
* ``gemini``    — uses ``response_mime_type="application/json"`` with
  ``response_schema`` (new ``google-genai`` SDK).
* ``local_vllm`` — uses the OpenAI-compatible Chat Completions API exposed by
  a local vLLM server.

Dependencies
------------
All SDKs are *soft* deps: the adapter only imports a provider's SDK when it's
actually needed for a call. If a provider's SDK, API key, or endpoint is
missing and the caller selects that provider, a ``RuntimeError`` with a clear
message is raised.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from . import llm_config


T = TypeVar("T", bound=BaseModel)


class StructuredResult(Dict[str, Any]):
    """Marker type only; we just return a dict for ergonomic JSON serialisation."""


# ─── Provider dispatch ────────────────────────────────────────────────────


def _resolve(role: str, provider: Optional[str], model: Optional[str]) -> tuple[str, str]:
    """Resolve final provider + model given optional overrides."""
    defaults = llm_config.get_role(role)
    return (provider or defaults["provider"], model or defaults["model"])


def _usage_attr(usage: Any, *names: str) -> Optional[int]:
    if usage is None:
        return None
    for name in names:
        value = getattr(usage, name, None)
        if value is None and isinstance(usage, dict):
            value = usage.get(name)
        if value is not None:
            return value
    return None


# ─── OpenAI ───────────────────────────────────────────────────────────────


def _openai_client():
    from openai import OpenAI

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=key)


def _openai_parse(model: str, system: str, user: str, schema: Type[T]) -> tuple[T, Dict[str, Any]]:
    client = _openai_client()
    response = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        text_format=schema,
    )
    parsed: T = response.output_parsed
    usage = {
        "model": getattr(response, "model", model),
        "provider": "openai",
        "input_tokens": getattr(response.usage, "input_tokens", None) if response.usage else None,
        "output_tokens": getattr(response.usage, "output_tokens", None) if response.usage else None,
    }
    return parsed, usage


def _openai_text(model: str, system: str, user: str) -> tuple[str, Dict[str, Any]]:
    client = _openai_client()
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    text = getattr(response, "output_text", "") or ""
    usage = {
        "model": getattr(response, "model", model),
        "provider": "openai",
        "input_tokens": getattr(response.usage, "input_tokens", None) if response.usage else None,
        "output_tokens": getattr(response.usage, "output_tokens", None) if response.usage else None,
    }
    return text, usage


# ─── Anthropic ────────────────────────────────────────────────────────────


def _anthropic_client():
    try:
        from anthropic import Anthropic  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "anthropic SDK not installed. Run `pip install anthropic` or remove "
            "Anthropic from llm_config."
        ) from e
    from anthropic import Anthropic

    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")
    return Anthropic(api_key=key)


def _anthropic_parse(model: str, system: str, user: str, schema: Type[T]) -> tuple[T, Dict[str, Any]]:
    client = _anthropic_client()
    tool_schema = schema.model_json_schema()
    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=system,
        messages=[{"role": "user", "content": user}],
        tools=[
            {
                "name": "return_structured",
                "description": "Return the answer as a JSON object matching the provided schema.",
                "input_schema": tool_schema,
            }
        ],
        tool_choice={"type": "tool", "name": "return_structured"},
    )
    tool_use = None
    for block in response.content:
        if getattr(block, "type", None) == "tool_use":
            tool_use = block
            break
    if tool_use is None:
        raise RuntimeError("Anthropic did not return a structured tool_use block.")
    parsed = schema.model_validate(tool_use.input)
    usage = {
        "model": getattr(response, "model", model),
        "provider": "anthropic",
        "input_tokens": getattr(response.usage, "input_tokens", None) if response.usage else None,
        "output_tokens": getattr(response.usage, "output_tokens", None) if response.usage else None,
    }
    return parsed, usage


def _anthropic_text(model: str, system: str, user: str) -> tuple[str, Dict[str, Any]]:
    client = _anthropic_client()
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(
        getattr(block, "text", "") for block in response.content if getattr(block, "type", None) == "text"
    )
    usage = {
        "model": getattr(response, "model", model),
        "provider": "anthropic",
        "input_tokens": getattr(response.usage, "input_tokens", None) if response.usage else None,
        "output_tokens": getattr(response.usage, "output_tokens", None) if response.usage else None,
    }
    return text, usage


# ─── Gemini ───────────────────────────────────────────────────────────────


def _gemini_client():
    try:
        from google import genai  # type: ignore[attr-defined]  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "google-genai SDK not installed. Run `pip install google-genai` or "
            "remove Gemini from llm_config."
        ) from e
    from google import genai  # type: ignore[attr-defined]

    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY / GEMINI_API_KEY is not set.")
    return genai.Client(api_key=key)


def _gemini_parse(model: str, system: str, user: str, schema: Type[T]) -> tuple[T, Dict[str, Any]]:
    client = _gemini_client()
    response = client.models.generate_content(
        model=model,
        contents=user,
        config={
            "system_instruction": system,
            "response_mime_type": "application/json",
            "response_schema": schema,
        },
    )
    text = getattr(response, "text", None) or ""
    try:
        parsed = schema.model_validate_json(text)
    except Exception:
        # Some SDK versions expose a .parsed attr that's already a pydantic instance.
        candidate = getattr(response, "parsed", None)
        if candidate is not None and isinstance(candidate, schema):
            parsed = candidate  # type: ignore[assignment]
        else:
            # Last-ditch: assume dict-ish
            parsed = schema.model_validate(json.loads(text))

    usage_meta = getattr(response, "usage_metadata", None)
    usage = {
        "model": model,
        "provider": "gemini",
        "input_tokens": getattr(usage_meta, "prompt_token_count", None) if usage_meta else None,
        "output_tokens": getattr(usage_meta, "candidates_token_count", None) if usage_meta else None,
    }
    return parsed, usage


def _gemini_text(model: str, system: str, user: str) -> tuple[str, Dict[str, Any]]:
    client = _gemini_client()
    response = client.models.generate_content(
        model=model,
        contents=user,
        config={"system_instruction": system},
    )
    text = getattr(response, "text", "") or ""
    usage_meta = getattr(response, "usage_metadata", None)
    usage = {
        "model": model,
        "provider": "gemini",
        "input_tokens": getattr(usage_meta, "prompt_token_count", None) if usage_meta else None,
        "output_tokens": getattr(usage_meta, "candidates_token_count", None) if usage_meta else None,
    }
    return text, usage


# ─── Local vLLM ───────────────────────────────────────────────────────────


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _vllm_client():
    try:
        from openai import OpenAI  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "openai SDK not installed. Run `pip install openai` or install "
            "backend requirements before using local_vllm."
        ) from e
    from openai import OpenAI

    base_url = os.getenv("LOCAL_VLLM_BASE_URL", "http://localhost:9001/v1")
    api_key = os.getenv("LOCAL_VLLM_API_KEY", "EMPTY")
    return OpenAI(base_url=base_url, api_key=api_key)


def _vllm_extra_body() -> Dict[str, Any]:
    """
    Qwen reasoning models can otherwise emit thinking text before the answer,
    which breaks structured parsing. Allow opt-out for other local models.
    """
    if not _env_bool("LOCAL_VLLM_DISABLE_THINKING", True):
        return {}
    return {"chat_template_kwargs": {"enable_thinking": False}}


def _vllm_usage(response: Any, model: str) -> Dict[str, Any]:
    usage = getattr(response, "usage", None)
    return {
        "model": getattr(response, "model", model),
        "provider": "local_vllm",
        "input_tokens": _usage_attr(usage, "input_tokens", "prompt_tokens"),
        "output_tokens": _usage_attr(usage, "output_tokens", "completion_tokens"),
    }


def _vllm_model_not_found(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code == 404:
        return True
    message = str(exc).lower()
    return "model" in message and ("does not exist" in message or "not found" in message)


def _vllm_first_served_model(client: Any) -> Optional[str]:
    try:
        models = client.models.list()
        data = getattr(models, "data", None) or []
        if not data:
            return None
        return getattr(data[0], "id", None)
    except Exception:
        return None


def _vllm_chat_completion(client: Any, model: str, **kwargs: Any) -> Any:
    try:
        return client.chat.completions.create(model=model, **kwargs)
    except Exception as e:
        fallback_model = os.getenv("LOCAL_VLLM_FALLBACK_MODEL")
        if _vllm_model_not_found(e):
            fallback_model = fallback_model or _vllm_first_served_model(client)
            if fallback_model and fallback_model != model:
                return client.chat.completions.create(model=fallback_model, **kwargs)
        raise


def _vllm_text(model: str, system: str, user: str) -> tuple[str, Dict[str, Any]]:
    client = _vllm_client()
    response = _vllm_chat_completion(
        client,
        model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
        max_tokens=_env_int("LOCAL_VLLM_TEXT_MAX_TOKENS", 4096),
        extra_body=_vllm_extra_body(),
    )
    text = getattr(response.choices[0].message, "content", "") or ""
    return text, _vllm_usage(response, model)


def _vllm_validate_json(content: str, schema: Type[T]) -> T:
    stripped = (content or "").strip()
    candidates = [stripped]

    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        candidates.append("\n".join(lines).strip())

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        candidates.append(stripped[start:end + 1])

    last_error: Optional[Exception] = None
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return schema.model_validate_json(candidate)
        except Exception as e:
            last_error = e

    preview = stripped[:500].replace("\n", "\\n")
    raise RuntimeError(
        f"local_vllm did not return valid {schema.__name__} JSON: "
        f"{last_error}. Output preview: {preview}"
    )


def _vllm_parse(model: str, system: str, user: str, schema: Type[T]) -> tuple[T, Dict[str, Any]]:
    client = _vllm_client()
    schema_json = schema.model_json_schema()
    response = _vllm_chat_completion(
        client,
        model,
        messages=[
            {
                "role": "system",
                "content": (
                    system
                    + "\nReturn only valid JSON matching the supplied schema. "
                    + "Do not include reasoning, markdown fences, or any text outside JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    "JSON schema:\n"
                    + json.dumps(schema_json, indent=2)
                    + "\n\nTask:\n"
                    + user
                ),
            },
        ],
        temperature=0,
        max_tokens=_env_int("LOCAL_VLLM_STRUCTURED_MAX_TOKENS", 8192),
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__,
                "schema": schema_json,
                "strict": True,
            },
        },
        extra_body=_vllm_extra_body(),
    )
    content = getattr(response.choices[0].message, "content", "") or ""
    return _vllm_validate_json(content, schema), _vllm_usage(response, model)


# ─── Public API ───────────────────────────────────────────────────────────


async def parse_structured(
    role: str,
    schema: Type[T],
    system: str,
    user: str,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> tuple[T, Dict[str, Any]]:
    """
    Call the model configured for ``role`` and validate its output against ``schema``.
    Runs the blocking SDK call in a worker thread so the event loop is free.
    """
    prov, mod = _resolve(role, provider, model)

    def _call() -> tuple[T, Dict[str, Any]]:
        if prov == "openai":
            return _openai_parse(mod, system, user, schema)
        if prov == "anthropic":
            return _anthropic_parse(mod, system, user, schema)
        if prov == "gemini":
            return _gemini_parse(mod, system, user, schema)
        if prov == "local_vllm":
            return _vllm_parse(mod, system, user, schema)
        raise RuntimeError(f"unsupported provider: {prov!r}")

    return await asyncio.to_thread(_call)


async def generate_text(
    role: str,
    system: str,
    user: str,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> tuple[str, Dict[str, Any]]:
    prov, mod = _resolve(role, provider, model)

    def _call() -> tuple[str, Dict[str, Any]]:
        if prov == "openai":
            return _openai_text(mod, system, user)
        if prov == "anthropic":
            return _anthropic_text(mod, system, user)
        if prov == "gemini":
            return _gemini_text(mod, system, user)
        if prov == "local_vllm":
            return _vllm_text(mod, system, user)
        raise RuntimeError(f"unsupported provider: {prov!r}")

    return await asyncio.to_thread(_call)


# ─── Live model catalogs & Caching ────────────────────────────────────────

_OPENAI_SKIP_SUBSTR = (
    "whisper",
    "tts",
    "audio",
    "transcribe",
    "realtime",
    "image",
    "dall-e",
    "davinci",
    "babbage",
    "embedding",
    "moderation",
    "sora",
    "omni-moderation",
    "computer-use",
    "codex-mini",
)

_GEMINI_SKIP_SUBSTR = (
    "embed",
    "imagen",
    "veo",
    "tts",
    "image",
    "robotics",
    "aqa",
    "gecko",
)


def _model_sort_key(model_id: str) -> tuple[int, str]:
    low = model_id.lower()
    score = 0
    # Tier bonuses for modern 2026 / recent models
    if "5.6" in low or "4.6" in low or "3.7" in low:
        score += 1000
    elif "5.5" in low or "4.5" in low:
        score += 800
    elif "5.4" in low or "2.5" in low or "3.5" in low:
        score += 600
    elif "gpt-5" in low or "o3" in low or "2.0" in low:
        score += 400
    elif "o1" in low or "o4" in low:
        score += 300
    elif "gpt-4" in low or "1.5" in low:
        score += 200
    elif "qwen3.6" in low or "llama-3.3" in low or "deepseek-r1" in low:
        score += 500

    # Variant bonuses
    if "turbo" in low or "sonnet" in low or "pro" in low:
        score += 50
    elif "sol" in low or "opus" in low:
        score += 60
    elif "mini" in low or "nano" in low or "haiku" in low or "flash" in low:
        score += 20

    return (score, low)


def _unique_sorted(ids: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for mid in ids:
        if not mid or mid in seen:
            continue
        seen.add(mid)
        out.append(mid)
    out.sort(key=_model_sort_key, reverse=True)
    return out[:50]


def _keep_openai_chat_model(model_id: str) -> bool:
    low = model_id.lower()
    if any(part in low for part in _OPENAI_SKIP_SUBSTR):
        return False
    return (
        low.startswith("gpt-")
        or low.startswith("o1")
        or low.startswith("o3")
        or low.startswith("o4")
        or low.startswith("chatgpt-")
    )


def _keep_gemini_chat_model(model_id: str) -> bool:
    low = model_id.lower()
    if not low.startswith("gemini-"):
        return False
    return not any(part in low for part in _GEMINI_SKIP_SUBSTR)


def _iter_model_ids(listing: Any) -> List[str]:
    ids: List[str] = []
    data = getattr(listing, "data", None)
    iterable = data if data is not None else listing
    try:
        for item in iterable:
            mid = getattr(item, "id", None) or getattr(item, "name", None)
            if not mid and isinstance(item, dict):
                mid = item.get("id") or item.get("name")
            if mid:
                ids.append(str(mid))
    except TypeError:
        pass
    return ids


def _list_openai_models() -> List[str]:
    from openai import OpenAI

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    client = OpenAI(api_key=key, timeout=3.0)
    raw = _iter_model_ids(client.models.list())
    return _unique_sorted([m for m in raw if _keep_openai_chat_model(m)])


def _list_anthropic_models() -> List[str]:
    try:
        from anthropic import Anthropic  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "anthropic SDK not installed. Run `pip install anthropic` or remove "
            "Anthropic from llm_config."
        ) from e
    from anthropic import Anthropic

    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")
    client = Anthropic(api_key=key, timeout=3.0)
    listing = client.models.list()
    raw = _iter_model_ids(listing)
    return _unique_sorted([m for m in raw if m.lower().startswith("claude-")])


def _list_gemini_models() -> List[str]:
    client = _gemini_client()
    raw: List[str] = []
    for item in client.models.list():
        name = getattr(item, "name", None) or getattr(item, "id", None) or ""
        name = str(name)
        if name.startswith("models/"):
            name = name[len("models/") :]
        raw.append(name)
    return _unique_sorted([m for m in raw if _keep_gemini_chat_model(m)])


def _list_vllm_models() -> List[str]:
    try:
        from openai import OpenAI  # noqa: F401
    except ImportError as e:
        raise RuntimeError("openai SDK not installed.") from e
    from openai import OpenAI

    base_url = os.getenv("LOCAL_VLLM_BASE_URL", "http://localhost:9001/v1")
    api_key = os.getenv("LOCAL_VLLM_API_KEY", "EMPTY")
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=2.0)
    raw = _iter_model_ids(client.models.list())
    return _unique_sorted(raw)


def list_provider_models(provider: str) -> List[str]:
    """Fetch chat-capable model ids from a provider. Raises on missing key/SDK."""
    if provider == "openai":
        return _list_openai_models()
    if provider == "anthropic":
        return _list_anthropic_models()
    if provider == "gemini":
        return _list_gemini_models()
    if provider == "local_vllm":
        return _list_vllm_models()
    raise RuntimeError(f"unsupported provider: {provider!r}")


# ─── In-memory cache for live catalogs ─────────────────────────────────────

_LIVE_CATALOG_CACHE: Dict[str, Any] = {
    "catalog": {},
    "timestamp": 0.0,
}
CACHE_TTL_SECONDS: float = 600.0  # 10 minutes


def get_cached_live_catalog() -> Optional[Dict[str, Dict[str, Any]]]:
    """Return in-memory live catalog if still within TTL."""
    now = time.time()
    if _LIVE_CATALOG_CACHE["catalog"] and (now - _LIVE_CATALOG_CACHE["timestamp"] < CACHE_TTL_SECONDS):
        return _LIVE_CATALOG_CACHE["catalog"]
    return None


def set_cached_live_catalog(catalog: Dict[str, Dict[str, Any]]) -> None:
    _LIVE_CATALOG_CACHE["catalog"] = catalog
    _LIVE_CATALOG_CACHE["timestamp"] = time.time()


def clear_live_catalog_cache() -> None:
    _LIVE_CATALOG_CACHE["catalog"] = {}
    _LIVE_CATALOG_CACHE["timestamp"] = 0.0


async def list_all_provider_models(
    providers: Optional[List[str]] = None,
    timeout_s: float = 3.0,
    force_refresh: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """
    List models for each provider in parallel with in-memory caching.

    If ``force_refresh=False`` and a recent cache exists, returns cached results
    immediately (<1ms). Otherwise polls active providers in parallel with a strict
    timeout.
    """
    if not force_refresh:
        cached = get_cached_live_catalog()
        if cached is not None:
            if providers:
                return {p: cached[p] for p in providers if p in cached}
            return cached

    targets = providers or ["openai", "anthropic", "gemini", "local_vllm"]

    async def _one(pid: str) -> tuple[str, Dict[str, Any]]:
        try:
            models = await asyncio.wait_for(
                asyncio.to_thread(list_provider_models, pid),
                timeout=timeout_s,
            )
            if not models:
                return pid, {
                    "models": [],
                    "source": "fallback",
                    "error": "Provider returned no chat models.",
                }
            return pid, {"models": models, "source": "live", "error": None}
        except Exception as exc:
            return pid, {"models": [], "source": "fallback", "error": str(exc)}

    pairs = await asyncio.gather(*(_one(pid) for pid in targets))
    result = dict(pairs)

    # Merge into cache
    current_cached = dict(_LIVE_CATALOG_CACHE.get("catalog") or {})
    current_cached.update(result)
    set_cached_live_catalog(current_cached)

    return result
