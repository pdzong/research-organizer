"""
Smoke test for the discovery sources (live arXiv + OpenAlex APIs) and the
add-from-source store logic (run against a temp papers.json).
Run from backend/: python test_sources.py
"""
import asyncio
import sys
import tempfile
from pathlib import Path

from services import huggingface
from services.sources import get_provider, list_sources


def test_registry():
    sources = list_sources()
    ids = [s.id for s in sources]
    assert "arxiv" in ids and "openalex" in ids, ids
    for s in sources:
        assert len(s.fields) > 0, f"{s.id} should expose filterable fields"
    assert get_provider("nope") is None
    print(f"PASS registry ({ids})")


def test_arxiv_discover():
    provider = get_provider("arxiv")
    papers = asyncio.run(provider.discover(query="robot learning", field="cs.RO", days=30, limit=5))
    assert len(papers) > 0, "arxiv discover returned nothing"
    p = papers[0]
    assert p.source == "arxiv" and p.external_ids.get("arxiv") and p.pdf_url
    assert p.id.startswith("arxiv_")
    # recency sort without query
    recent = asyncio.run(provider.discover(field="cs.AI", days=7, limit=5, sort="recency"))
    assert len(recent) > 0 and recent[0].published_date
    print(f"PASS arxiv discover ({len(papers)} results, top: {p.title[:50]}...)")


def test_openalex_discover():
    provider = get_provider("openalex")
    papers = asyncio.run(provider.discover(query="machine learning", field="17", days=30, limit=5))
    assert len(papers) > 0, "openalex discover returned nothing"
    p = papers[0]
    assert p.source == "openalex" and p.pdf_url, p
    assert p.relevance_score is not None, "expected relevance_score with search"
    # recency browse without query
    recent = asyncio.run(provider.discover(field="27", days=7, limit=5, sort="recency"))
    assert len(recent) > 0 and recent[0].published_date
    print(f"PASS openalex discover ({len(papers)} results, top: {p.title[:50]}...)")


def test_add_from_source():
    # Redirect the papers store to a temp file so real data is untouched
    original = huggingface.PAPERS_FILE
    with tempfile.TemporaryDirectory() as tmp:
        huggingface.PAPERS_FILE = Path(tmp) / "papers.json"
        try:
            source_paper = {
                "id": "openalex_W123",
                "source": "openalex",
                "source_record_id": "W123",
                "title": "Test Paper",
                "authors": ["A. Author"],
                "pdf_url": "https://example.org/paper.pdf",
                "landing_url": "https://example.org/paper",
                "published_date": "2026-06-01",
                "external_ids": {"openalex": "W123", "doi": "10.1/test"},
            }
            result = asyncio.run(huggingface.add_paper_from_source(source_paper))
            assert result["success"], result
            assert result["paper"]["id"] == "openalex_W123"
            assert result["paper"]["arxiv_id"] is None
            assert result["paper"]["pdf_url"] == "https://example.org/paper.pdf"

            # duplicate by DOI
            dup = dict(source_paper, id="openalex_W456", source_record_id="W456")
            result = asyncio.run(huggingface.add_paper_from_source(dup))
            assert not result["success"] and "DOI" in result["error"], result

            # arxiv-backed source paper gets arxiv id as primary id
            arxiv_paper = {
                "id": "arxiv_2401.99999",
                "source": "arxiv",
                "source_record_id": "2401.99999",
                "title": "Some New Paper",
                "authors": ["V."],
                "pdf_url": "https://arxiv.org/pdf/2401.99999.pdf",
                "external_ids": {"arxiv": "2401.99999"},
            }
            result = asyncio.run(huggingface.add_paper_from_source(arxiv_paper))
            assert result["success"] and result["paper"]["id"] == "2401.99999", result
            assert result["paper"]["arxiv_url"] == "https://arxiv.org/abs/2401.99999"

            # duplicate arXiv id vs the default seed papers
            dup_arxiv = {
                "id": "arxiv_1706.03762",
                "source": "arxiv",
                "source_record_id": "1706.03762",
                "title": "Attention",
                "authors": ["V."],
                "external_ids": {"arxiv": "1706.03762"},
            }
            result = asyncio.run(huggingface.add_paper_from_source(dup_arxiv))
            assert not result["success"], result

            # record lookup
            rec = huggingface.get_paper_record("openalex_W123")
            assert rec and rec["title"] == "Test Paper"
        finally:
            huggingface.PAPERS_FILE = original
    print("PASS add_paper_from_source + dedup + get_paper_record")


if __name__ == "__main__":
    test_registry()
    test_arxiv_discover()
    test_openalex_discover()
    test_add_from_source()
    print("\nAll source smoke tests passed.")
    sys.exit(0)
