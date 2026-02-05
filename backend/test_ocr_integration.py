"""
Test script for OCR endpoint integration
"""
import asyncio
from services.pdf_parser import check_ocr_endpoint, download_and_parse_paper

def test_ocr_endpoint():
    """Test if OCR endpoint is available"""
    print("=" * 60)
    print("Testing OCR Endpoint Detection")
    print("=" * 60)
    
    server_url = "http://localhost:8080/v1/chat/completions"
    is_available = check_ocr_endpoint(server_url)
    
    if is_available:
        print("[OK] OCR endpoint is AVAILABLE at", server_url)
        print("     Papers will be parsed using the local OCR model")
    else:
        print("[X] OCR endpoint is NOT available")
        print("    Papers will be parsed using PyMuPDF (fallback)")
    
    print("=" * 60)
    return is_available

async def test_parse_paper():
    """Test parsing a sample paper"""
    print("\n" + "=" * 60)
    print("Testing Paper Parsing")
    print("=" * 60)
    
    # Use a small, known paper for testing
    test_url = "https://arxiv.org/abs/1706.03762"  # Attention Is All You Need
    
    print(f"\nTest paper: {test_url}")
    print("\nStarting parse operation...")
    
    result = await download_and_parse_paper(test_url)
    
    print("\n" + "-" * 60)
    print("Parse Result:")
    print("-" * 60)
    print(f"Success: {result.get('success')}")
    print(f"Method: {result.get('method')}")
    print(f"Size: {result.get('size_bytes')} bytes")
    
    if result.get('success'):
        markdown_preview = result.get('markdown', '')[:500]
        print(f"\nMarkdown preview (first 500 chars):")
        print("-" * 60)
        print(markdown_preview)
        print("-" * 60)
    else:
        print(f"Error: {result.get('error')}")
    
    if result.get('ocr_error'):
        print(f"\nOCR Error (fell back to PyMuPDF): {result.get('ocr_error')}")
    
    print("=" * 60)
    return result

if __name__ == "__main__":
    # Test 1: Check OCR endpoint
    ocr_available = test_ocr_endpoint()
    
    # Test 2: Ask user if they want to test parsing
    print("\n")
    response = input("Do you want to test paper parsing? (y/n): ").strip().lower()
    
    if response == 'y':
        asyncio.run(test_parse_paper())
    else:
        print("\nSkipping paper parsing test.")
        print("Integration test complete!")
