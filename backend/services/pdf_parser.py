import httpx
import fitz  # PyMuPDF
from typing import Optional
import re
import os
import time
import tempfile
from pdf2image import convert_from_bytes
import requests

def check_ocr_endpoint(server_url: str = "http://localhost:8080/v1/chat/completions", timeout: float = 2.0) -> bool:
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
    server_url: str = "http://localhost:8080/v1/chat/completions"
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
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": file_url}}
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


async def download_pdf(arxiv_url: str) -> bytes:
    """
    Download PDF from ArXiv given an ArXiv URL.
    Converts abs URL to pdf URL if needed.
    """
    # Convert arxiv.org/abs/XXXX to arxiv.org/pdf/XXXX.pdf
    pdf_url = arxiv_url.replace('/abs/', '/pdf/')
    if not pdf_url.endswith('.pdf'):
        pdf_url += '.pdf'
    
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(pdf_url)
        response.raise_for_status()
        return response.content

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

async def download_and_parse_paper(arxiv_url: str, ocr_server_url: str = "http://localhost:8080/v1/chat/completions") -> dict:
    """
    Download and parse a paper from ArXiv.
    Attempts to use local OCR endpoint if available, falls back to PyMuPDF if not.
    
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
        
        # Check if OCR endpoint is available
        ocr_available = check_ocr_endpoint(ocr_server_url)
        
        if ocr_available:
            print("🔍 OCR endpoint detected, using local OCR model...")
            try:
                markdown = pdf_bytes_to_markdown_ocr(pdf_bytes, ocr_server_url)
                print("✅ OCR parsing successful")
                
                return {
                    "success": True,
                    "markdown": markdown,
                    "size_bytes": len(pdf_bytes),
                    "error": None,
                    "method": "ocr"
                }
            except Exception as ocr_error:
                print(f"⚠️ OCR parsing failed: {ocr_error}")
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
            print("📄 OCR endpoint not available, using PyMuPDF parser...")
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
