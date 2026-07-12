"""Tests for OpenAlex discovery provider (P1-003)."""

import asyncio
from unittest.mock import AsyncMock, patch

from services.sources.openalex import (
    extract_openalex_id,
    normalize_openalex_work,
    reconstruct_abstract,
    search_openalex_works,
)

SAMPLE_WORK = {
    "id": "https://openalex.org/W1234567890",
    "doi": "https://doi.org/10.1234/example",
    "display_name": "Robotics Survey",
    "publication_date": "2026-03-15",
    "publication_year": 2026,
    "type": "article",
    "cited_by_count": 12,
    "abstract_inverted_index": {
        "Robotics": [0],
        "advances": [1],
        "quickly": [2],
    },
    "authorships": [
        {"author": {"display_name": "Ada Lovelace"}},
        {"author": {"display_name": "Alan Turing"}},
    ],
    "open_access": {"is_oa": True, "oa_status": "gold"},
    "primary_location": {
        "landing_page_url": "https://example.org/article",
        "pdf_url": None,
    },
    "best_oa_location": {
        "pdf_url": "https://example.org/paper.pdf",
        "license": "cc-by",
    },
    "ids": {"openalex": "https://openalex.org/W1234567890"},
    "topics": [{"display_name": "Robotics"}],
}


def test_extract_openalex_id():
    assert extract_openalex_id("https://openalex.org/W1234567890") == "W1234567890"


def test_reconstruct_abstract():
    text = reconstruct_abstract(SAMPLE_WORK["abstract_inverted_index"])
    assert text == "Robotics advances quickly"


def test_normalize_openalex_work():
    paper = normalize_openalex_work(SAMPLE_WORK)
    assert paper.id == "openalex:W1234567890"
    assert paper.source == "openalex"
    assert paper.doi == "10.1234/example"
    assert paper.pdf_url == "https://example.org/paper.pdf"
    assert paper.is_open_access is True
    assert paper.authors == ["Ada Lovelace", "Alan Turing"]
    assert paper.abstract == "Robotics advances quickly"

    stored = paper.to_storage_dict()
    assert stored["external_ids"]["openalex"] == "W1234567890"
    assert stored["source_metadata"]["cited_by_count"] == 12


def test_search_openalex_works():
    async def run():
        mock_response = AsyncMock()
        mock_response.raise_for_status = lambda: None
        mock_response.json = lambda: {"results": [SAMPLE_WORK]}

        with patch("services.sources.openalex.httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.get = AsyncMock(return_value=mock_response)
            client_cls.return_value = client

            papers = await search_openalex_works(
                query="robotics", limit=5, since="2026-01-01"
            )

        assert len(papers) == 1
        assert papers[0].id == "openalex:W1234567890"

        call_kwargs = client.get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["search"] == "robotics"
        assert "is_oa:true" in params["filter"]
        assert "from_publication_date:2026-01-01" in params["filter"]

    asyncio.run(run())


if __name__ == "__main__":
    test_extract_openalex_id()
    test_reconstruct_abstract()
    test_normalize_openalex_work()
    test_search_openalex_works()
    print("OK: all OpenAlex provider tests passed")
