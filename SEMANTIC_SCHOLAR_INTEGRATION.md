# Semantic Scholar Metadata Integration

## Overview

Integrated Semantic Scholar API to fetch rich metadata about research papers, including citations, authors, publication venues, fields of study, and more. The metadata is displayed in a beautiful, collapsible accordion UI.

## Changes Made

### Backend

#### 1. **`backend/requirements.txt`** - Added Dependency
```txt
semanticscholar==0.8.4
```

#### 2. **`backend/services/semantic_scholar.py`** - New Service (Created)

Fetches paper metadata from Semantic Scholar using ArXiv ID.

**Key Function**: `get_paper_metadata(arxiv_id: str)`

**Returns**:
- `paperId`: Semantic Scholar paper ID
- `title`: Paper title
- `abstract`: Full abstract
- `tldr`: Short TL;DR summary
- `year`: Publication year
- `publicationDate`: Full publication date
- `citationCount`: Total citations
- `referenceCount`: Number of references
- `influentialCitationCount`: Highly influential citations
- `isOpenAccess`: Whether paper is open access
- `fieldsOfStudy`: Fields of study (e.g., "Computer Science")
- `s2FieldsOfStudy`: Semantic Scholar's categorization
- `publicationTypes`: Type of publication
- `publicationVenue`: Conference/journal details
- `journal`: Journal information (name, volume, pages)
- `authors`: List of authors with IDs and URLs
- `venue`: Venue name
- `openAccessPdf`: PDF URL if available
- `externalIds`: DOI, ArXiv, PubMed IDs, etc.
- `url`: Semantic Scholar URL
- `corpusId`: Corpus ID

#### 3. **`backend/routers/papers.py`** - New Endpoint

**Added**:
```python
GET /api/papers/{arxiv_id}/metadata

Response: MetadataResponse {
  success: bool,
  metadata: PaperMetadata | null,
  error: string | null
}
```

### Frontend

#### 1. **`frontend/src/services/api.ts`** - New Types & Function

**Added Types**:
```typescript
interface PaperMetadata { ... }
interface MetadataResponse { ... }
```

**Added Function**:
```typescript
getPaperMetadata(arxivId: string): Promise<MetadataResponse>
```

#### 2. **`frontend/src/App.tsx`** - State & Logic

**Added State**:
```typescript
const [metadata, setMetadata] = useState<PaperMetadata | null>(null);
const [loadingMetadata, setLoadingMetadata] = useState(false);
```

**Modified**: `handleSelectPaper()` - Now fetches metadata automatically when a paper is selected

#### 3. **`frontend/src/components/PaperDetail.tsx`** - Rich Metadata Display

**Added Props**:
- `metadata: PaperMetadata | null`
- `loadingMetadata: boolean`

**New UI Section**: Beautiful accordion with 6 collapsible sections:

1. **Overview & Citations**
   - TL;DR (if available)
   - Abstract
   - Citation count (with badge)
   - Influential citation count
   - Reference count

2. **Publication Information**
   - Year
   - Publication date
   - Venue
   - Publication venue (with type badge)
   - Journal (with volume and pages)
   - Open Access badge

3. **Authors** (count shown)
   - List of all authors
   - Clickable links to author profiles
   - Author IDs

4. **Fields of Study**
   - General fields (as badges)
   - Semantic Scholar specific fields (indigo badges)

5. **External Links**
   - Semantic Scholar page
   - Open Access PDF (if available)
   - External IDs (DOI, PubMed, etc.)

## Features

### 🎨 UI Design

- **Collapsible Accordion**: Each section can be expanded/collapsed
- **Icons**: Each section has a relevant icon
- **Badges**: Color-coded badges for different information types:
  - Blue: Citations
  - Green: Influential citations
  - Gray: References
  - Teal: Open Access
  - Indigo: S2 Fields
  - Outline: External IDs
- **Clickable Links**: Authors and external links are clickable
- **Loading State**: Shows loader while fetching

### 📊 Information Displayed

| Section | Information |
|---------|-------------|
| Overview | TL;DR, Abstract, Citation metrics |
| Publication | Year, Date, Venue, Journal, Open Access status |
| Authors | Full author list with profile links |
| Fields | Academic fields and categories |
| Links | Semantic Scholar, PDF, External IDs |

## Usage Flow

1. **User selects a paper** from the list
2. **Metadata is automatically fetched** from Semantic Scholar
3. **Loading indicator appears** during fetch
4. **Metadata displays** in expandable accordion
5. **User can expand/collapse** sections as needed

## Example Output

For "Attention Is All You Need" (ArXiv: 1706.03762):

```json
{
  "title": "Attention Is All You Need",
  "year": 2017,
  "citationCount": 120000+,
  "influentialCitationCount": 15000+,
  "fieldsOfStudy": ["Computer Science"],
  "venue": "NIPS",
  "isOpenAccess": true,
  "tldr": "The Transformer architecture...",
  "authors": [
    {"name": "Ashish Vaswani", "url": "..."},
    // ... 7 more authors
  ]
}
```

## Error Handling

- **Paper not found**: Returns error message
- **API failure**: Gracefully handles and shows error
- **Missing fields**: Null-safe, only shows available data
- **Network timeout**: Handled by async executor

## Performance

- **Automatic fetch**: Loads when paper is selected
- **Async loading**: Doesn't block UI
- **Cached in state**: No refetch on re-render
- **Fast API**: Semantic Scholar API is responsive

## Testing

### Backend Test
```bash
curl http://localhost:8000/api/papers/1706.03762/metadata
```

### Frontend Test
1. Select any paper
2. Wait for metadata to load
3. Expand accordion sections
4. Verify all data displays correctly

## Benefits

### Before
- ❌ Only basic paper info (title, authors, ArXiv ID)
- ❌ No citation metrics
- ❌ No publication venue
- ❌ No fields of study
- ❌ No author profiles

### After
- ✅ Rich metadata from Semantic Scholar
- ✅ Citation and influence metrics
- ✅ Publication venue and journal
- ✅ Academic fields categorization
- ✅ Clickable author profiles
- ✅ Open Access status
- ✅ External IDs (DOI, PubMed, etc.)
- ✅ TL;DR summary
- ✅ Beautiful collapsible UI

## Files Changed

**Backend:**
- `backend/requirements.txt` - Added semanticscholar
- `backend/services/semantic_scholar.py` - Created
- `backend/routers/papers.py` - Added endpoint

**Frontend:**
- `frontend/src/services/api.ts` - Added types & function
- `frontend/src/App.tsx` - Added state & fetch logic
- `frontend/src/components/PaperDetail.tsx` - Added metadata display

## API Documentation

### Endpoint
```
GET /api/papers/{arxiv_id}/metadata
```

### Parameters
- `arxiv_id` (path): ArXiv ID (e.g., "1706.03762")

### Response
```typescript
{
  success: boolean,
  metadata: {
    paperId: string | null,
    title: string | null,
    abstract: string | null,
    tldr: string | null,
    year: number | null,
    publicationDate: string | null,
    citationCount: number,
    referenceCount: number,
    influentialCitationCount: number,
    isOpenAccess: boolean,
    fieldsOfStudy: string[],
    s2FieldsOfStudy: Array<{category: string, source: string}>,
    publicationVenue: {...},
    journal: {...},
    authors: Array<{name: string, url: string}>,
    // ... more fields
  } | null,
  error: string | null
}
```

## Installation

```bash
# Backend
cd backend
pip install semanticscholar==0.8.4

# Restart backend
uvicorn main:app --reload
```

## Future Enhancements

Potential additions:
- [ ] Show top cited papers (references)
- [ ] Show papers that cite this paper
- [ ] Author collaboration network
- [ ] Publication venue ranking
- [ ] Citation trend over time
- [ ] Related papers recommendations
- [ ] Export citation in various formats

## Notes

- Semantic Scholar API is free but may have rate limits
- Not all papers have all fields (null-safe)
- Some papers may not be in Semantic Scholar database
- ArXiv ID must be valid format
- Async execution prevents blocking

## Conclusion

The Semantic Scholar integration provides a wealth of information about research papers in a user-friendly, collapsible interface. This greatly enhances the research experience by providing citation metrics, author information, and publication details at a glance.

Perfect for researchers who want quick insights into a paper's impact and context! 🎓✨
