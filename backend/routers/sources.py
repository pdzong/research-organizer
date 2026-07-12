from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.sources import SourceInfo, SourcePaper, get_provider, list_sources

router = APIRouter()


class DiscoverResponse(BaseModel):
    success: bool
    source: str
    papers: List[SourcePaper] = []
    error: Optional[str] = None


@router.get("/sources", response_model=List[SourceInfo])
async def get_sources():
    """List available paper discovery sources and their filterable fields."""
    return list_sources()


@router.get("/sources/{source_id}/discover", response_model=DiscoverResponse)
async def discover_papers(
    source_id: str,
    query: Optional[str] = Query(None, description="Free-text search query"),
    field: Optional[str] = Query(None, description="Field/category id from the source's field list"),
    days: int = Query(30, ge=1, le=365, description="Only papers published in the last N days"),
    limit: int = Query(20, ge=1, le=50),
    sort: str = Query("relevance", pattern="^(relevance|recency|citations)$"),
):
    """
    Discover recent papers from a source, ranked by relevance, recency or
    citations (where the source supports the metric).
    """
    provider = get_provider(source_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Unknown source '{source_id}'")

    try:
        papers = await provider.discover(
            query=query, field=field, days=days, limit=limit, sort=sort
        )
        return DiscoverResponse(success=True, source=source_id, papers=papers)
    except Exception as e:
        return DiscoverResponse(success=False, source=source_id, papers=[], error=str(e))
