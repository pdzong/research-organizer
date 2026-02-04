# Testing Application Filtering - Quick Guide

## What Was Implemented

When you click **"Add to List"** on an application, the system now:

1. ✅ Searches **arXiv** for related papers (10 results)
2. ✅ Merges with papers from "Recommended Related Papers"
3. ✅ Filters using **GPT-5-mini** AI model
4. ✅ Only saves **relevant** papers

## How to Test

### Prerequisites

Make sure the backend server is running:

```bash
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

And the frontend:

```bash
cd web_ui
npm run dev
```

### Test Procedure

1. **Open the app**: http://localhost:5173/

2. **Navigate to Papers view**

3. **Select a paper** (e.g., "ASTRA: Automated Synthesis...")

4. **Load Paper Content** and **Analyze Paper**

5. **Scroll to "Real-World Applications"**

6. **Click "Add to List"** on any application

7. **Watch the backend console** - you'll see:
   ```
   ============================================================
   🎯 Adding application: Enterprise tool agents
   ============================================================
   🔍 Searching arXiv for: Enterprise tool agents
   📊 Found 15 unique papers to check
   🤖 Checking relevance: AutoTool: Dynamic Tool Selection...
   ✅ Relevant: AutoTool: Dynamic Tool Selection...
   🤖 Checking relevance: Some Unrelated Paper...
   ❌ Not relevant: Some Unrelated Paper...
   ...
   ✨ Filtered to 8 relevant papers
   ============================================================
   ✅ Application saved with 8 relevant papers
   ============================================================
   ```

8. **Check the frontend notification**:
   - Should say: "Application '...' saved with X relevant papers"

9. **Switch to Applications view** (click Applications tab)

10. **Click the application** to view details

11. **Verify**: Only relevant papers are shown in "Related Papers" section

### What to Look For

#### ✅ Success Indicators

- Console shows filtering process
- Number of papers reduced from ~10-15 to smaller number
- Success notification shows filtered count
- Applications view shows filtered papers
- Each paper has title, authors, and arXiv ID

#### ❌ Issues to Watch For

- No papers after filtering (domain too specific)
- Too many papers (filtering not working)
- Error messages in console
- Missing metadata for papers
- Slow performance (>30 seconds)

## Example Test Cases

### Test Case 1: Broad Domain

**Application**: "Machine Learning"
- **Expected**: Many papers pass filter (10-15)
- **Reason**: Very broad domain

### Test Case 2: Specific Domain

**Application**: "Enterprise tool agents / API orchestration"
- **Expected**: Some papers filtered out (5-10 remain)
- **Reason**: Specific domain, only tool-agent papers relevant

### Test Case 3: Niche Domain

**Application**: "Quantum computing for protein folding"
- **Expected**: Few papers remain (1-3)
- **Reason**: Very specific, hard to find matches

## Verification Checklist

- [ ] arXiv search executes (see console log)
- [ ] Papers are deduplicated (unique arXiv IDs)
- [ ] Metadata fetching works (or loads from cache)
- [ ] GPT-5-mini relevance checks run (see console)
- [ ] Papers are filtered (count reduced)
- [ ] Success message shows filtered count
- [ ] applications.json contains filtered papers
- [ ] Applications view displays filtered papers
- [ ] Each paper has complete metadata

## Console Output Reference

### Normal Flow

```
🎯 Adding application: [Domain Name]
🔍 Searching arXiv for: [Domain Name]
📊 Found X unique papers to check
📥 Fetching metadata for [arxiv_id]  (if not cached)
🤖 Checking relevance: [Paper Title]...
✅ Relevant: [Paper Title]...
✨ Filtered to X relevant papers
✅ Application saved with X relevant papers
```

### With Errors

```
❌ Failed to fetch metadata for [arxiv_id]
⚠️ Missing title or abstract for [arxiv_id]
❌ Not relevant: [Paper Title]... - [Reason]
❌ Error processing [arxiv_id]: [Error message]
```

## Performance Benchmarks

### First Save (No Cache)
- **Time**: 15-30 seconds
- **Reason**: Fetching metadata + AI checks

### Subsequent Saves (With Cache)
- **Time**: 5-15 seconds
- **Reason**: Cached metadata, only AI checks

### API Calls
- **arXiv**: 1 search request
- **Semantic Scholar**: 5-15 metadata requests (only uncached)
- **OpenAI**: 10-20 relevance checks

## Data Verification

### Check applications.json

Location: `backend/data/cache/applications.json`

```json
{
  "id": "2026-02-04T...",
  "application": {
    "domain": "Enterprise tool agents",
    "specific_utility": "..."
  },
  "current_paper": {...},
  "related_papers": [
    {
      "title": "Relevant Paper 1",
      "authors": ["Author A", "Author B"],
      "arxiv_id": "1234.56789"
    }
    // Only relevant papers here!
  ],
  "added_at": "2026-02-04T..."
}
```

### Verify Filtering Quality

Manually check if the saved papers are actually relevant:

1. Read the application domain and utility
2. Look at each related paper title
3. Confirm they relate to the application
4. Check if irrelevant papers were filtered out

## Troubleshooting

### Issue: No papers saved

**Check**:
- Console for errors
- Application domain (might be too specific)
- arXiv search results (might be empty)

**Fix**:
- Use broader domain description
- Check internet connection
- Verify OPENAI_API_KEY is set

### Issue: All papers filtered out

**Check**:
- Application description clarity
- Model strictness (gpt-5-mini)

**Fix**:
- Make domain more specific to the papers
- Switch model to gpt-5-nano (more lenient)
- Check console for rejection reasons

### Issue: Slow performance

**Check**:
- Number of papers to check
- Network latency
- API rate limits

**Fix**:
- Reduce max_results in arXiv search
- Use cached metadata when possible
- Check OpenAI API status

## Advanced Testing

### Test Different Models

Edit `papers.py` line ~380:

```python
filtered_papers = await filter_papers_by_relevance(
    application=request.application,
    related_papers=[p.dict() for p in request.related_papers],
    model_id="gpt-5-mini"  # Try: gpt-5-nano, gpt-5.2
)
```

### Test Different Search Limits

Edit `papers.py` in `filter_papers_by_relevance()`:

```python
search_results = arxiv_search_tool(app_idea.domain, max_results=10)  # Try: 5, 20
```

### Monitor API Usage

Check OpenAI dashboard:
- Track token usage
- Monitor costs
- Check rate limits

## Success Criteria

✅ **Filtering works**: Papers are reduced from initial set
✅ **Relevance accurate**: Saved papers are actually relevant
✅ **Performance acceptable**: <30 seconds per save
✅ **UI updates**: Applications view shows filtered results
✅ **No errors**: Console shows clean execution
✅ **Data persists**: applications.json has correct data

## Next Steps

After successful testing:

1. **Save multiple applications** to build a library
2. **Compare filtering quality** across different domains
3. **Monitor performance** over time
4. **Adjust model/parameters** if needed
5. **Provide feedback** on filtering accuracy
