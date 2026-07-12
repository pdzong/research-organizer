"""OpenAlex discovery provider (https://docs.openalex.org/api-entities/works).

Free, no API key. Provides ready-made ranking metrics: relevance_score
(when searching), publication_date recency and cited_by_count, plus a
26-field taxonomy for filtering.
"""
import os
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import httpx

from .models import SourceField, SourcePaper

_API_URL = "https://api.openalex.org/works"

# OpenAlex top-level field taxonomy (stable ids, verified against
# https://api.openalex.org/fields).
_FIELDS = [
    SourceField(id="17", label="Computer Science"),
    SourceField(id="22", label="Engineering"),
    SourceField(id="27", label="Medicine"),
    SourceField(id="31", label="Physics and Astronomy"),
    SourceField(id="26", label="Mathematics"),
    SourceField(id="13", label="Biochemistry, Genetics and Molecular Biology"),
    SourceField(id="11", label="Agricultural and Biological Sciences"),
    SourceField(id="28", label="Neuroscience"),
    SourceField(id="16", label="Chemistry"),
    SourceField(id="25", label="Materials Science"),
    SourceField(id="23", label="Environmental Science"),
    SourceField(id="19", label="Earth and Planetary Sciences"),
    SourceField(id="21", label="Energy"),
    SourceField(id="15", label="Chemical Engineering"),
    SourceField(id="24", label="Immunology and Microbiology"),
    SourceField(id="30", label="Pharmacology, Toxicology and Pharmaceutics"),
    SourceField(id="32", label="Psychology"),
    SourceField(id="33", label="Social Sciences"),
    SourceField(id="20", label="Economics, Econometrics and Finance"),
    SourceField(id="14", label="Business, Management and Accounting"),
    SourceField(id="18", label="Decision Sciences"),
    SourceField(id="36", label="Health Professions"),
    SourceField(id="29", label="Nursing"),
    SourceField(id="12", label="Arts and Humanities"),
    SourceField(id="35", label="Dentistry"),
    SourceField(id="34", label="Veterinary"),
]

_ARXIV_URL_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})")


def _reconstruct_abstract(inverted_index: Optional[dict]) -> Optional[str]:
    """OpenAlex returns abstracts as an inverted index; rebuild plain text."""
    if not inverted_index:
        return None
    positions = []
    for word, indexes in inverted_index.items():
        for idx in indexes:
            positions.append((idx, word))
    positions.sort()
    return " ".join(word for _, word in positions) or None


def _extract_arxiv_id(work: dict) -> Optional[str]:
    """Detect an arXiv id from any of the work's locations."""
    for loc in work.get("locations") or []:
        for key in ("pdf_url", "landing_page_url"):
            url = (loc or {}).get(key) or ""
            match = _ARXIV_URL_RE.search(url)
            if match:
                return match.group(1)
    return None


def _extract_pdf_url(work: dict) -> Optional[str]:
    """
    Find a direct PDF URL. The has_pdf_url filter matches *any* location,
    so fall back to scanning all locations when best_oa/primary lack one.
    """
    best_oa = work.get("best_oa_location") or {}
    primary = work.get("primary_location") or {}
    if best_oa.get("pdf_url"):
        return best_oa["pdf_url"]
    if primary.get("pdf_url"):
        return primary["pdf_url"]
    for loc in work.get("locations") or []:
        if (loc or {}).get("pdf_url"):
            return loc["pdf_url"]
    return None


class OpenAlexProvider:
    id = "openalex"
    label = "OpenAlex"

    def fields(self) -> List[SourceField]:
        return _FIELDS

    async def discover(
        self,
        query: Optional[str] = None,
        field: Optional[str] = None,
        days: Optional[int] = None,
        limit: int = 20,
        sort: str = "relevance",
    ) -> List[SourcePaper]:
        # Only open-access works with a direct PDF are useful downstream:
        # everything discovered here must be parseable by the existing flow.
        filters = ["is_oa:true", "has_pdf_url:true"]
        if days:
            since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
            filters.append(f"from_publication_date:{since}")
        if field:
            filters.append(f"primary_topic.field.id:fields/{field}")

        # relevance_score sorting is only valid together with `search`.
        if sort == "relevance" and query:
            sort_param = "relevance_score:desc"
        elif sort == "citations":
            sort_param = "cited_by_count:desc"
        else:
            sort_param = "publication_date:desc"

        params = {
            "filter": ",".join(filters),
            "sort": sort_param,
            "per-page": limit,
        }
        if query:
            params["search"] = query
        contact = os.environ.get("OPENALEX_EMAIL") or os.environ.get("CONTACT_EMAIL")
        if contact:
            params["mailto"] = contact

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(_API_URL, params=params)
            response.raise_for_status()
            data = response.json()

        return [self._normalize(work) for work in data.get("results", [])]

    def _normalize(self, work: dict) -> SourcePaper:
        openalex_id = (work.get("id") or "").rsplit("/", 1)[-1]  # W1234567890
        best_oa = work.get("best_oa_location") or {}
        primary = work.get("primary_location") or {}
        primary_topic = work.get("primary_topic") or {}

        external_ids = {"openalex": openalex_id}
        doi_url = (work.get("ids") or {}).get("doi") or ""
        if doi_url:
            external_ids["doi"] = doi_url.replace("https://doi.org/", "")
        arxiv_id = _extract_arxiv_id(work)
        if arxiv_id:
            external_ids["arxiv"] = arxiv_id

        fields_of_study = []
        field_name = (primary_topic.get("field") or {}).get("display_name")
        if field_name:
            fields_of_study.append(field_name)
        topic_name = primary_topic.get("display_name")
        if topic_name and topic_name not in fields_of_study:
            fields_of_study.append(topic_name)

        venue = ((best_oa.get("source") or primary.get("source")) or {}).get("display_name")

        return SourcePaper(
            id=f"openalex_{openalex_id}",
            source=self.id,
            source_record_id=openalex_id,
            title=work.get("display_name") or "Untitled",
            authors=[
                ((a.get("author") or {}).get("display_name") or "Unknown")
                for a in (work.get("authorships") or [])[:8]
            ],
            abstract=_reconstruct_abstract(work.get("abstract_inverted_index")),
            published_date=work.get("publication_date"),
            landing_url=best_oa.get("landing_page_url") or primary.get("landing_page_url") or doi_url or None,
            pdf_url=_extract_pdf_url(work),
            is_open_access=(work.get("open_access") or {}).get("is_oa"),
            citation_count=work.get("cited_by_count"),
            relevance_score=work.get("relevance_score"),
            fields_of_study=fields_of_study,
            venue=venue,
            external_ids=external_ids,
        )
