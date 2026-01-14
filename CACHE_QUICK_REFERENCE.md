# Cache System - Quick Reference

## What's New? 🎉

Your research agent now automatically saves all data locally to avoid redundant API calls!

## User Experience

### When You Select a Paper

✅ **Automatic Loading**
- If you've viewed a paper before, all cached data loads instantly
- No need to click "Load" buttons - it happens automatically!

### Button States

| Button Text | What It Means |
|------------|---------------|
| "Load Paper Content" | Will download from ArXiv |
| "Load Paper Content (Cached)" | Will load from local cache (fast!) |
| "Reload Paper Content" | Force re-download (shown after loaded) |
| "Analyze Paper" | Will generate new AI analysis |
| "Load Analysis (Cached)" | Will load from local cache |
| "Regenerate Analysis" | Force new AI analysis |
| "Reload" (metadata) | Refresh metadata from Semantic Scholar |

## When to Use Reload/Regenerate?

### Reload Paper Content
- PDF has been updated on ArXiv
- Parsing failed previously

### Regenerate Analysis
- **Most common**: You modified the OpenAI prompt in `openai_service.py`
- You want a fresh analysis with updated AI models
- Previous analysis had errors

### Reload Metadata
- Citation counts or other metrics have changed
- Paper details were updated

## Cache Location

All cache files are stored in:
```
backend/data/cache/{arxiv_id}/
├── metadata.json      (Semantic Scholar data)
├── markdown.md        (Parsed PDF)
└── analysis.json      (AI analysis)
```

## Benefits

💰 **Cost Savings**: No repeated OpenAI API calls  
⚡ **Speed**: Instant loading of previously viewed papers  
📴 **Offline**: View cached papers without internet  
🔒 **Reproducibility**: Analysis results are preserved  

## Testing the Feature

1. **Restart backend** (if not already)
2. Open a paper you haven't viewed yet
3. Load content, metadata, and analyze
4. Go back to the paper list
5. **Select the same paper again** → Everything loads instantly! 🚀
6. Notice the "Reload"/"Regenerate" buttons appear after loading

## Clearing Cache (Optional)

If you want to clear cache for a specific paper:
1. Navigate to `backend/data/cache/{arxiv_id}/`
2. Delete the specific file or entire folder
3. Next time you load, it will fetch fresh data

Or use the "Reload"/"Regenerate" buttons in the UI!
