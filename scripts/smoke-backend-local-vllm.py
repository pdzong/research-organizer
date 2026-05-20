#!/usr/bin/env python3
"""
Smoke-test the backend LLM adapter against a local vLLM endpoint.

This exercises the same services.llm_clients paths used by the application,
not just the raw /v1/chat/completions endpoint.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("LOCAL_VLLM_BASE_URL", "http://localhost:9001/v1")
os.environ.setdefault("LOCAL_VLLM_API_KEY", "EMPTY")
os.environ.setdefault("LOCAL_VLLM_DISABLE_THINKING", "true")

try:
    from services import llm_clients  # noqa: E402
    from services.models import RelevanceDecision  # noqa: E402
except ModuleNotFoundError as e:
    missing = e.name or "backend dependency"
    raise SystemExit(
        f"Missing Python dependency: {missing}\n"
        "Run this from an environment with backend requirements installed, e.g.:\n"
        "  cd backend && source venv/bin/activate && cd ..\n"
        "  python scripts/smoke-backend-local-vllm.py"
    ) from e


def discover_model() -> str:
    configured = os.getenv("LOCAL_VLLM_TEST_MODEL") or os.getenv("LOCAL_VLLM_SERVED_MODEL_NAME")
    if configured:
        return configured

    base_url = os.environ["LOCAL_VLLM_BASE_URL"].rstrip("/")
    with urllib.request.urlopen(f"{base_url}/models", timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    data = payload.get("data") or []
    if not data:
        raise RuntimeError(f"no models returned by {base_url}/models")
    return data[0]["id"]


async def main() -> None:
    model = discover_model()
    print(f"Testing backend local_vllm adapter with model: {model}")

    text, text_usage = await llm_clients.generate_text(
        role="plan_brief",
        provider="local_vllm",
        model=model,
        system="Return only the requested short answer.",
        user="Reply with exactly: local backend ok",
    )
    if not text.strip():
        raise RuntimeError("generate_text returned empty content")
    print(f"OK generate_text: {text.strip()[:200]}")
    print(f"usage: {text_usage}")

    parsed, parse_usage = await llm_clients.parse_structured(
        role="relevance",
        provider="local_vllm",
        model=model,
        schema=RelevanceDecision,
        system="Return a relevance decision.",
        user=(
            "Target application: local LLM integration testing.\n"
            "Candidate paper: A practical note on testing OpenAI-compatible APIs.\n"
            "Return is_relevant=true with a concise reason."
        ),
    )
    if not isinstance(parsed.is_relevant, bool) or not parsed.reasoning.strip():
        raise RuntimeError(f"parse_structured returned invalid data: {parsed!r}")
    print(f"OK parse_structured: {parsed.model_dump()}")
    print(f"usage: {parse_usage}")


if __name__ == "__main__":
    asyncio.run(main())
