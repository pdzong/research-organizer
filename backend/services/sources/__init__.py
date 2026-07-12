"""Discovery source registry."""

from __future__ import annotations

from typing import Any, Dict, List

# Sources exposed via GET /api/sources. ``searchable`` sources support /api/sources/search.
SOURCE_CATALOG: List[Dict[str, Any]] = [
    {"id": "openalex", "label": "OpenAlex", "searchable": True},
    {"id": "huggingface", "label": "Hugging Face Daily Papers", "searchable": False},
    {"id": "arxiv", "label": "arXiv", "searchable": False},
]


def list_sources() -> List[Dict[str, Any]]:
    return list(SOURCE_CATALOG)


def get_source(source_id: str) -> Dict[str, Any] | None:
    for source in SOURCE_CATALOG:
        if source["id"] == source_id:
            return source
    return None
