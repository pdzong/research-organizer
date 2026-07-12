import httpx
import json
import os
import re
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

from .source_paper import SourcePaper, enrich_storage_dict, normalize_legacy_paper

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

def load_papers() -> List[Dict[str, Any]]:
    """Load papers from JSON file, create with defaults if doesn't exist."""
    try:
        if PAPERS_FILE.exists():
            with open(PAPERS_FILE, 'r', encoding='utf-8') as f:
                papers = json.load(f)
                normalized = [enrich_storage_dict(p) for p in papers]
                print(f"Loaded {len(normalized)} papers from {PAPERS_FILE}")
                return normalized
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

def save_papers(papers: List[Dict[str, Any]]) -> bool:
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
                "paper": normalize_legacy_paper({
                    "id": arxiv_id,
                    "title": title,
                    "authors": authors,
                    "arxiv_url": normalized_url,
                    "arxiv_id": arxiv_id,
                }).to_storage_dict(),
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
    
    # Check if paper already exists (by stable id or arxiv_id)
    if any(
        p.get("id") == paper.get("id")
        or (paper.get("arxiv_id") and p.get("arxiv_id") == paper["arxiv_id"])
        for p in papers
    ):
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

async def fetch_papers() -> List[Dict[str, Any]]:
    """
    Fetch papers from local JSON file.
    """
    return load_papers()


def add_source_paper(paper: SourcePaper) -> dict:
    """
    Add a normalized ``SourcePaper`` to the library (P1-005).

    Dedupes on stable id, DOI, and ArXiv id across sources.
    """
    papers = load_papers()

    doi = paper.doi
    arxiv_id = paper.arxiv_id
    for p in papers:
        if p.get("id") == paper.id:
            return {"success": False, "error": f"Paper {paper.id} already exists in the list"}
        existing_ids = p.get("external_ids") or {}
        if doi and (existing_ids.get("doi") == doi or p.get("doi") == doi):
            return {"success": False, "error": f"Paper with DOI {doi} already exists in the list"}
        if arxiv_id and p.get("arxiv_id") == arxiv_id:
            return {"success": False, "error": f"Paper with ArXiv ID {arxiv_id} already exists in the list"}

    record = paper.to_storage_dict()
    record["added_date"] = datetime.now().isoformat()
    papers.insert(0, record)

    if save_papers(papers):
        return {"success": True, "paper": record, "message": f"Added paper: {paper.title}"}
    return {"success": False, "error": "Failed to save paper to file"}

async def add_paper_from_semantic_scholar(paper_id: str, arxiv_id: Optional[str], title: str, authors: List[str]) -> dict:
    """
    Add a paper from Semantic Scholar data.
    
    Args:
        paper_id: The Semantic Scholar paper ID
        arxiv_id: Optional ArXiv ID
        title: Paper title
        authors: List of author names
    
    Returns:
        dict with success status and paper data
    """
    papers = load_papers()
    
    # Use arxiv_id as the primary ID if available, otherwise use paper_id
    primary_id = arxiv_id if arxiv_id else paper_id
    
    # Check if paper already exists (by arxiv_id or paper_id)
    for p in papers:
        if p.get("arxiv_id") == arxiv_id and arxiv_id:
            return {
                "success": False,
                "error": f"Paper with ArXiv ID {arxiv_id} already exists in the list"
            }
        if p.get("id") == primary_id:
            return {
                "success": False,
                "error": f"Paper {primary_id} already exists in the list"
            }
    
    # Create paper object
    arxiv_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None
    
    paper = normalize_legacy_paper({
        "id": primary_id,
        "title": title,
        "authors": authors if isinstance(authors, list) else [authors],
        "arxiv_url": arxiv_url,
        "arxiv_id": arxiv_id,
        "semantic_scholar_id": paper_id,
        "added_date": datetime.now().isoformat(),
        "cache_status": {},
        "source": "arxiv" if arxiv_id else "semantic_scholar",
        "source_record_id": arxiv_id or paper_id,
        "external_ids": {
            **({"arxiv": arxiv_id} if arxiv_id else {}),
            "s2": paper_id,
        },
    }).to_storage_dict()
    
    # Add paper to the beginning of the list
    papers.insert(0, paper)
    
    # Save updated list
    if save_papers(papers):
        return {
            "success": True,
            "paper": paper,
            "message": f"Added paper: {title}"
        }
    else:
        return {
            "success": False,
            "error": "Failed to save papers list"
        }
