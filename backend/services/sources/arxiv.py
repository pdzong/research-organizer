"""arXiv discovery provider built on the public export API (Atom feed)."""
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import httpx

from .models import SourceField, SourcePaper

_API_URL = "https://export.arxiv.org/api/query"
_ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}

# Curated subset of arXiv categories exposed as filterable "fields" in the UI.
_FIELDS = [
    SourceField(id="cs.AI", label="Artificial Intelligence"),
    SourceField(id="cs.LG", label="Machine Learning"),
    SourceField(id="cs.CL", label="Computation and Language"),
    SourceField(id="cs.CV", label="Computer Vision"),
    SourceField(id="cs.RO", label="Robotics"),
    SourceField(id="cs.NE", label="Neural and Evolutionary Computing"),
    SourceField(id="cs.MA", label="Multiagent Systems"),
    SourceField(id="cs.SE", label="Software Engineering"),
    SourceField(id="cs.CR", label="Cryptography and Security"),
    SourceField(id="cs.DC", label="Distributed Computing"),
    SourceField(id="stat.ML", label="Statistics / Machine Learning"),
    SourceField(id="eess.SY", label="Systems and Control"),
    SourceField(id="q-bio.QM", label="Quantitative Biology Methods"),
    SourceField(id="physics.med-ph", label="Medical Physics"),
    SourceField(id="econ.EM", label="Econometrics"),
    SourceField(id="math.OC", label="Optimization and Control"),
]

_FIELD_LABELS = {f.id: f.label for f in _FIELDS}


class ArxivProvider:
    id = "arxiv"
    label = "arXiv"

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
        terms = []
        if query:
            terms.append(f"all:{query}")
        if field:
            terms.append(f"cat:{field}")
        if days:
            now = datetime.now(timezone.utc)
            start = (now - timedelta(days=days)).strftime("%Y%m%d0000")
            end = now.strftime("%Y%m%d2359")
            terms.append(f"submittedDate:[{start} TO {end}]")
        if not terms:
            terms.append("cat:cs.*")

        # arXiv has no citation metric; relevance sort only makes sense with
        # a query, otherwise fall back to newest submissions.
        sort_by = "relevance" if (sort == "relevance" and query) else "submittedDate"

        params = {
            "search_query": " AND ".join(terms),
            "sortBy": sort_by,
            "sortOrder": "descending",
            "max_results": limit,
        }

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(_API_URL, params=params)
            response.raise_for_status()

        return self._parse_feed(response.text)

    def _parse_feed(self, feed_xml: str) -> List[SourcePaper]:
        root = ET.fromstring(feed_xml)
        papers = []
        for entry in root.findall("a:entry", _ATOM_NS):
            entry_id = entry.findtext("a:id", "", _ATOM_NS)
            # http://arxiv.org/abs/2606.12406v1 -> 2606.12406
            arxiv_id = entry_id.rsplit("/abs/", 1)[-1].split("v")[0]
            if not arxiv_id:
                continue

            title = " ".join((entry.findtext("a:title", "", _ATOM_NS) or "").split())
            abstract = " ".join((entry.findtext("a:summary", "", _ATOM_NS) or "").split())
            published = entry.findtext("a:published", "", _ATOM_NS)
            authors = [
                a.findtext("a:name", "", _ATOM_NS)
                for a in entry.findall("a:author", _ATOM_NS)
            ]
            categories = [
                c.get("term", "")
                for c in entry.findall("a:category", _ATOM_NS)
            ]
            field_labels = [
                _FIELD_LABELS.get(c, c) for c in categories if c
            ]

            papers.append(SourcePaper(
                id=f"arxiv_{arxiv_id}",
                source=self.id,
                source_record_id=arxiv_id,
                title=title,
                authors=[a for a in authors if a],
                abstract=abstract or None,
                published_date=published[:10] if published else None,
                landing_url=f"https://arxiv.org/abs/{arxiv_id}",
                pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                is_open_access=True,
                fields_of_study=field_labels[:4],
                external_ids={"arxiv": arxiv_id},
            ))
        return papers
