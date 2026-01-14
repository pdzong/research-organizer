# Caching System Documentation

## Overview

The research agent now includes a comprehensive caching system that stores all loaded data (metadata, parsed PDFs, and AI analysis) locally to avoid redundant API calls and improve performance.

## How It Works

### Backend Cache Structure

All cached data is stored in `backend/data/cache/` with the following structure:

```
backend/data/cache/
├── {arxiv_id}/
│   ├── metadata.json      # Semantic Scholar metadata
│   ├── markdown.md         # Parsed PDF content
│   └── analysis.json       # OpenAI analysis results
```

### papers.json Enhancement

The `backend/data/papers.json` file now includes cache references:

```json
{
  "id": "1706.03762",
  "title": "Attention Is All You Need",
  "authors": [...],
  "arxiv_url": "...",
  "arxiv_id": "1706.03762",
  "cached": {
    "metadata": "cache/1706.03762/metadata.json",
    "markdown": "cache/1706.03762/markdown.md",
    "analysis": "cache/1706.03762/analysis.json",
    "lastUpdated": {
      "metadata": "2026-01-14T12:00:00",
      "markdown": "2026-01-14T12:00:00",
      "analysis": "2026-01-14T12:00:00"
    }
  }
}
```

## Features

### 1. Automatic Caching

When you:
- **Load paper content**: The parsed markdown is automatically saved to cache
- **Analyze a paper**: The AI analysis is saved to cache
- **Fetch metadata**: The Semantic Scholar data is saved to cache

### 2. Auto-Loading from Cache

When you select a paper:
- If cached data exists, it's **automatically loaded** without making new API calls
- This significantly speeds up loading previously viewed papers
- No manual intervention needed

### 3. Force Reload/Regenerate

Each data section has a reload button:
- **Reload Paper Content**: Re-downloads and re-parses the PDF from ArXiv
- **Regenerate Analysis**: Re-analyzes the paper with OpenAI (useful if you update the prompt)
- **Reload Metadata**: Re-fetches data from Semantic Scholar

### 4. Visual Indicators

Buttons show different states:
- "Load Paper Content" → Fetches from ArXiv
- "Load Paper Content (Cached)" → Will load from cache
- "Reload Paper Content" → Forces re-download (shown after content is loaded)
- "Analyze Paper" → Generates new analysis
- "Load Analysis (Cached)" → Will load from cache
- "Regenerate Analysis" → Forces new AI analysis

## API Endpoints

### Get Cache Status
```
GET /api/papers/{arxiv_id}/cache-status
```
Returns which cache files exist for a paper:
```json
{
  "metadata": true,
  "markdown": true,
  "analysis": false
}
```

### Parse with Optional Force Reload
```
GET /api/papers/{arxiv_id}/parse?force_reload=true
```
- `force_reload=false` (default): Uses cache if available
- `force_reload=true`: Bypasses cache and re-downloads

### Analyze with Optional Force Reload
```
GET /api/papers/{arxiv_id}/analyze?force_reload=true
```
- `force_reload=false` (default): Uses cache if available
- `force_reload=true`: Regenerates analysis

### Metadata with Optional Force Reload
```
GET /api/papers/{arxiv_id}/metadata?force_reload=true
```
- `force_reload=false` (default): Uses cache if available
- `force_reload=true`: Re-fetches from Semantic Scholar

## Cache Management

### Backend Service (`backend/services/cache_service.py`)

Provides utility functions:

```python
# Save operations
save_metadata(arxiv_id, metadata)
save_markdown(arxiv_id, markdown)
save_analysis(arxiv_id, analysis)

# Load operations
load_metadata(arxiv_id)
load_markdown(arxiv_id)
load_analysis(arxiv_id)

# Status check
get_cache_status(arxiv_id)

# Clear cache
clear_cache(arxiv_id, cache_type="metadata")  # Clear specific type
clear_cache(arxiv_id)  # Clear all cache for paper
```

### Manual Cache Management

You can manually manage cache by:
1. **View cache**: Check `backend/data/cache/{arxiv_id}/` directory
2. **Clear cache**: Delete specific files or entire paper directory
3. **Backup cache**: Copy the entire `cache/` directory

## Benefits

1. **Faster Loading**: Cached papers load instantly
2. **Reduced API Costs**: Fewer calls to OpenAI and Semantic Scholar
3. **Offline Viewing**: View previously loaded papers without internet
4. **Reproducibility**: Analysis results are preserved
5. **Flexibility**: Force reload when needed (e.g., after updating prompts)

## Best Practices

1. **Let auto-loading work**: The system automatically loads cached data when available
2. **Use reload sparingly**: Only regenerate when you need fresh data or updated analysis
3. **Regular backups**: Back up your `backend/data/` directory to preserve your cache
4. **Monitor disk space**: Large PDFs can accumulate; clear cache for papers you no longer need

## Cost Savings

### Example: Viewing a Previously Analyzed Paper

**Without caching:**
- ArXiv PDF download: ~2-5 seconds
- PDF parsing: ~1-3 seconds
- Semantic Scholar API: ~1-2 seconds
- OpenAI API: ~5-15 seconds + token costs (~$0.01-0.05 per paper)

**With caching:**
- Load all data: < 1 second
- API costs: $0.00

For a frequently referenced paper viewed 10 times, you save:
- **Time**: ~2 minutes
- **Money**: $0.10-0.50 in API costs
