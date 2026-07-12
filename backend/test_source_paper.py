"""Smoke tests for source-neutral paper records (P1-001)."""

from services.source_paper import (
    enrich_storage_dict,
    normalize_legacy_paper,
    paper_cache_key,
    paper_legacy_cache_key,
    paper_matches_cache_ref,
    find_paper_by_id,
    resolve_pdf_url,
    resolve_cache_key_for_paper_id,
)


def test_legacy_arxiv_record():
    raw = {
        "id": "1706.03762",
        "title": "Attention Is All You Need",
        "authors": ["Vaswani et al."],
        "arxiv_url": "https://arxiv.org/abs/1706.03762",
        "arxiv_id": "1706.03762",
    }
    paper = normalize_legacy_paper(raw)
    assert paper.id == "arxiv:1706.03762"
    assert paper.source == "arxiv"
    assert paper.arxiv_id == "1706.03762"
    assert paper.pdf_url == "https://arxiv.org/pdf/1706.03762.pdf"
    assert paper.is_open_access is True
    assert paper_legacy_cache_key(paper) == "1706.03762"
    assert paper_cache_key(paper) == "arxiv_1706.03762"


def test_enrich_preserves_cached_and_legacy_fields():
    raw = {
        "id": "2604.15308",
        "title": "RAD-2",
        "authors": ["A"],
        "arxiv_url": "https://arxiv.org/abs/2604.15308",
        "arxiv_id": "2604.15308",
        "cached": {"markdown": "cache/2604.15308/markdown.md"},
    }
    out = enrich_storage_dict(raw)
    assert out["id"] == "arxiv:2604.15308"
    assert out["arxiv_id"] == "2604.15308"
    assert out["arxiv_url"] == "https://arxiv.org/abs/2604.15308"
    assert out["cached"]["markdown"] == "cache/2604.15308/markdown.md"
    assert out["source"] == "arxiv"
    assert out["pdf_url"].endswith(".pdf")


def test_openalex_style_record():
    raw = {
        "id": "openalex:W1234567890",
        "source": "openalex",
        "source_record_id": "W1234567890",
        "title": "Robotics survey",
        "authors": ["Smith"],
        "doi": "10.1234/example",
        "pdf_url": "https://example.org/paper.pdf",
        "is_open_access": True,
        "license": "CC-BY",
    }
    paper = normalize_legacy_paper(raw)
    assert paper.doi == "10.1234/example"
    assert paper.source == "openalex"
    assert paper_cache_key(paper) == "doi_10.1234_example"
    assert paper_legacy_cache_key(paper) == "doi_10.1234_example"


def test_paper_matches_cache_ref():
    paper = {"id": "arxiv:1706.03762", "arxiv_id": "1706.03762"}
    assert paper_matches_cache_ref(paper, "1706.03762")
    assert paper_matches_cache_ref(paper, "arxiv:1706.03762")


def test_resolve_pdf_url_and_find_paper():
    papers = [
        {
            "id": "openalex:W999",
            "source": "openalex",
            "source_record_id": "W999",
            "title": "OA only",
            "pdf_url": "https://example.org/oa.pdf",
        }
    ]
    found = find_paper_by_id(papers, "openalex:W999")
    assert found is not None
    assert resolve_pdf_url(found) == "https://example.org/oa.pdf"
    assert resolve_cache_key_for_paper_id(papers, "openalex:W999") == "openalex_W999"


if __name__ == "__main__":
    test_legacy_arxiv_record()
    test_enrich_preserves_cached_and_legacy_fields()
    test_openalex_style_record()
    test_paper_matches_cache_ref()
    test_resolve_pdf_url_and_find_paper()
    print("OK: all source_paper tests passed")
