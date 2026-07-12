"""OpenAlex discovery provider."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

from ..source_paper import SourcePaper

OPENALEX_WORKS_URL = "https://api.openalex.org/works"


def _openalex_email() -> Optional[str]:
    return os.environ.get("OPENALEX_EMAIL") or os.environ.get("CONTACT_EMAIL")


def extract_openalex_id(work_id: str) -> str:
    """``https://openalex.org/W123`` → ``W123``."""
    return work_id.rsplit("/", 1)[-1]


def reconstruct_abstract(
    inverted_index: Optional[Dict[str, List[int]]],
) -> Optional[str]:
    if not inverted_index:
        return None
    max_pos = max(pos for positions in inverted_index.values() for pos in positions)
    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    text = " ".join(words).strip()
    return text or None


def _location_pdf_url(location: Optional[Dict[str, Any]]) -> Optional[str]:
    if not location:
        return None
    return location.get("pdf_url")


def _location_landing_url(location: Optional[Dict[str, Any]]) -> Optional[str]:
    if not location:
        return None
    return location.get("landing_page_url") or location.get("pdf_url")


def _normalize_doi(doi: Optional[str]) -> Optional[str]:
    if not doi:
        return None
    return doi.replace("https://doi.org/", "").strip()


def normalize_openalex_work(work: Dict[str, Any]) -> SourcePaper:
    """Map an OpenAlex work object to ``SourcePaper``."""
    openalex_id = extract_openalex_id(work["id"])
    external_ids: Dict[str, str] = {"openalex": openalex_id}

    doi = _normalize_doi(work.get("doi"))
    if doi:
        external_ids["doi"] = doi

    ids = work.get("ids") or {}
    if ids.get("arxiv"):
        external_ids["arxiv"] = ids["arxiv"].replace("https://arxiv.org/abs/", "")
    if ids.get("pmid"):
        external_ids["pmid"] = str(ids["pmid"]).replace(
            "https://pubmed.ncbi.nlm.nih.gov/", ""
        )
    if ids.get("pmcid"):
        external_ids["pmcid"] = str(ids["pmcid"]).replace(
            "https://www.ncbi.nlm.nih.gov/pmc/articles/", ""
        ).strip("/")

    authors: List[str] = []
    for authorship in work.get("authorships") or []:
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            authors.append(name)

    oa = work.get("open_access") or {}
    best_oa = work.get("best_oa_location") or {}
    primary = work.get("primary_location") or {}

    pdf_url = _location_pdf_url(best_oa) or _location_pdf_url(primary)
    landing_url = _location_landing_url(primary) or _location_landing_url(best_oa)
    if not landing_url and doi:
        landing_url = f"https://doi.org/{doi}"

    license_info = best_oa.get("license") or primary.get("license")
    license_id = None
    if isinstance(license_info, dict):
        license_id = license_info.get("id")
    elif isinstance(license_info, str):
        license_id = license_info

    topics = [
        topic.get("display_name")
        for topic in (work.get("topics") or [])
        if topic.get("display_name")
    ]

    source_metadata = {
        "cited_by_count": work.get("cited_by_count"),
        "publication_year": work.get("publication_year"),
        "type": work.get("type"),
        "topics": topics[:8],
        "oa_status": oa.get("oa_status"),
        "openalex_url": work.get("id"),
    }

    return SourcePaper(
        id=f"openalex:{openalex_id}",
        source="openalex",
        source_record_id=openalex_id,
        title=work.get("display_name") or work.get("title") or "Unknown Title",
        authors=authors,
        abstract=reconstruct_abstract(work.get("abstract_inverted_index")),
        published_date=work.get("publication_date"),
        landing_url=landing_url,
        pdf_url=pdf_url,
        is_open_access=oa.get("is_oa"),
        license=license_id,
        external_ids=external_ids,
        source_metadata=source_metadata,
    )


async def get_openalex_work(identifier: str) -> Optional[SourcePaper]:
    """
    Fetch a single OpenAlex work by OpenAlex ID (``W…``) or DOI (``10.…``).
    Returns ``None`` when the work is not found.
    """
    ident = identifier.strip()
    if ident.lower().startswith("10."):
        path = f"doi:{ident}"
    elif ident.lower().startswith("https://doi.org/"):
        path = f"doi:{ident[len('https://doi.org/'):]}"
    else:
        path = extract_openalex_id(ident)

    params: Dict[str, Any] = {}
    email = _openalex_email()
    if email:
        params["mailto"] = email

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{OPENALEX_WORKS_URL}/{path}", params=params)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return normalize_openalex_work(response.json())


async def search_openalex_works(
    query: Optional[str] = None,
    limit: int = 20,
    since: Optional[str] = None,
    open_access_only: bool = True,
) -> List[SourcePaper]:
    """
    Search OpenAlex works, newest first.

    Uses the polite pool when ``OPENALEX_EMAIL`` or ``CONTACT_EMAIL`` is set.
    """
    # Relevance sort for keyword searches; date sort otherwise. Sorting
    # searches by date surfaces junk records with bogus future dates.
    params: Dict[str, Any] = {
        "per-page": min(max(limit, 1), 200),
        "sort": "relevance_score:desc" if query else "publication_date:desc",
    }
    email = _openalex_email()
    if email:
        params["mailto"] = email

    filters: List[str] = []
    if open_access_only:
        filters.append("is_oa:true")
    if since:
        filters.append(f"from_publication_date:{since}")
    if filters:
        params["filter"] = ",".join(filters)
    if query:
        params["search"] = query

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(OPENALEX_WORKS_URL, params=params)
        response.raise_for_status()
        data = response.json()

    papers: List[SourcePaper] = []
    for work in data.get("results", [])[:limit]:
        papers.append(normalize_openalex_work(work))
    return papers
