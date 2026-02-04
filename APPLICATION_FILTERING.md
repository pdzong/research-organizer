# Application Paper Filtering - Technical Documentation

## Overview

When saving an application, the system now automatically filters related papers to ensure only **relevant** papers are included. This uses a combination of arXiv search and OpenAI's GPT-5-mini model to validate relevance.

## How It Works

### 1. Paper Collection Phase

When you click "Add to List" on an application:

```
Application Domain (e.g., "Enterprise tool agents")
          ↓
    arXiv Search (10 papers)
          ↓
    Extract arXiv IDs
          ↓
    Merge with Related Papers from UI
          ↓
    Create Unique Paper Set
```

### 2. Filtering Phase

For each paper in the set:

```
Get/Fetch Paper Metadata
          ↓
Extract Title + Abstract
          ↓
Check Relevance with GPT-5-mini
          ↓
    Is Relevant?
    ├─ YES → Add to filtered list ✅
    └─ NO  → Skip ❌
```

### 3. Save Phase

```
Filtered Papers List
          ↓
Save to applications.json
```

## Implementation Details

### Key Components

#### 1. `filter_papers_by_relevance()` Function

Located in: `backend/routers/papers.py`

**Purpose**: Orchestrates the filtering process

**Steps**:
1. Creates `ApplicationIdea` object from application data
2. Searches arXiv using the application domain
3. Extracts arXiv IDs from search results
4. Merges with related papers from the UI
5. For each unique paper:
   - Fetches metadata (or loads from cache)
   - Calls `is_paper_relevant()` to check relevance
   - Includes only papers where `decision = True`

**Parameters**:
- `application`: Dict with `domain` and `specific_utility`
- `related_papers`: Initial list from UI
- `model_id`: OpenAI model (default: `"gpt-5-mini"`)

**Returns**: List of filtered papers with `title`, `authors`, `arxiv_id`

#### 2. `is_paper_relevant()` Function

Located in: `backend/services/openai_service.py`

**Purpose**: Determines if a paper is relevant to the application

**How it works**:
- Uses OpenAI's structured outputs API
- Analyzes paper title and abstract against application context
- Returns boolean decision + reasoning

**Criteria for Relevance**:
1. Does the paper propose a method/model/dataset useful for the target application?
2. Is it technically aligned with the application domain?

**Model**: `gpt-5-mini` (new OpenAI model)

**Returns**:
```json
{
  "success": true,
  "decision": true/false,
  "reason": "One-sentence justification"
}
```

#### 3. `arxiv_search_tool()` Function

Located in: `backend/services/some_extensions/research_tools.py`

**Purpose**: Searches arXiv API for papers

**Parameters**:
- `query`: Search keywords (application domain)
- `max_results`: Number of results (default: 10)

**Returns**: List of paper metadata including title, authors, abstract, URL

### Data Flow

```python
# 1. User clicks "Add to List" on application
POST /api/applications/add
{
  "application": {
    "domain": "Enterprise tool agents",
    "specific_utility": "Improves multi-turn workflow..."
  },
  "current_paper": {...},
  "related_papers": [10 papers from UI]
}

# 2. Backend processes
async def add_application(request):
    # Filter papers
    filtered_papers = await filter_papers_by_relevance(
        application=request.application,
        related_papers=request.related_papers,
        model_id="gpt-5-mini"
    )
    
    # Save with filtered papers
    cache_service.save_application(
        application=request.application,
        current_paper=request.current_paper,
        related_papers=filtered_papers  # Only relevant papers!
    )

# 3. Result
applications.json now contains only relevant papers
```

## Console Output

When saving an application, you'll see detailed logging:

```
============================================================
🎯 Adding application: Enterprise tool agents
============================================================
🔍 Searching arXiv for: Enterprise tool agents
📊 Found 15 unique papers to check
📥 Fetching metadata for 2512.13278
🤖 Checking relevance: AutoTool: Dynamic Tool Selection and Integration...
✅ Relevant: AutoTool: Dynamic Tool Selection and Integration...
🤖 Checking relevance: Some Unrelated Paper...
❌ Not relevant: Some Unrelated Paper... - Paper focuses on NLP, not tool agents
...
✨ Filtered to 8 relevant papers
============================================================
✅ Application saved with 8 relevant papers
============================================================
```

## Performance Considerations

### Caching Strategy

**Metadata Caching**:
- First check: `cache_service.load_metadata(arxiv_id)`
- If not cached: Fetch from Semantic Scholar and save
- Subsequent requests: Load from cache (instant)

**Benefits**:
- Reduces API calls to Semantic Scholar
- Speeds up filtering for frequently referenced papers
- Persistent across application saves

### API Costs

**Per Application Save**:
- ArXiv search: Free, 1 request
- Semantic Scholar metadata: Free, ~5-15 requests (only for uncached papers)
- OpenAI relevance checks: ~10-20 requests using `gpt-5-mini` (cheap model)

**Example Cost Calculation**:
- 15 papers to check
- 15 × OpenAI API calls with gpt-5-mini
- Input: ~500 tokens per call (application context + title + abstract)
- Output: ~50 tokens per call (decision + reasoning)
- Total: ~8,250 tokens per application save

### Processing Time

**Typical Timeline**:
- ArXiv search: ~1-2 seconds
- Metadata fetching: ~0.5-1 second per uncached paper
- Relevance checking: ~0.5-1 second per paper
- **Total**: ~10-30 seconds for 15 papers (first time)
- **Total**: ~5-15 seconds (with cached metadata)

## Configuration

### Model Selection

Current model: `gpt-5-mini`

To change the model, update in `papers.py`:

```python
filtered_papers = await filter_papers_by_relevance(
    application=request.application,
    related_papers=[p.dict() for p in request.related_papers],
    model_id="gpt-5-mini"  # Change here
)
```

Available models:
- `gpt-5-mini` - Fast, cheap, good for filtering (recommended)
- `gpt-5-nano` - Fastest, cheapest (original default in deep_analysis.py)
- `gpt-5.2` - Most capable, expensive

### Search Parameters

To adjust arXiv search results count:

In `filter_papers_by_relevance()`:
```python
search_results = arxiv_search_tool(app_idea.domain, max_results=10)  # Change here
```

## Error Handling

### Graceful Degradation

**Missing Metadata**:
```python
if not metadata:
    print(f"❌ Failed to fetch metadata for {arxiv_id}")
    continue  # Skip this paper
```

**Missing Title/Abstract**:
```python
if not title or not abstract:
    print(f"⚠️ Missing title or abstract for {arxiv_id}")
    continue  # Skip this paper
```

**API Errors**:
```python
try:
    relevance = await is_paper_relevant(...)
except Exception as e:
    print(f"❌ Error processing {arxiv_id}: {e}")
    continue  # Skip this paper
```

### Failure Modes

1. **arXiv Search Fails**: Returns papers from UI only
2. **Metadata Fetch Fails**: Skips that specific paper
3. **Relevance Check Fails**: Defaults to `decision=False` (skip)
4. **All Checks Fail**: Saves with empty related_papers list

## Comparison with deep_analysis.py

### Similarities
- Both use `arxiv_search_tool`
- Both use `is_paper_relevant` for filtering
- Both cache metadata
- Both extract arXiv IDs from search results

### Differences

| Feature | deep_analysis.py | papers.py (applications) |
|---------|------------------|--------------------------|
| **Trigger** | Manual script execution | Automatic on "Add to List" |
| **Output** | CSV file with relevance data | Filtered papers in JSON |
| **Model** | `gpt-5-nano` | `gpt-5-mini` |
| **Logging** | CSV with all decisions | Console output only |
| **Purpose** | Research/analysis | Production filtering |

## Benefits

### User Experience
✅ **Only Relevant Papers**: No clutter from unrelated papers
✅ **Automatic**: No manual filtering needed
✅ **Fast**: Leverages caching for speed
✅ **Transparent**: Console logs show filtering process

### Data Quality
✅ **Higher Precision**: AI-validated relevance
✅ **Domain Expansion**: arXiv search finds related papers
✅ **Deduplication**: Unique arXiv IDs only
✅ **Consistent**: Same filtering criteria for all applications

## Future Enhancements

### Potential Improvements

1. **Configurable Filtering**:
   - User-adjustable relevance threshold
   - Optional strict/lenient modes

2. **Batch Optimization**:
   - Parallel relevance checks for speed
   - Batch OpenAI API requests

3. **Feedback Loop**:
   - User can mark papers as relevant/irrelevant
   - Train custom relevance model

4. **Advanced Filtering**:
   - Citation count threshold
   - Publication date range
   - Venue/journal filtering

5. **UI Feedback**:
   - Progress bar during filtering
   - Show filtered out papers (with reasons)
   - Manual override to include/exclude papers

## Troubleshooting

### Issue: Too Few Papers After Filtering

**Possible Causes**:
- Application domain too specific
- Model being too strict
- Limited arXiv search results

**Solutions**:
1. Broaden application domain description
2. Switch to `gpt-5-nano` (more lenient)
3. Increase `max_results` in arXiv search

### Issue: Too Many Irrelevant Papers

**Possible Causes**:
- Application description too broad
- Model being too lenient

**Solutions**:
1. Make application domain more specific
2. Switch to `gpt-5.2` (more strict)
3. Add additional filtering criteria

### Issue: Slow Performance

**Possible Causes**:
- Many uncached papers
- Network latency
- OpenAI API slowness

**Solutions**:
1. Pre-cache common papers
2. Implement parallel processing
3. Use faster model (`gpt-5-mini`)

## Testing

### Manual Testing

1. **Save an application** with a specific domain
2. **Check console output** for filtering details
3. **Verify filtered papers** in applications.json
4. **Confirm relevance** by reviewing included papers

### Example Test Case

```python
Application: "Enterprise tool agents / API orchestration"

Expected Relevant Papers:
✅ Papers about tool-using agents
✅ Papers about API integration
✅ Papers about multi-turn workflows

Expected Filtered Out:
❌ Pure NLP papers without tool use
❌ Computer vision papers
❌ Papers about unrelated domains
```

## Code References

### Main Files
- `backend/routers/papers.py` - Filtering implementation
- `backend/services/openai_service.py` - Relevance checking
- `backend/services/some_extensions/research_tools.py` - arXiv search
- `backend/services/cache_service.py` - Metadata caching
- `backend/services/semantic_scholar.py` - Metadata fetching

### Key Functions
- `filter_papers_by_relevance()` - Main filtering orchestrator
- `is_paper_relevant()` - AI relevance checker
- `arxiv_search_tool()` - Paper search
- `extract_arxiv_id_from_url()` - URL parsing
