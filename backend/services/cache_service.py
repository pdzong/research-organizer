import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Cache directory structure
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
PAPERS_FILE = Path(__file__).parent.parent / "data" / "papers.json"
APPLICATIONS_FILE = CACHE_DIR / "applications.json"

def ensure_cache_dir(arxiv_id: str) -> Path:
    """Ensure cache directory exists for a paper."""
    paper_cache_dir = CACHE_DIR / arxiv_id
    paper_cache_dir.mkdir(parents=True, exist_ok=True)
    return paper_cache_dir

def save_metadata(arxiv_id: str, metadata: Dict[str, Any]) -> bool:
    """Save metadata to cache."""
    try:
        cache_dir = ensure_cache_dir(arxiv_id)
        metadata_file = cache_dir / "metadata.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        update_paper_cache_ref(arxiv_id, "metadata", str(metadata_file.relative_to(CACHE_DIR.parent)))
        return True
    except Exception as e:
        print(f"Error saving metadata cache: {e}")
        return False

def load_metadata(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """Load metadata from cache."""
    try:
        cache_dir = CACHE_DIR / arxiv_id
        metadata_file = cache_dir / "metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Error loading metadata cache: {e}")
        return None

def save_markdown(arxiv_id: str, markdown: str) -> bool:
    """Save markdown to cache."""
    try:
        cache_dir = ensure_cache_dir(arxiv_id)
        markdown_file = cache_dir / "markdown.md"
        
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        update_paper_cache_ref(arxiv_id, "markdown", str(markdown_file.relative_to(CACHE_DIR.parent)))
        return True
    except Exception as e:
        print(f"Error saving markdown cache: {e}")
        return False

def load_markdown(arxiv_id: str) -> Optional[str]:
    """Load markdown from cache."""
    try:
        cache_dir = CACHE_DIR / arxiv_id
        markdown_file = cache_dir / "markdown.md"
        
        if markdown_file.exists():
            with open(markdown_file, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    except Exception as e:
        print(f"Error loading markdown cache: {e}")
        return None

def save_analysis(arxiv_id: str, analysis: Dict[str, Any]) -> bool:
    """Save analysis to cache."""
    try:
        cache_dir = ensure_cache_dir(arxiv_id)
        analysis_file = cache_dir / "analysis.json"
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        update_paper_cache_ref(arxiv_id, "analysis", str(analysis_file.relative_to(CACHE_DIR.parent)))
        return True
    except Exception as e:
        print(f"Error saving analysis cache: {e}")
        return False

def load_analysis(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """Load analysis from cache."""
    try:
        cache_dir = CACHE_DIR / arxiv_id
        analysis_file = cache_dir / "analysis.json"
        
        if analysis_file.exists():
            with open(analysis_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Error loading analysis cache: {e}")
        return None

def update_paper_cache_ref(arxiv_id: str, cache_type: str, file_path: str):
    """Update papers.json with cache reference."""
    try:
        if not PAPERS_FILE.exists():
            return
        
        with open(PAPERS_FILE, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        
        # Find the paper and update cache reference
        for paper in papers:
            if paper.get("arxiv_id") == arxiv_id:
                if "cached" not in paper:
                    paper["cached"] = {}
                if "lastUpdated" not in paper["cached"]:
                    paper["cached"]["lastUpdated"] = {}
                
                paper["cached"][cache_type] = file_path
                paper["cached"]["lastUpdated"][cache_type] = datetime.utcnow().isoformat()
                break
        
        with open(PAPERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)
    
    except Exception as e:
        print(f"Error updating paper cache reference: {e}")

def save_sections(arxiv_id: str, sections: Dict[str, Any]) -> bool:
    """Save paper sections to cache."""
    try:
        cache_dir = ensure_cache_dir(arxiv_id)
        sections_file = cache_dir / "sections.json"
        
        with open(sections_file, 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=2, ensure_ascii=False)
        
        update_paper_cache_ref(arxiv_id, "sections", str(sections_file.relative_to(CACHE_DIR.parent)))
        return True
    except Exception as e:
        print(f"Error saving sections cache: {e}")
        return False

def load_sections(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """Load paper sections from cache."""
    try:
        cache_dir = CACHE_DIR / arxiv_id
        sections_file = cache_dir / "sections.json"
        
        if sections_file.exists():
            with open(sections_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Error loading sections cache: {e}")
        return None

def get_cache_status(arxiv_id: str) -> Dict[str, bool]:
    """Check which cache files exist for a paper."""
    cache_dir = CACHE_DIR / arxiv_id
    
    return {
        "metadata": (cache_dir / "metadata.json").exists(),
        "markdown": (cache_dir / "markdown.md").exists(),
        "sections": (cache_dir / "sections.json").exists(),
        "analysis": (cache_dir / "analysis.json").exists()
    }

def clear_cache(arxiv_id: str, cache_type: Optional[str] = None) -> bool:
    """Clear cache for a paper. If cache_type is None, clear all."""
    try:
        cache_dir = CACHE_DIR / arxiv_id
        
        if not cache_dir.exists():
            return True
        
        if cache_type:
            # Clear specific cache
            file_map = {
                "metadata": "metadata.json",
                "markdown": "markdown.md",
                "sections": "sections.json",
                "analysis": "analysis.json"
            }
            cache_file = cache_dir / file_map.get(cache_type, "")
            if cache_file.exists():
                cache_file.unlink()
        else:
            # Clear all cache for this paper
            import shutil
            shutil.rmtree(cache_dir)
        
        return True
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return False

def save_application(application: Dict[str, Any], current_paper: Dict[str, Any], related_papers: list) -> bool:
    """
    Save an application idea to applications.json.
    
    Args:
        application: Dict with 'domain' and 'specific_utility' fields
        current_paper: Dict with 'title', 'authors', and optional 'arxiv_id'
        related_papers: List of dicts, each with 'title', 'authors', and optional 'arxiv_id'
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure cache directory exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load existing applications or create new list
        applications = []
        if APPLICATIONS_FILE.exists():
            with open(APPLICATIONS_FILE, 'r', encoding='utf-8') as f:
                applications = json.load(f)
        
        # Create new application entry
        new_entry = {
            "id": datetime.utcnow().isoformat(),
            "application": application,
            "current_paper": current_paper,
            "related_papers": related_papers,
            "added_at": datetime.utcnow().isoformat()
        }
        
        applications.append(new_entry)
        
        # Save back to file
        with open(APPLICATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(applications, f, indent=2, ensure_ascii=False)
        
        print(f"Saved application '{application.get('domain', 'Unknown')}' to applications.json")
        return True
    
    except Exception as e:
        print(f"Error saving application: {e}")
        return False

def load_applications() -> list:
    """
    Load all applications from applications.json.
    
    Returns:
        List of application entries, or empty list if file doesn't exist
    """
    try:
        if APPLICATIONS_FILE.exists():
            with open(APPLICATIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading applications: {e}")
        return []
