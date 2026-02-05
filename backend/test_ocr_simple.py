"""
Simple automated test for OCR endpoint integration
"""
from services.pdf_parser import check_ocr_endpoint

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
        print("\nIntegration Status: SUCCESS")
        print("When you parse papers, they will use the OCR endpoint.")
    else:
        print("[X] OCR endpoint is NOT available")
        print("    Papers will be parsed using PyMuPDF (fallback)")
        print("\nIntegration Status: FALLBACK MODE")
        print("Start your vLLM OCR server to enable OCR parsing.")
    
    print("=" * 60)
    return is_available

if __name__ == "__main__":
    test_ocr_endpoint()
