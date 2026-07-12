"""Source-neutral models for paper discovery providers."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SourcePaper(BaseModel):
    """Normalized paper record returned by any discovery provider."""
    id: str  # source-neutral id, e.g. "arxiv_1706.03762" or "openalex_W123"
    source: str  # provider id, e.g. "arxiv", "openalex"
    source_record_id: str  # native id inside the source
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    published_date: Optional[str] = None  # ISO date
    landing_url: Optional[str] = None
    pdf_url: Optional[str] = None
    is_open_access: Optional[bool] = None
    citation_count: Optional[int] = None
    relevance_score: Optional[float] = None
    fields_of_study: List[str] = Field(default_factory=list)
    venue: Optional[str] = None
    external_ids: Dict[str, str] = Field(default_factory=dict)


class SourceField(BaseModel):
    """A filterable field/category exposed by a provider."""
    id: str
    label: str


class SourceInfo(BaseModel):
    """Describes a discovery provider for the UI."""
    id: str
    label: str
    fields: List[SourceField] = Field(default_factory=list)
