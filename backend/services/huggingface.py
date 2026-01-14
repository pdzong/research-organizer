import httpx
import json
import os
import re
from typing import List, Dict, Optional
from pathlib import Path

PAPERS_FILE = Path(__file__).parent.parent / "data" / "papers.json"

def get_default_papers() -> List[Dict[str, any]]:
    """Return default curated list of papers."""
    return [
        {
            "id": "1706.03762",
            "title": "Attention Is All You Need",
            "authors": ["Vaswani et al."],
            "arxiv_url": "https://arxiv.org/abs/1706.03762",
            "arxiv_id": "1706.03762"
        },
        {
            "id": "2303.08774",
            "title": "GPT-4 Technical Report",
            "authors": ["OpenAI"],
            "arxiv_url": "https://arxiv.org/abs/2303.08774",
            "arxiv_id": "2303.08774"
        },
        {
            "id": "2307.09288",
            "title": "Llama 2: Open Foundation and Fine-Tuned Chat Models",
            "authors": ["Touvron et al."],
            "arxiv_url": "https://arxiv.org/abs/2307.09288",
            "arxiv_id": "2307.09288"
        },
        {
            "id": "2005.14165",
            "title": "Language Models are Few-Shot Learners (GPT-3)",
            "authors": ["Brown et al."],
            "arxiv_url": "https://arxiv.org/abs/2005.14165",
            "arxiv_id": "2005.14165"
        },
        {
            "id": "2103.00020",
            "title": "Learning Transferable Visual Models From Natural Language Supervision (CLIP)",
            "authors": ["Radford et al."],
            "arxiv_url": "https://arxiv.org/abs/2103.00020",
            "arxiv_id": "2103.00020"
        },
        {
            "id": "2010.11929",
            "title": "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale (ViT)",
            "authors": ["Dosovitskiy et al."],
            "arxiv_url": "https://arxiv.org/abs/2010.11929",
            "arxiv_id": "2010.11929"
        },
        {
            "id": "1810.04805",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "authors": ["Devlin et al."],
            "arxiv_url": "https://arxiv.org/abs/1810.04805",
            "arxiv_id": "1810.04805"
        },
        {
            "id": "2106.09685",
            "title": "LoRA: Low-Rank Adaptation of Large Language Models",
            "authors": ["Hu et al."],
            "arxiv_url": "https://arxiv.org/abs/2106.09685",
            "arxiv_id": "2106.09685"
        }
    ]

def load_papers() -> List[Dict[str, any]]:
    """Load papers from JSON file, create with defaults if doesn't exist."""
    try:
        if PAPERS_FILE.exists():
            with open(PAPERS_FILE, 'r', encoding='utf-8') as f:
                papers = json.load(f)
                print(f"Loaded {len(papers)} papers from {PAPERS_FILE}")
                return papers
        else:
            # Create data directory and default papers file
            PAPERS_FILE.parent.mkdir(parents=True, exist_ok=True)
            papers = get_default_papers()
            save_papers(papers)
            print(f"Created new papers file with {len(papers)} default papers")
            return papers
    except Exception as e:
        print(f"Error loading papers file: {e}. Using defaults.")
        return get_default_papers()

def save_papers(papers: List[Dict[str, any]]) -> bool:
    """Save papers to JSON file."""
    try:
        PAPERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PAPERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving papers: {e}")
        return False

def extract_arxiv_id(url: str) -> Optional[str]:
    """Extract ArXiv ID from URL."""
    # Match patterns like: arxiv.org/abs/1234.5678 or arxiv.org/pdf/1234.5678.pdf
    match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', url)
    if match:
        return match.group(1)
    # Also try just the ID pattern
    match = re.search(r'(\d{4}\.\d{4,5})', url)
    if match:
        return match.group(1)
    return None

async def validate_arxiv_url(arxiv_url: str) -> dict:
    """
    Validate ArXiv URL and fetch basic metadata.
    Returns dict with success status and paper info.
    """
    try:
        # Extract and validate arxiv ID
        arxiv_id = extract_arxiv_id(arxiv_url)
        if not arxiv_id:
            return {
                "success": False,
                "error": "Invalid ArXiv URL format. Expected format: https://arxiv.org/abs/XXXX.XXXXX"
            }
        
        # Normalize URL to abs format
        normalized_url = f"https://arxiv.org/abs/{arxiv_id}"
        
        # Try to fetch the page to validate it exists
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(normalized_url)
            
            if response.status_code == 404:
                return {
                    "success": False,
                    "error": f"Paper {arxiv_id} not found on ArXiv"
                }
            
            response.raise_for_status()
            
            # Try to extract title from the page
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = "Unknown Title"
            authors = ["Unknown"]
            
            # Try to extract title
            title_tag = soup.find('h1', class_='title')
            if title_tag:
                title = title_tag.get_text(strip=True).replace('Title:', '').strip()
            
            # Try to extract authors
            authors_tag = soup.find('div', class_='authors')
            if authors_tag:
                author_links = authors_tag.find_all('a')
                if author_links:
                    authors = [a.get_text(strip=True) for a in author_links[:5]]
            
            return {
                "success": True,
                "paper": {
                    "id": arxiv_id,
                    "title": title,
                    "authors": authors,
                    "arxiv_url": normalized_url,
                    "arxiv_id": arxiv_id
                }
            }
    
    except httpx.HTTPError as e:
        return {
            "success": False,
            "error": f"Failed to validate ArXiv URL: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error validating paper: {str(e)}"
        }

async def add_paper(arxiv_url: str) -> dict:
    """
    Add a new paper by ArXiv URL.
    Validates the URL and adds it to the papers list.
    """
    # Validate the URL and fetch metadata
    result = await validate_arxiv_url(arxiv_url)
    
    if not result["success"]:
        return result
    
    paper = result["paper"]
    
    # Load existing papers
    papers = load_papers()
    
    # Check if paper already exists
    if any(p["arxiv_id"] == paper["arxiv_id"] for p in papers):
        return {
            "success": False,
            "error": f"Paper {paper['arxiv_id']} already exists in the list"
        }
    
    # Add paper to the beginning of the list
    papers.insert(0, paper)
    
    # Save updated list
    if save_papers(papers):
        return {
            "success": True,
            "paper": paper,
            "message": f"Successfully added paper {paper['arxiv_id']}"
        }
    else:
        return {
            "success": False,
            "error": "Failed to save paper to file"
        }

async def fetch_papers() -> List[Dict[str, any]]:
    """
    Fetch papers from local JSON file.
    """
    return load_papers()
