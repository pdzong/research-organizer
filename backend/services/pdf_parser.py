import base64
import httpx
import fitz  # PyMuPDF
from typing import Optional
import re
import os
import time
import tempfile
from pdf2image import convert_from_bytes
import requests

# Allow the OCR server URL to be overridden via environment variable so the
# same code works both locally (localhost:8080) and inside Docker (ocr:8080).
_DEFAULT_OCR_URL = os.environ.get(
    "OCR_SERVER_URL", "http://localhost:8080/v1/chat/completions"
)

# Z.ai hosted GLM-OCR (layout parsing) API. Same model as the local vLLM
# service, but fully managed — no GPU required.
_DEFAULT_ZAI_OCR_URL = os.environ.get(
    "ZAI_OCR_URL", "https://api.z.ai/api/paas/v4/layout_parsing"
)

# Z.ai limits for the layout_parsing endpoint
_ZAI_MAX_PDF_BYTES = 50 * 1024 * 1024
_ZAI_MAX_PDF_PAGES = 100

VALID_PARSER_MODES = ("auto", "local_ocr", "zai_ocr", "pymupdf")


def get_parser_mode() -> str:
    """
    Resolve the PDF parser feature flag from the environment.

    Modes:
        auto      - local OCR if reachable -> Z.ai API if key set -> PyMuPDF
        local_ocr - local vLLM GLM-OCR (PyMuPDF fallback on failure)
        zai_ocr   - hosted Z.ai GLM-OCR API (PyMuPDF fallback on failure)
        pymupdf   - pure-Python text extraction, no OCR
    """
    mode = os.environ.get("PDF_PARSER_MODE", "auto").strip().lower()
    if mode not in VALID_PARSER_MODES:
        print(f"⚠️ Unknown PDF_PARSER_MODE '{mode}', falling back to 'auto'")
        return "auto"
    return mode

def check_ocr_endpoint(server_url: str = _DEFAULT_OCR_URL, timeout: float = 2.0) -> bool:
    """
    Check if the local OCR endpoint is available.
    
    Args:
        server_url: URL of the vLLM OCR server
        timeout: Timeout in seconds for the health check
    
    Returns:
        True if endpoint is available, False otherwise
    """
    try:
        # Try to reach the server root or models endpoint
        base_url = server_url.rsplit('/v1/', 1)[0]
        health_url = f"{base_url}/health"
        
        response = requests.get(health_url, timeout=timeout)
        return response.status_code == 200
    except:
        # If health check fails, try the main endpoint with a minimal request
        try:
            # Just check if the endpoint exists (connection is enough)
            response = requests.get(base_url, timeout=timeout)
            return True
        except:
            return False


def pdf_bytes_to_markdown_ocr(
    pdf_bytes: bytes,
    server_url: str = _DEFAULT_OCR_URL,
) -> str:
    """
    Convert PDF bytes to Markdown using local OCR endpoint.
    Processes PDF page-by-page via vLLM server.
    
    Args:
        pdf_bytes: PDF file as bytes
        server_url: URL of the vLLM OCR server
    
    Returns:
        Markdown text extracted from the PDF
    
    Raises:
        Exception if OCR processing fails
    """
    print(f"📖 Starting OCR processing with local endpoint...")
    
    # Convert PDF bytes to images (DPI=150 to prevent token overflow)
    try:
        pages = convert_from_bytes(pdf_bytes, dpi=150)
    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF to images. Error: {e}")

    full_markdown = []
    total_pages = len(pages)
    print(f"📄 Found {total_pages} pages. Starting OCR processing...\n")

    # Process each page
    for i, page_image in enumerate(pages):
        page_num = i + 1
        
        # Create temp file for this page
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_filename = temp_file.name
            abs_temp_path = os.path.abspath(temp_filename)
        
        try:
            # Save image to temp file
            page_image.save(abs_temp_path, "JPEG")

            # PATH TRANSLATION (Windows -> WSL if needed)
            # Check if running on Windows and convert path for WSL
            if os.name == 'nt' and abs_temp_path[1:3] == ':\\':
                # Convert "C:\Users..." to "/mnt/c/Users..."
                drive_letter = abs_temp_path[0].lower()
                wsl_path = f"/mnt/{drive_letter}{abs_temp_path[2:]}".replace("\\", "/")
                file_url = f"file://{wsl_path}"
            else:
                # Unix-like system, use path as-is
                file_url = f"file://{abs_temp_path}"

            prompt_text = (
                "Read this page carefully. Extract all content into a single Markdown format.\n"
                "1. Transcribe text exactly as it appears.\n"
                "2. Convert all mathematical formulas into LaTeX format (enclose in $$).\n"
                "3. Detect tables and convert them into Markdown tables.\n"
                "Do not summarize or skip any content."
            )   

            # Prepare OCR request
            payload = {
                "model": "zai-org/GLM-OCR",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": file_url}},
                            {"type": "text", "text": prompt_text}                         
                        ]
                    }
                ],
                "temperature": 0.0,
                "max_tokens": 4096
            }

            print(f"   ⏳ Processing Page {page_num}/{total_pages}...", end="\r")
            
            start_time = time.time()
            response = requests.post(server_url, json=payload, timeout=120.0)
            response.raise_for_status()
            
            # Extract content
            content = response.json()['choices'][0]['message']['content']
            
            # Add page delimiter
            page_text = f"\n\n## Page {page_num}\n\n{content}"
            full_markdown.append(page_text)
            
            duration = time.time() - start_time
            print(f"   ✅ Page {page_num}/{total_pages} done in {duration:.2f}s")

        except Exception as e:
            print(f"   ❌ Error on Page {page_num}: {e}")
            full_markdown.append(f"\n\n[ERROR PROCESSING PAGE {page_num}]\n\n")
        
        finally:
            # Cleanup temp file
            if os.path.exists(abs_temp_path):
                try:
                    os.remove(abs_temp_path)
                except:
                    pass

    print("\n🎉 OCR Conversion Complete!")
    return "# Research Paper\n\n" + "".join(full_markdown)


def pdf_bytes_to_markdown_zai(
    pdf_bytes: bytes,
    api_url: str = _DEFAULT_ZAI_OCR_URL,
    timeout: float = 300.0,
) -> str:
    """
    Convert PDF bytes to Markdown using the hosted Z.ai GLM-OCR API.

    The whole PDF is sent as a base64 data URI in a single layout_parsing
    call; the API runs the full GLM-OCR pipeline (layout detection + OCR)
    server-side and returns markdown.

    Requires ZAI_API_KEY in the environment.

    Raises:
        Exception if the API call fails or limits are exceeded.
    """
    api_key = os.environ.get("ZAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ZAI_API_KEY is not set.")

    if len(pdf_bytes) > _ZAI_MAX_PDF_BYTES:
        raise RuntimeError(
            f"PDF is {len(pdf_bytes)} bytes, exceeding the Z.ai limit of "
            f"{_ZAI_MAX_PDF_BYTES} bytes."
        )

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        page_count = len(doc)
    if page_count > _ZAI_MAX_PDF_PAGES:
        raise RuntimeError(
            f"PDF has {page_count} pages, exceeding the Z.ai limit of "
            f"{_ZAI_MAX_PDF_PAGES} pages."
        )

    print(f"📖 Sending {page_count}-page PDF to Z.ai GLM-OCR API...")
    data_uri = "data:application/pdf;base64," + base64.b64encode(pdf_bytes).decode("ascii")

    start_time = time.time()
    response = requests.post(
        api_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "glm-ocr",
            "file": data_uri,
            "need_layout_visualization": False,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    result = response.json()

    if "error" in result:
        raise RuntimeError(f"Z.ai GLM-OCR API error: {result['error']}")

    # md_results is normally a top-level string; tolerate per-page lists and
    # responses nested under "data".
    md = result.get("md_results")
    if md is None and isinstance(result.get("data"), dict):
        md = result["data"].get("md_results")
    if isinstance(md, list):
        md = "\n\n".join(str(part) for part in md)
    if not md or not isinstance(md, str):
        raise RuntimeError(f"Z.ai GLM-OCR API returned no markdown: {str(result)[:500]}")

    print(f"✅ Z.ai GLM-OCR done in {time.time() - start_time:.2f}s")
    return md


async def download_pdf(url: str) -> bytes:
    """
    Download a PDF from a URL.

    ArXiv abs URLs are rewritten to their PDF counterpart; any other URL is
    fetched as-is (e.g. a direct open-access pdf_url from OpenAlex).
    """
    pdf_url = url
    if "arxiv.org" in url:
        # Convert arxiv.org/abs/XXXX to arxiv.org/pdf/XXXX.pdf
        pdf_url = url.replace('/abs/', '/pdf/')
        if not pdf_url.endswith('.pdf'):
            pdf_url += '.pdf'

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(pdf_url)
        response.raise_for_status()
        content = response.content

    if not content.lstrip()[:5].startswith(b"%PDF"):
        raise RuntimeError(
            f"URL did not return a PDF (got "
            f"{response.headers.get('content-type', 'unknown content type')}). "
            "It may be a publisher landing page rather than a direct PDF link."
        )
    return content

def parse_pdf_to_markdown(pdf_bytes: bytes) -> str:
    """
    Parse PDF bytes to markdown format using PyMuPDF.
    Extracts text and attempts to preserve structure.
    """
    try:
        # Open PDF from bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        markdown_content = []
        markdown_content.append("# Research Paper\n")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text blocks with position info
            blocks = page.get_text("blocks")
            
            page_text = []
            for block in blocks:
                # block format: (x0, y0, x1, y1, "text", block_no, block_type)
                if len(block) >= 5:
                    text = block[4].strip()
                    if text:
                        page_text.append(text)
            
            # Join blocks with proper spacing
            if page_text:
                markdown_content.append(f"\n## Page {page_num + 1}\n")
                markdown_content.append('\n\n'.join(page_text))
        
        doc.close()
        
        full_text = '\n'.join(markdown_content)
        
        # Post-processing to improve markdown formatting
        full_text = improve_markdown_formatting(full_text)
        
        return full_text
    
    except Exception as e:
        raise Exception(f"Error parsing PDF: {str(e)}")

def improve_markdown_formatting(text: str) -> str:
    """
    Improve the markdown formatting of extracted text.
    """
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Try to identify section headers (all caps or numbered sections)
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            formatted_lines.append('')
            continue
        
        # Check if line is likely a section header
        # Pattern 1: All caps (but not just one word)
        if stripped.isupper() and len(stripped.split()) > 1 and len(stripped) < 100:
            formatted_lines.append(f"\n### {stripped.title()}\n")
        # Pattern 2: Numbered sections like "1. Introduction" or "1 Introduction"
        elif re.match(r'^\d+\.?\s+[A-Z]', stripped):
            formatted_lines.append(f"\n### {stripped}\n")
        # Pattern 3: Roman numerals
        elif re.match(r'^[IVX]+\.?\s+[A-Z]', stripped):
            formatted_lines.append(f"\n### {stripped}\n")
        else:
            formatted_lines.append(stripped)
    
    text = '\n'.join(formatted_lines)
    
    # Clean up excessive newlines again
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text

def _select_parser(mode: str, ocr_server_url: str) -> str:
    """
    Pick the concrete parser ("local_ocr", "zai_ocr" or "pymupdf") for the
    given mode, checking availability where the mode requires it.
    """
    if mode == "auto":
        if check_ocr_endpoint(ocr_server_url):
            print("🔍 Local OCR endpoint detected, using local GLM-OCR...")
            return "local_ocr"
        if os.environ.get("ZAI_API_KEY", "").strip():
            print("☁️ ZAI_API_KEY set, using hosted Z.ai GLM-OCR API...")
            return "zai_ocr"
        print("📄 No OCR available, using PyMuPDF parser...")
        return "pymupdf"
    return mode


def _parse_with(parser: str, pdf_bytes: bytes, ocr_server_url: str) -> str:
    if parser == "local_ocr":
        # Guard against a forced local_ocr mode with the server down: the
        # per-page loop swallows request errors, so fail fast here instead.
        if not check_ocr_endpoint(ocr_server_url):
            raise RuntimeError(f"Local OCR endpoint not reachable at {ocr_server_url}")
        return pdf_bytes_to_markdown_ocr(pdf_bytes, ocr_server_url)
    if parser == "zai_ocr":
        return pdf_bytes_to_markdown_zai(pdf_bytes)
    return parse_pdf_to_markdown(pdf_bytes)


async def download_and_parse_paper(arxiv_url: str, ocr_server_url: str = _DEFAULT_OCR_URL) -> dict:
    """
    Download and parse a paper from ArXiv.

    The parser is chosen by the PDF_PARSER_MODE feature flag (see
    get_parser_mode). OCR parsers fall back to PyMuPDF on failure.

    Args:
        arxiv_url: ArXiv URL of the paper
        ocr_server_url: URL of the local OCR server (optional)

    Returns:
        dict with markdown content and metadata
    """
    try:
        # Download PDF
        print(f"📥 Downloading PDF from {arxiv_url}")
        pdf_bytes = await download_pdf(arxiv_url)
        print(f"✅ Downloaded {len(pdf_bytes)} bytes")

        mode = get_parser_mode()
        parser = _select_parser(mode, ocr_server_url)

        if parser != "pymupdf":
            try:
                markdown = _parse_with(parser, pdf_bytes, ocr_server_url)
                print(f"✅ {parser} parsing successful")

                return {
                    "success": True,
                    "markdown": markdown,
                    "size_bytes": len(pdf_bytes),
                    "error": None,
                    "method": parser
                }
            except Exception as ocr_error:
                print(f"⚠️ {parser} parsing failed: {ocr_error}")
                print("📄 Falling back to PyMuPDF parser...")
                markdown = parse_pdf_to_markdown(pdf_bytes)

                return {
                    "success": True,
                    "markdown": markdown,
                    "size_bytes": len(pdf_bytes),
                    "error": None,
                    "method": "pymupdf_fallback",
                    "ocr_error": str(ocr_error)
                }
        else:
            markdown = parse_pdf_to_markdown(pdf_bytes)

            return {
                "success": True,
                "markdown": markdown,
                "size_bytes": len(pdf_bytes),
                "error": None,
                "method": "pymupdf"
            }

    except Exception as e:
        return {
            "success": False,
            "markdown": None,
            "error": str(e),
            "method": None
        }
