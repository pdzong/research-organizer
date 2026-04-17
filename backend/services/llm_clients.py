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

Dependencies
------------
All three SDKs are *soft* deps: the adapter only imports a provider's SDK
when it's actually needed for a call. If a provider's SDK or API key is
missing and the caller selects that provider, a ``RuntimeError`` with a
clear message is raised.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional, Type, TypeVar

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
        raise RuntimeError(f"unsupported provider: {prov!r}")

    return await asyncio.to_thread(_call)
