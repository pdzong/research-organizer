from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
from services.huggingface import fetch_papers, add_paper, add_paper_from_semantic_scholar
from services.pdf_parser import download_and_parse_paper
from services.openai_service import summarize_paper
from services.semantic_scholar import get_paper_metadata
from services import cache_service

router = APIRouter()

class AnalyzeRequest(BaseModel):
    markdown: str

class AddPaperRequest(BaseModel):
    arxiv_url: str

class AddRelatedPaperRequest(BaseModel):
    paper_id: str
    arxiv_id: Optional[str] = None
    title: str
    authors: List[str]

class PaperResponse(BaseModel):
    id: str
    title: str
    authors: List[str]
    arxiv_url: Optional[str]
    arxiv_id: Optional[str]

class ParseResponse(BaseModel):
    success: bool
    markdown: Optional[str]
    size_bytes: Optional[int]
    error: Optional[str]
    from_cache: Optional[bool] = False

class AnalyzeResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None  # Structured analysis dict
    usage: Optional[Dict] = None  # Contains model, input_tokens, output_tokens
    error: Optional[str] = None
    from_cache: Optional[bool] = False

class AddPaperResponse(BaseModel):
    success: bool
    paper: Optional[PaperResponse] = None
    message: Optional[str] = None
    error: Optional[str] = None

class MetadataResponse(BaseModel):
    success: bool
    metadata: Optional[Dict] = None
    error: Optional[str] = None
    from_cache: Optional[bool] = False

class SimplePaperInfo(BaseModel):
    title: str
    authors: List[str]
    arxiv_id: Optional[str] = None

class AddApplicationRequest(BaseModel):
    application: Dict  # Contains domain and specific_utility
    current_paper: SimplePaperInfo
    related_papers: List[SimplePaperInfo]

class AddApplicationResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

@router.get("/papers", response_model=List[PaperResponse])
async def get_papers():
    """
    Get list of papers from local JSON file.
    """
    try:
        papers = await fetch_papers()
        return papers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching papers: {str(e)}")

@router.post("/papers/add", response_model=AddPaperResponse)
async def add_new_paper(request: AddPaperRequest):
    """
    Add a new paper by ArXiv URL.
    Validates the URL and fetches metadata from ArXiv.
    
    Args:
        request: AddPaperRequest with arxiv_url field
    """
    try:
        result = await add_paper(request.arxiv_url)
        return result
    except Exception as e:
        return {
            "success": False,
            "paper": None,
            "message": None,
            "error": str(e)
        }

@router.post("/papers/add-related", response_model=AddPaperResponse)
async def add_related_paper(request: AddRelatedPaperRequest):
    """
    Add a related paper from Semantic Scholar data.
    
    Args:
        request: AddRelatedPaperRequest with paper_id, arxiv_id (optional), title, and authors
    """
    try:
        result = await add_paper_from_semantic_scholar(
            paper_id=request.paper_id,
            arxiv_id=request.arxiv_id,
            title=request.title,
            authors=request.authors
        )
        return result
    except Exception as e:
        return {
            "success": False,
            "paper": None,
            "message": None,
            "error": str(e)
        }

@router.get("/papers/{paper_id}/parse", response_model=ParseResponse)
async def parse_paper(
    paper_id: str, 
    arxiv_url: Optional[str] = None,
    force_reload: bool = Query(False, description="Force reload even if cached")
):
    """
    Download and parse a paper's PDF to markdown.
    
    Args:
        paper_id: The paper ID (ArXiv ID)
        arxiv_url: Optional ArXiv URL. If not provided, will construct from paper_id
        force_reload: If True, bypass cache and re-download
    """
    try:
        # Check cache first unless force reload
        if not force_reload:
            cached_markdown = cache_service.load_markdown(paper_id)
            if cached_markdown:
                print(f"Loaded markdown from cache for {paper_id}")
                return {
                    "success": True,
                    "markdown": cached_markdown,
                    "size_bytes": len(cached_markdown.encode('utf-8')),
                    "error": None,
                    "from_cache": True
                }
        
        # If no arxiv_url provided, construct from paper_id
        if not arxiv_url:
            arxiv_url = f"https://arxiv.org/abs/{paper_id}"
        
        result = await download_and_parse_paper(arxiv_url)
        
        # Cache the result if successful
        if result.get("success") and result.get("markdown"):
            cache_service.save_markdown(paper_id, result["markdown"])
            print(f"Saved markdown to cache for {paper_id}")
        
        result["from_cache"] = False
        return result
    
    except Exception as e:
        return {
            "success": False,
            "markdown": None,
            "size_bytes": None,
            "error": str(e),
            "from_cache": False
        }

@router.post("/papers/analyze", response_model=AnalyzeResponse)
async def analyze_paper(request: AnalyzeRequest):
    """
    Analyze a paper's markdown content using OpenAI.
    This endpoint doesn't use cache - use the GET endpoint for cached analysis.
    
    Args:
        request: AnalyzeRequest with markdown field
    """
    try:
        if not request.markdown:
            raise HTTPException(status_code=400, detail="Markdown content is required")
        
        result = await summarize_paper(request.markdown)
        return result
    
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "usage": None,
            "error": str(e)
        }

@router.get("/papers/{arxiv_id}/analyze", response_model=AnalyzeResponse)
async def get_cached_analysis(
    arxiv_id: str,
    force_reload: bool = Query(False, description="Force regenerate even if cached")
):
    """
    Get cached analysis or generate new one.
    
    Args:
        arxiv_id: The ArXiv ID
        force_reload: If True, bypass cache and regenerate
    """
    try:
        # Check cache first unless force reload
        if not force_reload:
            cached_analysis = cache_service.load_analysis(arxiv_id)
            if cached_analysis:
                print(f"Loaded analysis from cache for {arxiv_id}")
                cached_analysis["from_cache"] = True
                return cached_analysis
        
        # Need to load markdown to analyze
        markdown = cache_service.load_markdown(arxiv_id)
        if not markdown:
            return {
                "success": False,
                "data": None,
                "usage": None,
                "error": "Paper must be parsed first before analysis",
                "from_cache": False
            }
        
        # Generate new analysis
        result = await summarize_paper(markdown)
        
        # Cache the result if successful
        if result.get("success") and result.get("data"):
            cache_service.save_analysis(arxiv_id, result)
            print(f"Saved analysis to cache for {arxiv_id}")
        
        result["from_cache"] = False
        return result
    
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "usage": None,
            "error": str(e),
            "from_cache": False
        }

@router.get("/papers/{arxiv_id}/metadata", response_model=MetadataResponse)
async def get_paper_metadata_endpoint(
    arxiv_id: str,
    force_reload: bool = Query(False, description="Force reload even if cached")
):
    """
    Get rich metadata from Semantic Scholar for a paper.
    
    Args:
        arxiv_id: The ArXiv ID of the paper
        force_reload: If True, bypass cache and fetch fresh data
    """
    try:
        # Check cache first unless force reload
        if not force_reload:
            cached_metadata = cache_service.load_metadata(arxiv_id)
            if cached_metadata:
                print(f"Loaded metadata from cache for {arxiv_id}")
                return {
                    "success": True,
                    "metadata": cached_metadata,
                    "error": None,
                    "from_cache": True
                }
        
        result = await get_paper_metadata(arxiv_id)
        
        # Cache the result if successful
        if result.get("success"):
            cache_service.save_metadata(arxiv_id, result)
            print(f"Saved metadata to cache for {arxiv_id}")
            
            return {
                "success": True,
                "metadata": result,
                "error": None,
                "from_cache": False
            }
        else:
            return {
                "success": False,
                "metadata": None,
                "error": result.get("error", "Unknown error"),
                "from_cache": False
            }
    except Exception as e:
        return {
            "success": False,
            "metadata": None,
            "error": str(e),
            "from_cache": False
        }

@router.get("/papers/{arxiv_id}/cache-status")
async def get_cache_status(arxiv_id: str):
    """
    Get cache status for a paper.
    
    Args:
        arxiv_id: The ArXiv ID
    """
    return cache_service.get_cache_status(arxiv_id)

@router.post("/applications/add", response_model=AddApplicationResponse)
async def add_application(request: AddApplicationRequest):
    """
    Add an application idea to the applications.json file.
    
    Args:
        request: AddApplicationRequest with application data, current paper, and related papers
    """
    try:
        cache_service.save_application(
            application=request.application,
            current_paper=request.current_paper.dict(),
            related_papers=[p.dict() for p in request.related_papers]
        )
        return {
            "success": True,
            "message": f"Application '{request.application.get('domain', 'Unknown')}' saved successfully",
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "message": None,
            "error": str(e)
        }

@router.get("/applications")
async def get_applications():
    """
    Get all saved applications from applications.json.
    """
    try:
        applications = cache_service.load_applications()
        return {
            "success": True,
            "applications": applications,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "applications": [],
            "error": str(e)
        }
