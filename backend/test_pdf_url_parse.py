"""Tests for pdf_url parsing (P1-002)."""

import asyncio
from unittest.mock import AsyncMock, patch

from services.source_paper import resolve_pdf_url, resolve_cache_key_for_paper_id
from services.pdf_parser import download_pdf_url, download_and_parse_url

MINIMAL_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


def test_resolve_pdf_url_open_access_only():
    paper = {
        "id": "openalex:W123",
        "source": "openalex",
        "source_record_id": "W123",
        "title": "OA Paper",
        "pdf_url": "https://example.org/paper.pdf",
    }
    assert resolve_pdf_url(paper) == "https://example.org/paper.pdf"


def test_resolve_cache_key_for_pdf_only_paper():
    papers = [
        {
            "id": "openalex:W123",
            "source": "openalex",
            "source_record_id": "W123",
            "title": "OA Paper",
            "pdf_url": "https://example.org/paper.pdf",
        }
    ]
    assert resolve_cache_key_for_paper_id(papers, "openalex:W123") == "openalex_W123"


def test_download_pdf_url_rejects_html():
    async def run():
        mock_response = AsyncMock()
        mock_response.raise_for_status = lambda: None
        mock_response.headers = {"content-type": "text/html"}
        mock_response.content = b"<html>not a pdf</html>"

        with patch("services.pdf_parser.httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.__aenter__.return_value = client
            client.get = AsyncMock(return_value=mock_response)
            client_cls.return_value = client
            try:
                await download_pdf_url("https://example.org/landing")
                assert False, "expected ValueError"
            except ValueError as exc:
                assert "did not return a PDF" in str(exc)

    asyncio.run(run())


def test_download_and_parse_url_happy_path():
    async def run():
        with patch("builtins.print"):
            with patch("services.pdf_parser.download_pdf_url", new=AsyncMock(return_value=MINIMAL_PDF)):
                with patch(
                    "services.pdf_parser.parse_pdf_bytes",
                    new=AsyncMock(
                        return_value={
                            "success": True,
                            "markdown": "# Research Paper\n\ntest",
                            "size_bytes": len(MINIMAL_PDF),
                            "error": None,
                            "method": "pymupdf",
                        }
                    ),
                ):
                    result = await download_and_parse_url("https://example.org/paper.pdf")
        assert result.get("error") is None, result
        assert result["success"] is True
        assert result["source_url"] == "https://example.org/paper.pdf"

    asyncio.run(run())


if __name__ == "__main__":
    test_resolve_pdf_url_open_access_only()
    test_resolve_cache_key_for_pdf_only_paper()
    test_download_pdf_url_rejects_html()
    test_download_and_parse_url_happy_path()
    print("OK: all P1-002 tests passed")
