"""
Source-neutral paper records (P1-001).

Normalizes legacy ArXiv-centric ``papers.json`` entries at read time without
moving on-disk cache directories.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, computed_field

PaperDict = Dict[str, Any]
PaperInput = Union[PaperDict, "SourcePaper"]


def _safe_cache_segment(value: str) -> str:
    """Filesystem-safe segment for cache directory names."""
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", value.strip())


def _as_dict(paper: PaperInput) -> PaperDict:
    if isinstance(paper, SourcePaper):
        return paper.to_storage_dict()
    return dict(paper)


class SourcePaper(BaseModel):
    """Canonical, source-neutral paper record."""

    id: str = Field(..., description="Stable app id, e.g. arxiv:1706.03762 or doi:10.xxxx/yyyy")
    source: str = Field(..., description="Origin provider, e.g. arxiv, openalex, crossref")
    source_record_id: str = Field(..., description="Provider-native record identifier")
    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    published_date: Optional[str] = None
    landing_url: Optional[str] = None
    pdf_url: Optional[str] = None
    fulltext_url: Optional[str] = None
    is_open_access: Optional[bool] = None
    license: Optional[str] = None
    external_ids: Dict[str, str] = Field(default_factory=dict)
    source_metadata: Dict[str, Any] = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def arxiv_id(self) -> Optional[str]:
        return self.external_ids.get("arxiv")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def doi(self) -> Optional[str]:
        return self.external_ids.get("doi")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def oa_status(self) -> Optional[str]:
        if self.is_open_access is True:
            return "open"
        if self.is_open_access is False:
            return "closed"
        return None

    def to_storage_dict(self, extra: Optional[PaperDict] = None) -> PaperDict:
        """Merge normalized fields into a JSON-serializable dict for ``papers.json``."""
        out: PaperDict = dict(extra or {})
        out.update(self.model_dump(exclude_none=True))
        if self.arxiv_id:
            out["arxiv_id"] = self.arxiv_id
            if self.source == "arxiv" and self.landing_url:
                out["arxiv_url"] = self.landing_url
        if self.oa_status is not None:
            out["oa_status"] = self.oa_status
        return out


def normalize_legacy_paper(raw: PaperDict) -> SourcePaper:
    """
    Convert a legacy or partial paper dict into a ``SourcePaper``.

    Existing ArXiv-only records keep working; cache paths stay on bare ``arxiv_id``.
    """
    data = dict(raw)
    arxiv_id = data.get("arxiv_id")
    external_ids = dict(data.get("external_ids") or {})

    if arxiv_id and "arxiv" not in external_ids:
        external_ids["arxiv"] = arxiv_id
    if data.get("doi") and "doi" not in external_ids:
        external_ids["doi"] = data["doi"]
    if data.get("semantic_scholar_id") and "s2" not in external_ids:
        external_ids["s2"] = data["semantic_scholar_id"]

    source = data.get("source")
    if not source:
        if arxiv_id:
            source = "arxiv"
        elif external_ids.get("doi"):
            source = "crossref"
        elif external_ids.get("openalex"):
            source = "openalex"
        else:
            source = "unknown"

    source_record_id = data.get("source_record_id")
    if not source_record_id:
        if arxiv_id:
            source_record_id = arxiv_id
        elif external_ids.get("openalex"):
            source_record_id = external_ids["openalex"]
        elif external_ids.get("doi"):
            source_record_id = external_ids["doi"]
        elif data.get("id"):
            source_record_id = str(data["id"])
        else:
            source_record_id = "unknown"

    paper_id = data.get("id")
    if not paper_id or (arxiv_id and paper_id == arxiv_id):
        if arxiv_id:
            paper_id = f"arxiv:{arxiv_id}"
        elif external_ids.get("doi"):
            paper_id = f"doi:{external_ids['doi']}"
        else:
            paper_id = f"{source}:{source_record_id}"

    landing_url = data.get("landing_url") or data.get("arxiv_url")
    pdf_url = data.get("pdf_url")
    if not pdf_url and arxiv_id:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    is_open_access = data.get("is_open_access")
    if is_open_access is None and data.get("oa_status") is not None:
        oa = data.get("oa_status")
        if isinstance(oa, bool):
            is_open_access = oa
        elif isinstance(oa, str):
            is_open_access = oa.lower() not in ("closed", "false", "no")
    if is_open_access is None and arxiv_id:
        is_open_access = True

    return SourcePaper(
        id=paper_id,
        source=source,
        source_record_id=source_record_id,
        title=data.get("title") or "Unknown Title",
        authors=list(data.get("authors") or []),
        abstract=data.get("abstract"),
        published_date=data.get("published_date"),
        landing_url=landing_url,
        pdf_url=pdf_url,
        fulltext_url=data.get("fulltext_url"),
        is_open_access=is_open_access,
        license=data.get("license"),
        external_ids=external_ids,
        source_metadata=dict(data.get("source_metadata") or {}),
    )


def enrich_storage_dict(raw: PaperDict) -> PaperDict:
    """Normalize at read time; preserve extra keys (``cached``, dates, etc.)."""
    paper = normalize_legacy_paper(raw)
    return paper.to_storage_dict(extra=raw)


def paper_cache_key(paper: PaperInput) -> str:
    """
    Stable source-neutral cache key for *new* papers.

    Format: ``arxiv_1706.03762``, ``doi_10.1145_1234567``, ``openalex_W123…``
    """
    data = _as_dict(paper)
    external_ids = data.get("external_ids") or {}

    if external_ids.get("doi"):
        return "doi_" + _safe_cache_segment(external_ids["doi"])
    if external_ids.get("arxiv"):
        return "arxiv_" + _safe_cache_segment(external_ids["arxiv"])
    if external_ids.get("pmcid"):
        return "pmcid_" + _safe_cache_segment(external_ids["pmcid"])
    if external_ids.get("pmid"):
        return "pmid_" + _safe_cache_segment(external_ids["pmid"])
    if external_ids.get("s2"):
        return "s2_" + _safe_cache_segment(external_ids["s2"])
    if external_ids.get("openalex"):
        return "openalex_" + _safe_cache_segment(external_ids["openalex"])

    source = data.get("source") or "unknown"
    record_id = data.get("source_record_id") or data.get("id") or "unknown"
    return _safe_cache_segment(f"{source}:{record_id}")


def paper_legacy_cache_key(paper: PaperInput) -> str:
    """
    On-disk cache directory name.

    Legacy ArXiv caches live at ``cache/{arxiv_id}/``; this helper keeps that
    path until a later migration phase moves directories.
    """
    data = _as_dict(paper)
    external_ids = data.get("external_ids") or {}
    arxiv = external_ids.get("arxiv") or data.get("arxiv_id")
    if arxiv:
        return arxiv
    return paper_cache_key(paper)


def paper_matches_cache_ref(paper: PaperDict, ref_id: str) -> bool:
    """True if ``ref_id`` refers to this paper's on-disk cache directory."""
    if not ref_id:
        return False
    if paper.get("arxiv_id") == ref_id or paper.get("id") == ref_id:
        return True
    try:
        enriched = enrich_storage_dict(paper)
        return paper_legacy_cache_key(enriched) == ref_id
    except Exception:
        return False


def find_paper_by_id(papers: List[PaperDict], paper_id: str) -> Optional[PaperDict]:
    """Look up a paper record by stable id, legacy arxiv id, or cache key."""
    for raw in papers:
        enriched = enrich_storage_dict(raw)
        if enriched.get("id") == paper_id:
            return enriched
        if enriched.get("arxiv_id") == paper_id:
            return enriched
        if paper_legacy_cache_key(enriched) == paper_id:
            return enriched
        if enriched.get("id", "").endswith(f":{paper_id}"):
            return enriched
    return None


def resolve_pdf_url(paper: PaperDict) -> Optional[str]:
    """Return a direct PDF URL for the paper, if known."""
    data = enrich_storage_dict(paper) if not paper.get("source") else dict(paper)
    if data.get("pdf_url"):
        return data["pdf_url"]

    arxiv_id = data.get("arxiv_id")
    if arxiv_id:
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    landing = data.get("landing_url") or data.get("arxiv_url")
    if landing and "arxiv.org" in landing:
        pdf_url = landing.replace("/abs/", "/pdf/")
        if not pdf_url.endswith(".pdf"):
            pdf_url = pdf_url.rstrip("/") + ".pdf"
        return pdf_url

    return None


def resolve_cache_key_for_paper_id(papers: List[PaperDict], paper_id: str) -> str:
    """Map a route ``paper_id`` to the on-disk cache directory name."""
    paper = find_paper_by_id(papers, paper_id)
    if paper:
        return paper_legacy_cache_key(paper)
    if paper_id.startswith("arxiv:"):
        return paper_id.split(":", 1)[1]
    return paper_id
