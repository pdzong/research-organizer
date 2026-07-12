"""Tests for the generalized add-paper flow (P1-005)."""

from unittest.mock import patch

from routers.papers import _paper_from_direct_pdf_url
from services.huggingface import add_source_paper
from services.source_paper import SourcePaper


def _openalex_paper() -> SourcePaper:
    return SourcePaper(
        id="openalex:W2741809807",
        source="openalex",
        source_record_id="W2741809807",
        title="The state of OA",
        authors=["Heather Piwowar"],
        abstract="An analysis of open access.",
        pdf_url="https://example.org/oa.pdf",
        is_open_access=True,
        external_ids={"openalex": "W2741809807", "doi": "10.7717/peerj.4375"},
    )


def test_paper_from_direct_pdf_url():
    paper = _paper_from_direct_pdf_url("https://example.org/papers/cool_result-v2.pdf")
    assert paper.source == "web"
    assert paper.pdf_url == "https://example.org/papers/cool_result-v2.pdf"
    assert paper.title == "cool result v2"
    assert paper.id.startswith("web:")


def test_add_source_paper_and_dedupe():
    stored = []

    def fake_save(papers):
        stored.clear()
        stored.extend(papers)
        return True

    with patch("services.huggingface.load_papers", side_effect=lambda: list(stored)), \
         patch("services.huggingface.save_papers", side_effect=fake_save):
        result = add_source_paper(_openalex_paper())
        assert result["success"], result.get("error")
        assert stored[0]["id"] == "openalex:W2741809807"
        assert stored[0]["added_date"]

        # Same stable id → rejected
        dup = add_source_paper(_openalex_paper())
        assert not dup["success"]

        # Different id but same DOI → rejected
        doi_dup = _openalex_paper()
        doi_dup.id = "doi:10.7717/peerj.4375"
        result = add_source_paper(doi_dup)
        assert not result["success"]
        assert "DOI" in result["error"]


if __name__ == "__main__":
    test_paper_from_direct_pdf_url()
    test_add_source_paper_and_dedupe()
    print("All generalized add-paper tests passed.")
