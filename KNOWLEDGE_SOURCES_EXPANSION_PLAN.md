# Knowledge Sources Expansion Plan

Date: 2026-05-28

## Goal

Expand the Research Paper Analyzer from an ArXiv-centered ingestion pipeline into a broader open scientific knowledge discovery system. The target is a source-agnostic pipeline that can discover recent scientific articles and preprints from many fields, resolve legally available open full text or PDFs, parse them, and reuse the existing analysis and application-planning flow.

## Current Project Evaluation

The project already has a useful parse -> section extraction -> analysis -> application discovery pipeline, but most source assumptions are hard-coded around ArXiv identifiers.

Current source-related assumptions:

- `backend/services/huggingface.py` validates and adds only ArXiv URLs.
- `backend/services/pdf_parser.py` downloads PDFs by converting `https://arxiv.org/abs/{id}` into `https://arxiv.org/pdf/{id}.pdf`.
- `backend/services/semantic_scholar.py` enriches metadata by querying Semantic Scholar with `ARXIV:{id}`.
- `backend/services/auto_research.py` discovers papers by scraping Hugging Face Daily Papers and extracting ArXiv IDs.
- `web_ui/src/components/PaperList.tsx` exposes the add-paper input as "ArXiv URL".
- `backend/data/cache/{arxiv_id}/` uses the ArXiv ID as the cache key.

What is already reusable:

- PDF parsing from bytes with PyMuPDF and optional OCR.
- Markdown caching.
- Section extraction into `PaperSections`.
- LLM-based summarization, benchmark extraction, novelty analysis, application extraction, and solution planning.
- Semantic Scholar metadata display, especially citations, recommendations, fields of study, and open-access PDF information.
- Existing dependencies include `pyalex`, `semanticscholar`, `httpx`, and `beautifulsoup4`, which makes OpenAlex and Semantic Scholar integration straightforward.

## Recommended Source Strategy

Use a layered source strategy instead of treating every provider as a complete solution.

1. Discover broadly with OpenAlex.
2. Enrich and rank with Semantic Scholar.
3. Resolve open access locations with Unpaywall, CORE, OpenAlex `open_access`, and source-specific APIs.
4. Fetch content only from legal open-access URLs or provider-supported full-text endpoints.
5. Parse PDFs/XML/HTML into the same markdown pipeline the app already uses.

## Priority Source Matrix

| Priority | Source | Best Use | Coverage | Content Access | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | OpenAlex | Broad discovery and metadata graph | Very broad, cross-disciplinary | Metadata, OA flags, OA locations where available | Best default index for "recent across many fields". |
| 1 | CORE | Open access full text and metadata | Broad OA repositories and journals | Metadata plus full text when available | Best broad full-text complement to OpenAlex. |
| 1 | Unpaywall | DOI -> legal OA location | DOI-assigned literature | OA URL/PDF URL resolution | Use after Crossref/OpenAlex/Semantic Scholar returns a DOI. |
| 2 | Semantic Scholar | Enrichment, ranking, related papers | Broad, strong in CS/biomedicine | Metadata, abstracts, citations, openAccessPdf | Already integrated; expand beyond ArXiv IDs. |
| 2 | Crossref | DOI metadata and publisher metadata | Very broad DOI registry | Metadata, license and full-text links when deposited | Not a full-text source by itself. |
| 2 | Europe PMC / PMC | Biomedical and life sciences depth | PubMed, PMC, preprints, life sciences | Metadata, OA full-text XML, citations, references | Essential for biology, medicine, agriculture, health. |
| 3 | bioRxiv / medRxiv | Recent biology and medical preprints | Biology and medicine preprints | Metadata and preprint links | Excellent recency source. |
| 3 | DOAJ | Vetted open access journal articles | Cross-disciplinary OA journals | Article metadata and links | Strong quality filter for OA journals. |
| 4 | ChemRxiv | Chemistry preprints | Chemistry and adjacent fields | Metadata and associated files | Add once the source-adapter pattern exists. |
| 4 | EarthArXiv | Earth and planetary science preprints | Earth science, climate, geoscience | OAI-PMH metadata with PDF links | Uses standard harvesting. |
| 4 | RePEc | Economics and working papers | Economics and related social science | Metadata and links | Useful for economics coverage. |
| 4 | OSF Preprints | Multidisciplinary preprints | Broad, variable by preprint server | Metadata and files through OSF API | Good later-stage adapter. |

## Source Details And Official APIs

### OpenAlex

Use for broad discovery, topic filtering, institutional filtering, citation graph traversal, and recent OA work discovery.

Official docs:

- https://docs.openalex.org/api-entities/works
- https://developers.openalex.org/api-reference/introduction

Useful query patterns:

- Recent OA works:
  `https://api.openalex.org/works?filter=from_publication_date:2026-01-01,is_oa:true&sort=publication_date:desc`
- Topic search:
  `https://api.openalex.org/works?search=robotics&filter=is_oa:true&sort=publication_date:desc`
- High-signal recent papers:
  `filter=from_publication_date:2025-01-01,is_oa:true,cited_by_count:>10`

Implementation notes:

- The repo already depends on `pyalex`; prefer it unless a direct `httpx` call is simpler.
- Normalize OpenAlex IDs into `external_ids.openalex`.
- Use `primary_location`, `best_oa_location`, DOI, publication date, abstract inverted index, topics, concepts, and citation count.
- OpenAlex is a metadata/discovery source first; still resolve content via OA URLs, CORE, Unpaywall, or source-specific links.

### CORE

Use for open access full text from repositories and OA journals.

Official docs:

- https://core.ac.uk/services/api
- https://api.core.ac.uk/docs/v3

Implementation notes:

- Add a `CoreProvider` for search and a `CoreContentResolver` for full-text/PDF access.
- Prefer CORE when OpenAlex identifies a work as OA but does not provide a directly parseable PDF.
- Store `external_ids.core` when available.
- CORE may require an API key depending on usage level; keep `CORE_API_KEY` optional in `.env`.

### Unpaywall

Use to resolve a DOI into a legal open access location.

Official docs:

- https://unpaywall.org/products/api
- https://unpaywall.org/data-format

Useful query:

`https://api.unpaywall.org/v2/{doi}?email={email}`

Implementation notes:

- Requires an email parameter.
- Use `best_oa_location.url_for_pdf` first, then `best_oa_location.url`.
- Store `oa_status`, `license`, `host_type`, and `is_oa`.
- Use as a resolver, not as a discovery index.

### Semantic Scholar

Use for enrichment, citation graph, recommendations, TLDRs, and ranking.

Official docs:

- https://www.semanticscholar.org/product/api
- https://api.semanticscholar.org/api-docs/graph

Useful query patterns:

- Search:
  `https://api.semanticscholar.org/graph/v1/paper/search?query=agentic%20rag&fields=title,abstract,authors,year,publicationDate,externalIds,openAccessPdf,citationCount,fieldsOfStudy`
- DOI lookup:
  `https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}`
- ArXiv lookup:
  `https://api.semanticscholar.org/graph/v1/paper/ARXIV:{arxiv_id}`

Implementation notes:

- Refactor `get_paper_metadata(arxiv_id)` into a more generic `get_paper_metadata(identifier_type, identifier)`.
- Keep the existing UI metadata accordion, but allow non-ArXiv papers.
- Use `openAccessPdf.url` as one candidate content URL.

### Crossref

Use for DOI metadata, recency filters, publisher metadata, license metadata, and DOI search.

Official docs:

- https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/

Useful query patterns:

- Recent works:
  `https://api.crossref.org/works?filter=from-pub-date:2026-01-01,type:journal-article&sort=published&order=desc`
- Works with licenses:
  `https://api.crossref.org/works?filter=from-pub-date:2026-01-01,has-license:true`
- DOI lookup:
  `https://api.crossref.org/works/{doi}`

Implementation notes:

- Crossref gives metadata, not guaranteed full text.
- Use Crossref DOI records to feed Unpaywall and OpenAlex enrichment.
- Store `external_ids.doi`.

### Europe PMC / PubMed Central

Use for biomedical and life-science articles, preprints, citations, references, annotations, and OA full-text XML.

Official docs:

- https://europepmc.org/RestfulWebService
- https://pmc.ncbi.nlm.nih.gov/tools/developers/
- https://www.ncbi.nlm.nih.gov/home/develop/api/

Useful query patterns:

- Recent search:
  `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=machine%20learning%20sort_date:y&resultType=core&format=json`
- Article lookup:
  `https://www.ebi.ac.uk/europepmc/webservices/rest/article/{source}/{id}?resultType=core&format=json`
- OA full-text XML:
  `https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML`

Implementation notes:

- Add XML-to-markdown support for PMC/JATS XML.
- Store `external_ids.pmid` and `external_ids.pmcid`.
- Prefer XML when available because it preserves structure better than PDF extraction.

### bioRxiv / medRxiv

Use for very recent biology and medicine preprints.

Official docs:

- https://api.biorxiv.org/

Useful query patterns:

- Recent bioRxiv:
  `https://api.biorxiv.org/details/biorxiv/7d`
- Recent medRxiv:
  `https://api.biorxiv.org/details/medrxiv/7d`
- Date range:
  `https://api.biorxiv.org/details/biorxiv/2026-05-01/2026-05-28`

Implementation notes:

- Add `BiorxivProvider` and `MedrxivProvider`.
- Treat records as preprints and surface that status in the UI.
- Resolve DOI through Crossref/Unpaywall when needed.

### DOAJ

Use for open access journal metadata and as a quality/eligibility filter.

Official docs and data pages:

- https://doaj.org/
- https://doaj.org/docs/faq/
- https://doaj.org/docs/openurl/

Implementation notes:

- DOAJ is valuable as a curated OA journal/article source.
- Use article metadata links as candidates; still verify parseable full text.
- Store journal ISSN/eISSN and DOAJ journal/article identifiers when available.

### Specialized Later-Stage Sources

Add these after the provider interface is stable:

- ChemRxiv: chemistry preprints and associated files.
- EarthArXiv: OAI-PMH feed at `https://eartharxiv.org/api/oai/`.
- RePEc: economics working papers and articles via https://ideas.repec.org/api.html.
- OSF Preprints: official OSF API at https://developer.osf.io/.

## Proposed Data Model

Replace ArXiv-specific fields as the primary contract with a source-neutral shape. Keep `arxiv_id` as a backward-compatible optional field while migrating.

```json
{
  "id": "openalex:W1234567890",
  "source": "openalex",
  "source_record_id": "W1234567890",
  "title": "Paper title",
  "authors": ["Author One", "Author Two"],
  "abstract": "Abstract text when available",
  "published_date": "2026-05-28",
  "publication_year": 2026,
  "publication_type": "journal-article",
  "venue": "Journal or conference name",
  "is_preprint": false,
  "is_open_access": true,
  "license": "cc-by",
  "landing_url": "https://example.org/article",
  "pdf_url": "https://example.org/article.pdf",
  "fulltext_url": "https://example.org/fulltext.xml",
  "external_ids": {
    "doi": "10.xxxx/yyyy",
    "arxiv": "2601.12345",
    "openalex": "W1234567890",
    "semantic_scholar": "abc123",
    "pmid": "123456",
    "pmcid": "PMC123456"
  },
  "fields_of_study": ["Computer Science", "Biology"],
  "topics": ["machine learning", "robotics"],
  "citation_count": 42,
  "source_metadata": {}
}
```

Backward compatibility:

- Keep reading existing `arxiv_id` and `arxiv_url`.
- When an existing paper only has `arxiv_id`, derive:
  - `id = "arxiv:{arxiv_id}"`
  - `source = "arxiv"`
  - `external_ids.arxiv = arxiv_id`
  - `landing_url = arxiv_url`
  - `pdf_url = https://arxiv.org/pdf/{arxiv_id}.pdf`

## Cache Key Migration

Current cache keys are ArXiv IDs. Move toward stable source-neutral cache keys.

Recommended cache key format:

- `arxiv_1706.03762`
- `doi_10.1145_1234567`
- `openalex_W1234567890`
- `pmcid_PMC1234567`
- `s2_abcdef`

Implementation function:

```python
def paper_cache_key(paper: dict) -> str:
    external_ids = paper.get("external_ids") or {}
    if external_ids.get("doi"):
        return "doi_" + safe_id(external_ids["doi"])
    if external_ids.get("arxiv"):
        return "arxiv_" + safe_id(external_ids["arxiv"])
    if external_ids.get("pmcid"):
        return "pmcid_" + safe_id(external_ids["pmcid"])
    return safe_id(f"{paper['source']}:{paper['source_record_id']}")
```

## Proposed Backend Architecture

Create a new package:

```text
backend/services/sources/
  __init__.py
  models.py
  registry.py
  openalex.py
  core.py
  semantic_scholar_provider.py
  crossref.py
  unpaywall.py
  europe_pmc.py
  biorxiv.py
  arxiv.py
  content.py
```

### Common Provider Interface

```python
from typing import Protocol, List, Optional
from pydantic import BaseModel

class SourcePaper(BaseModel):
    id: str
    source: str
    source_record_id: str
    title: str
    authors: list[str] = []
    abstract: str | None = None
    published_date: str | None = None
    landing_url: str | None = None
    pdf_url: str | None = None
    fulltext_url: str | None = None
    is_open_access: bool | None = None
    license: str | None = None
    external_ids: dict[str, str] = {}
    source_metadata: dict = {}

class DiscoveryProvider(Protocol):
    id: str
    label: str

    async def search_recent(
        self,
        query: str | None = None,
        limit: int = 20,
        since: str | None = None,
    ) -> list[SourcePaper]:
        ...

    async def get(self, identifier: str) -> SourcePaper | None:
        ...
```

### Content Resolution Interface

```python
class ResolvedContent(BaseModel):
    url: str
    content_type: str
    license: str | None = None
    source: str

class ContentResolver(Protocol):
    async def resolve(self, paper: SourcePaper) -> list[ResolvedContent]:
        ...
```

Resolution order:

1. `paper.pdf_url`
2. `paper.fulltext_url`
3. Semantic Scholar `openAccessPdf.url`
4. OpenAlex best OA location
5. Unpaywall best OA location by DOI
6. CORE full text/PDF by DOI/title/provider ID
7. Europe PMC full-text XML by PMCID

Only fetch content if:

- It is explicitly open access.
- The provider API allows retrieval.
- License/rights metadata does not contradict reuse.
- Robots/API terms are respected.

## Proposed API Changes

### Add Source Listing

Existing endpoint:

`GET /api/auto-research/sources`

Expand to include:

```json
[
  {"id": "openalex", "label": "OpenAlex"},
  {"id": "core", "label": "CORE"},
  {"id": "semantic_scholar", "label": "Semantic Scholar"},
  {"id": "europe_pmc", "label": "Europe PMC"},
  {"id": "biorxiv", "label": "bioRxiv"},
  {"id": "medrxiv", "label": "medRxiv"},
  {"id": "arxiv", "label": "arXiv"},
  {"id": "huggingface", "label": "Hugging Face Daily Papers"}
]
```

### Add Search Endpoint

```text
GET /api/sources/search?source=openalex&query=robotics&limit=20&since=2026-01-01
```

Response:

```json
{
  "success": true,
  "papers": [],
  "source": "openalex"
}
```

### Replace ArXiv-Only Add Endpoint

Keep:

```text
POST /api/papers/add
```

But allow either:

```json
{"url": "https://arxiv.org/abs/1706.03762"}
```

or:

```json
{
  "source": "openalex",
  "source_record_id": "W1234567890"
}
```

or:

```json
{
  "doi": "10.xxxx/yyyy"
}
```

### Generalize Parse Endpoint

Current:

```text
GET /api/papers/{arxiv_id}/parse
```

Future:

```text
GET /api/papers/{paper_id}/parse
```

Where `paper_id` is the stored source-neutral `id`. The backend resolves the cached paper record, finds content URLs, downloads content, and parses PDF/XML/HTML.

## Proposed Frontend Changes

1. Rename "ArXiv URL" input to "Paper URL, DOI, or source ID".
2. Add source badges:
   - ArXiv
   - OpenAlex
   - Semantic Scholar
   - CORE
   - Europe PMC
   - bioRxiv
   - medRxiv
3. Show OA/license status on paper cards.
4. Add a source selector to auto-research.
5. Add a search/discovery view:
   - query
   - source
   - since date
   - open-access only toggle
   - add selected papers
6. In metadata accordion, replace "View on ArXiv" assumptions with generic "Source", "DOI", "Open Access PDF", and "Publisher/Repository".

## Implementation Phases

### Phase 1: Normalize Paper Records

Goal: support non-ArXiv records without changing the analysis pipeline.

Tasks:

- Add `SourcePaper` Pydantic model.
- Add `normalize_legacy_paper()` for current `papers.json`.
- Add `external_ids`, `source`, `source_record_id`, `landing_url`, `pdf_url`, `is_open_access`, and `license` to saved records.
- Add a source-neutral cache key helper.
- Keep all existing ArXiv behavior working.

Acceptance criteria:

- Existing papers still list, parse, analyze, and show metadata.
- Existing `arxiv_id` records are automatically normalized at read time.
- No cache files are deleted or moved during this phase.

### Phase 2: Generalize Content Fetching

Goal: parse any known open PDF URL, not only ArXiv PDFs.

Tasks:

- Rename `download_pdf(arxiv_url)` to `download_pdf_url(pdf_url)`.
- Keep `download_arxiv_pdf(arxiv_id)` as a helper.
- Add `download_and_parse_url(url, content_type="pdf")`.
- Add content validation:
  - check status code
  - check content type
  - reject HTML publisher landing pages unless an HTML parser is implemented
  - store final redirected URL

Acceptance criteria:

- ArXiv parsing still works.
- A direct OA PDF URL can be parsed if added manually.

### Phase 3: Add OpenAlex Discovery

Goal: broad recent discovery across fields.

Tasks:

- Implement `OpenAlexProvider.search_recent()`.
- Use `pyalex` or direct `httpx`.
- Normalize OpenAlex works into `SourcePaper`.
- Add `openalex` to auto-research sources.
- Add basic API tests or manual smoke commands.

Acceptance criteria:

- `GET /api/auto-research/sources` includes OpenAlex.
- Auto-research can discover recent OpenAlex OA papers and register them.
- Papers with direct OA PDFs can be parsed.

### Phase 4: Add OA Resolution

Goal: turn metadata-only records into parseable content.

Tasks:

- Implement `UnpaywallResolver`.
- Implement `SemanticScholarResolver`.
- Implement OpenAlex OA-location resolver.
- Implement resolver chain in `content.py`.
- Add `.env.example` entries:
  - `UNPAYWALL_EMAIL`
  - `SEMANTIC_SCHOLAR_API_KEY`
  - `CORE_API_KEY`

Acceptance criteria:

- A DOI-backed OpenAlex record can resolve to an OA PDF when available.
- Resolver results are cached in metadata.
- Papers without OA content fail gracefully with a clear message.

### Phase 5: Add CORE Full Text

Goal: improve broad full-text success rate.

Tasks:

- Implement `CoreProvider.search_recent()`.
- Implement `CoreResolver`.
- Add API-key handling.
- Prefer direct full text when API returns it; otherwise fetch PDF URL.

Acceptance criteria:

- CORE records can be discovered and added.
- CORE full text/PDF can feed the existing markdown analysis flow.

### Phase 6: Add Europe PMC And XML Parsing

Goal: strong biomedical/life-science ingestion.

Tasks:

- Implement `EuropePmcProvider`.
- Add JATS/XML-to-markdown conversion for OA full-text XML.
- Store PMID/PMCID.
- Use Europe PMC citations/references where available.

Acceptance criteria:

- Europe PMC source can discover recent life-science papers.
- OA full-text XML parses into clean markdown.
- XML path avoids unnecessary PDF/OCR when full text XML exists.

### Phase 7: Add Preprint Sources

Goal: improve recent scientific coverage.

Tasks:

- Add `bioRxivProvider`.
- Add `medRxivProvider`.
- Add optional `ChemRxivProvider`, `EarthArXivProvider`, `RepecProvider`, and `OsfPreprintsProvider`.
- Mark preprint status in the UI.

Acceptance criteria:

- Recent preprint discovery works by date range.
- Preprint records are visibly labeled as preprints.

## Suggested First Vertical Slice

The lowest-risk useful slice:

1. Add source-neutral fields while preserving ArXiv behavior.
2. Allow parsing from a direct `pdf_url`.
3. Implement OpenAlex discovery for recent OA works.
4. Resolve content from OpenAlex `best_oa_location`.
5. Keep Semantic Scholar enrichment as-is for ArXiv and add DOI-based enrichment later.

This gives broad discovery without immediately needing every resolver.

## Risks And Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Metadata-only records without full text | Analysis cannot run | Show "metadata only" status and resolve via Unpaywall/CORE/Europe PMC. |
| License ambiguity | Legal/compliance risk | Store license, OA status, provider, and only fetch open URLs. |
| Provider rate limits | Failed discovery or enrichment | Add per-provider rate limiting, caching, and polite user agents. |
| Duplicate papers across sources | Noisy library | Deduplicate by DOI, ArXiv ID, PMID/PMCID, Semantic Scholar ID, then fuzzy title/year. |
| PDF parsing quality varies | Lower analysis quality | Prefer XML/JATS/HTML full text when available; use OCR fallback only for PDFs. |
| Existing code assumes ArXiv IDs | Regression risk | Keep backward-compatible `arxiv_id` fields until all routes are migrated. |

## Deduplication Rules

Use this order:

1. DOI match.
2. ArXiv ID match.
3. PMCID match.
4. PMID match.
5. Semantic Scholar paper ID match.
6. OpenAlex ID match.
7. Normalized title + publication year + first author.

When duplicates are found, merge metadata rather than replacing the record. Keep a list of all source IDs.

## Environment Variables

Add optional environment variables:

```text
OPENALEX_EMAIL=
UNPAYWALL_EMAIL=
SEMANTIC_SCHOLAR_API_KEY=
CORE_API_KEY=
CONTACT_EMAIL=
```

Use `CONTACT_EMAIL` as a polite user-agent/contact fallback for APIs that request contact info.

## Manual Testing Plan

Because the repo currently has no full automated test suite, use these smoke tests first:

1. Existing ArXiv path:
   - Add `https://arxiv.org/abs/1706.03762`
   - Parse
   - Analyze
   - Load metadata

2. Direct PDF path:
   - Add a paper record with `pdf_url`
   - Parse
   - Confirm markdown cache is created under the new cache key

3. OpenAlex search:
   - Search recent OA papers for `robotics`
   - Add one result
   - Resolve content
   - Parse if OA PDF is available

4. DOI resolution:
   - Add a DOI
   - Resolve via Unpaywall
   - Parse if OA PDF is available

5. Europe PMC:
   - Search `machine learning sort_date:y`
   - Add an OA full-text article
   - Parse XML to markdown

## References

- OpenAlex Works API: https://docs.openalex.org/api-entities/works
- OpenAlex API reference: https://developers.openalex.org/api-reference/introduction
- CORE API: https://core.ac.uk/services/api
- CORE API docs: https://api.core.ac.uk/docs/v3
- Semantic Scholar API: https://www.semanticscholar.org/product/api
- Semantic Scholar Graph API docs: https://api.semanticscholar.org/api-docs/graph
- Crossref REST API: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- Crossref filters: https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/
- Unpaywall API: https://unpaywall.org/products/api
- Unpaywall data format: https://unpaywall.org/data-format
- Europe PMC REST API: https://europepmc.org/RestfulWebService
- PMC developer tools: https://pmc.ncbi.nlm.nih.gov/tools/developers/
- NCBI APIs: https://www.ncbi.nlm.nih.gov/home/develop/api/
- bioRxiv/medRxiv API: https://api.biorxiv.org/
- DOAJ: https://doaj.org/
- DOAJ metadata help: https://doaj.org/docs/faq/
- EarthArXiv OAI-PMH note: https://eartharxiv.github.io/
- RePEc API: https://ideas.repec.org/api.html
- OSF API: https://developer.osf.io/
