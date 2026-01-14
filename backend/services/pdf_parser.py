import httpx
import fitz  # PyMuPDF
from typing import Optional
import re

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

async def download_and_parse_paper(arxiv_url: str) -> dict:
    """
    Download and parse a paper from ArXiv.
    Returns a dict with markdown content and metadata.
    """
    try:
        # Download PDF
        pdf_bytes = await download_pdf(arxiv_url)
        
        # Parse to markdown
        markdown = parse_pdf_to_markdown(pdf_bytes)
        
        return {
            "success": True,
            "markdown": markdown,
            "size_bytes": len(pdf_bytes),
            "error": None
        }
    
    except Exception as e:
        return {
            "success": False,
            "markdown": None,
            "error": str(e)
        }
