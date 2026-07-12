import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .source_paper import paper_matches_cache_ref

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
            if paper_matches_cache_ref(paper, arxiv_id):
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

def save_application(application: Dict[str, Any], current_paper: Dict[str, Any], related_papers: list) -> Optional[str]:
    """
    Save an application idea to applications.json.

    Args:
        application: Dict with 'domain' and 'specific_utility' fields
        current_paper: Dict with 'title', 'authors', and optional 'arxiv_id'
        related_papers: List of dicts, each with 'title', 'authors', and optional 'arxiv_id'

    Returns:
        The new entry's ``id`` on success, ``None`` on failure.
        (Callers that treated this as a ``bool`` still work: ``id`` strings are truthy.)
    """
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        applications = []
        if APPLICATIONS_FILE.exists():
            with open(APPLICATIONS_FILE, 'r', encoding='utf-8') as f:
                applications = json.load(f)

        entry_id = datetime.utcnow().isoformat()
        new_entry = {
            "id": entry_id,
            "application": application,
            "current_paper": current_paper,
            "related_papers": related_papers,
            "added_at": datetime.utcnow().isoformat()
        }

        applications.append(new_entry)

        with open(APPLICATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(applications, f, indent=2, ensure_ascii=False)

        print(f"Saved application '{application.get('domain', 'Unknown')}' to applications.json")
        return entry_id

    except Exception as e:
        print(f"Error saving application: {e}")
        return None

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


def load_application(application_id: str) -> Optional[Dict[str, Any]]:
    """Find a single application entry by its ``id`` field."""
    for app in load_applications():
        if app.get("id") == application_id:
            return app
    return None


# ─── Solution plans ──────────────────────────────────────────────────────────

SOLUTIONS_DIR = CACHE_DIR / "solutions"


def _solutions_dir() -> Path:
    SOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SOLUTIONS_DIR


def _safe_id(application_id: str) -> str:
    # ISO timestamps contain ':' which is illegal on Windows file systems.
    return application_id.replace(":", "-").replace("/", "_")


def save_solution_plan(application_id: str, payload: Dict[str, Any]) -> bool:
    """
    Persist a generated solution plan. Stored both as JSON (for the API) and
    as a standalone .md file (for downstream code-gen pipelines / humans).
    """
    try:
        directory = _solutions_dir()
        safe = _safe_id(application_id)

        record = {
            "application_id": application_id,
            "generated_at": datetime.utcnow().isoformat(),
            **payload,
        }

        (directory / f"{safe}.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        if payload.get("markdown"):
            (directory / f"{safe}.md").write_text(
                payload["markdown"], encoding="utf-8"
            )
        return True
    except Exception as e:
        print(f"Error saving solution plan: {e}")
        return False


def load_solution_plan(application_id: str) -> Optional[Dict[str, Any]]:
    try:
        path = _solutions_dir() / f"{_safe_id(application_id)}.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading solution plan: {e}")
        return None


def list_solution_plans() -> list:
    """Return all generated plans, newest first."""
    try:
        directory = _solutions_dir()
        plans = []
        for p in directory.glob("*.json"):
            try:
                plans.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        plans.sort(key=lambda r: r.get("generated_at", ""), reverse=True)
        return plans
    except Exception as e:
        print(f"Error listing solution plans: {e}")
        return []
