"""
Smoke test for the PDF_PARSER_MODE feature flag and parser fallback chain
(Z.ai GLM-OCR API path preserved from PR #7).

Run from backend/: python test_parser_modes.py
No network or OCR server required (download_pdf is stubbed).
"""
import asyncio
import os
import sys

import fitz

from services import pdf_parser


def make_test_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "INTRODUCTION TO TESTING")
    page.insert_text((72, 100), "This is a tiny test paper used for parser smoke tests.")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_get_parser_mode():
    os.environ.pop("PDF_PARSER_MODE", None)
    assert pdf_parser.get_parser_mode() == "auto", "default should be auto"

    os.environ["PDF_PARSER_MODE"] = "nonsense"
    assert pdf_parser.get_parser_mode() == "auto", "invalid value should fall back to auto"

    for mode in pdf_parser.VALID_PARSER_MODES:
        os.environ["PDF_PARSER_MODE"] = mode.upper()
        assert pdf_parser.get_parser_mode() == mode, f"mode {mode} should round-trip"
    print("PASS get_parser_mode")


def test_select_parser():
    unreachable = "http://localhost:1/v1/chat/completions"

    os.environ.pop("ZAI_API_KEY", None)
    assert pdf_parser._select_parser("auto", unreachable) == "pymupdf"

    os.environ["ZAI_API_KEY"] = "test-key"
    assert pdf_parser._select_parser("auto", unreachable) == "zai_ocr"

    # auto with no OCR URL configured still resolves via Z.ai key
    assert pdf_parser._select_parser("auto", "") == "zai_ocr"

    assert pdf_parser._select_parser("pymupdf", unreachable) == "pymupdf"
    assert pdf_parser._select_parser("local_ocr", unreachable) == "local_ocr"
    assert pdf_parser._select_parser("zai_ocr", unreachable) == "zai_ocr"
    print("PASS _select_parser")


def test_zai_requires_key():
    os.environ.pop("ZAI_API_KEY", None)
    try:
        pdf_parser.pdf_bytes_to_markdown_zai(make_test_pdf())
    except RuntimeError as e:
        assert "ZAI_API_KEY" in str(e)
        print("PASS pdf_bytes_to_markdown_zai raises without key")
        return
    raise AssertionError("expected RuntimeError without ZAI_API_KEY")


def test_pymupdf_parse():
    md = pdf_parser.parse_pdf_to_markdown(make_test_pdf())
    assert "tiny test paper" in md, md[:200]
    print("PASS parse_pdf_to_markdown")


def test_end_to_end_fallbacks():
    pdf_bytes = make_test_pdf()

    async def fake_download(url):
        return pdf_bytes

    original = pdf_parser.download_pdf
    pdf_parser.download_pdf = fake_download
    unreachable = "http://localhost:1/v1/chat/completions"
    try:
        # pymupdf mode -> method pymupdf
        os.environ["PDF_PARSER_MODE"] = "pymupdf"
        result = asyncio.run(pdf_parser.download_and_parse_paper("http://x", unreachable))
        assert result["success"] and result["method"] == "pymupdf", result

        # forced zai_ocr without key -> graceful pymupdf fallback
        os.environ["PDF_PARSER_MODE"] = "zai_ocr"
        os.environ.pop("ZAI_API_KEY", None)
        result = asyncio.run(pdf_parser.download_and_parse_paper("http://x", unreachable))
        assert result["success"] and result["method"] == "pymupdf_fallback", result
        assert "ZAI_API_KEY" in result["ocr_error"], result

        # forced local_ocr with server down -> fail fast, pymupdf fallback
        os.environ["PDF_PARSER_MODE"] = "local_ocr"
        result = asyncio.run(pdf_parser.download_and_parse_paper("http://x", unreachable))
        assert result["success"] and result["method"] == "pymupdf_fallback", result
        assert "not reachable" in result["ocr_error"], result

        # auto without anything available -> plain pymupdf
        os.environ["PDF_PARSER_MODE"] = "auto"
        os.environ.pop("ZAI_API_KEY", None)
        result = asyncio.run(pdf_parser.download_and_parse_paper("http://x", unreachable))
        assert result["success"] and result["method"] == "pymupdf", result
    finally:
        pdf_parser.download_pdf = original
        os.environ.pop("PDF_PARSER_MODE", None)
        os.environ.pop("ZAI_API_KEY", None)
    print("PASS download_and_parse_paper fallback chain")


if __name__ == "__main__":
    test_get_parser_mode()
    test_select_parser()
    test_zai_requires_key()
    test_pymupdf_parse()
    test_end_to_end_fallbacks()
    print("\nAll parser-mode smoke tests passed.")
    sys.exit(0)
