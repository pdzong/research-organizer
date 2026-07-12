"""Source discovery API routes."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.sources import list_sources
from services.sources.openalex import search_openalex_works

router = APIRouter()


class SourceInfo(BaseModel):
    id: str
    label: str
    searchable: bool


class SourcesListResponse(BaseModel):
    success: bool
    sources: List[SourceInfo]


class SourceSearchResponse(BaseModel):
    success: bool
    source: str
    papers: list
    count: int
    error: Optional[str] = None


@router.get("/sources", response_model=SourcesListResponse)
async def get_sources():
    """List configured discovery sources."""
    return {"success": True, "sources": list_sources()}


@router.get("/sources/search", response_model=SourceSearchResponse)
async def search_source_papers(
    source: str = Query(..., description="Source id, e.g. openalex"),
    query: Optional[str] = Query(None, description="Search keywords"),
    limit: int = Query(20, ge=1, le=50, description="Max results"),
    since: Optional[str] = Query(
        None,
        description="Earliest publication date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    open_access_only: bool = Query(
        True, description="Restrict to open-access works when supported"
    ),
):
    """
    Search a discovery source and return normalized ``SourcePaper`` records.
    """
    if source != "openalex":
        raise HTTPException(
            status_code=400,
            detail=f"Source '{source}' is not searchable yet. Supported: openalex",
        )

    try:
        papers = await search_openalex_works(
            query=query,
            limit=limit,
            since=since,
            open_access_only=open_access_only,
        )
        payload = [paper.to_storage_dict() for paper in papers]
        return {
            "success": True,
            "source": source,
            "papers": payload,
            "count": len(payload),
            "error": None,
        }
    except Exception as exc:
        return {
            "success": False,
            "source": source,
            "papers": [],
            "count": 0,
            "error": str(exc),
        }
