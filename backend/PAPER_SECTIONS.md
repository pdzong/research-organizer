# Paper Sections Extraction & Caching

## Overview

The system now automatically extracts structured sections from parsed papers using GPT-5-nano, making analysis more efficient and higher quality.

## How It Works

### 1. **Paper Parsing Flow**
```
PDF → OCR/PyMuPDF → Raw Markdown → Extract Sections → Cache Both
```

When you load paper content (`/papers/{id}/parse`):
1. Downloads and parses PDF to markdown
2. **NEW:** Automatically calls `extract_paper_sections()`
3. Saves both raw markdown AND structured sections to cache

### 2. **Structured Sections (PaperSections)**

The `PaperSections` model organizes the paper into:
- **title**: Paper title
- **abstract_text**: Full abstract
- **introduction_text**: Introduction + Related Work
- **methodology_text**: Methods, Architecture, Approach
- **experiments_text**: Results, Tables, Experiments
- **conclusion_text**: Conclusion, Discussion, Limitations
- **github_url**: Code repository link (if found)

**Key Benefits:**
- Removes noise (References, Appendix)
- Focuses on relevant content
- Reduces token usage for analysis
- Improves analysis quality

### 3. **Analysis Flow**
```
Analyze Request → Load Sections → to_clean_markdown() → Summarize → Cache
```

When you request analysis (`/papers/{id}/analyze`):
1. Loads `PaperSections` from cache
2. Calls `sections.to_clean_markdown()` to generate clean content
3. Passes clean markdown to `summarize_paper()`
4. Caches the analysis result

## API Changes

### Parse Endpoint (Updated)
```
GET /api/papers/{paper_id}/parse?force_reload=false
```

**New Behavior:**
- After successful parsing, automatically extracts sections
- Saves `sections.json` to cache
- Logs: `🧹 Extracting paper sections...` → `✅ Saved paper sections`

### Analyze Endpoint (Updated)
```
GET /api/papers/{arxiv_id}/analyze?force_reload=false
```

**New Behavior:**
- First tries to load structured sections
- Uses `to_clean_markdown()` for clean content
- Falls back to raw markdown if sections not available
- Logs: `📚 Using structured sections` or `⚠️ Falling back to raw markdown`

### New Endpoint: Get Sections
```
GET /api/papers/{arxiv_id}/sections
```

**Response:**
```json
{
  "success": true,
  "sections": {
    "title": "Paper Title",
    "abstract_text": "...",
    "introduction_text": "...",
    "methodology_text": "...",
    "experiments_text": "...",
    "conclusion_text": "...",
    "github_url": "https://github.com/..."
  },
  "error": null
}
```

### Cache Status (Updated)
```
GET /api/papers/{arxiv_id}/cache-status
```

**Response:**
```json
{
  "metadata": true,
  "markdown": true,
  "sections": true,  // NEW!
  "analysis": true
}
```

## Cache Structure

```
backend/data/cache/{arxiv_id}/
  ├── markdown.md        # Raw parsed content
  ├── sections.json      # NEW: Structured sections
  ├── metadata.json      # Semantic Scholar data
  └── analysis.json      # Analysis results
```

## Benefits

### 1. **Better Analysis Quality**
- Clean, focused content without references/appendix
- Properly organized sections
- Preserved structure for LLM reasoning

### 2. **Token Efficiency**
- Removes noise and repetition
- Focuses on essential sections
- Reduces cost for analysis

### 3. **GitHub Discovery**
- Actively searches for code repositories
- Extracts and validates URLs
- Surfaces implementation details

### 4. **Graceful Degradation**
- Falls back to raw markdown if extraction fails
- Analysis continues even without sections
- No breaking changes

## Example Output

### sections.json:
```json
{
  "title": "Attention Is All You Need",
  "github_url": "https://github.com/tensorflow/tensor2tensor",
  "abstract_text": "The dominant sequence transduction models...",
  "introduction_text": "Recurrent neural networks...",
  "methodology_text": "The Transformer model architecture...",
  "experiments_text": "We evaluated on two machine translation tasks...",
  "conclusion_text": "In this work, we presented the Transformer..."
}
```

### Clean Markdown Generated:
```markdown
# Attention Is All You Need

## Abstract
The dominant sequence transduction models...

## Introduction & Context
Recurrent neural networks...

## Methodology
The Transformer model architecture...

## Experiments & Results
We evaluated on two machine translation tasks...

## Conclusion & Limitations
In this work, we presented the Transformer...

## Meta Info
GitHub: https://github.com/tensorflow/tensor2tensor
```

## Cost Optimization

### Section Extraction:
- Model: `gpt-5-nano` (cheapest, fastest)
- Task: Simple segmentation (no reasoning)
- Cost: ~$0.001 per paper

### Analysis:
- Model: `gpt-5.2` (balanced)
- Task: Deep reasoning on clean content
- Savings: 30-50% fewer tokens vs raw markdown

## Logs to Watch

When loading a paper:
```
📥 Downloading PDF from https://arxiv.org/abs/XXXX
🔍 OCR endpoint detected, using local OCR model...
✅ OCR parsing successful
Saved markdown to cache for XXXX
🧹 Extracting paper sections for XXXX...
✅ Saved paper sections to cache for XXXX
```

When analyzing:
```
📚 Using structured sections for analysis of XXXX
✅ Generated clean markdown (15234 chars)
🤖 Analyzing paper XXXX...
✅ Saved analysis to cache for XXXX
```

## Troubleshooting

### Sections Not Generated?
- Check backend logs for extraction errors
- Sections extraction uses gpt-5-nano (verify API key)
- Falls back gracefully if extraction fails

### Analysis Using Raw Markdown?
- Sections might not be cached yet
- Re-load the paper content to trigger extraction
- Check `cache-status` endpoint

### Invalid Section Data?
- Clear cache: `cache_service.clear_cache(arxiv_id, 'sections')`
- Re-parse the paper with `force_reload=true`

## Future Enhancements

Potential improvements:
- [ ] Section-by-section display in UI
- [ ] Interactive section navigation
- [ ] Section-specific queries
- [ ] Multi-paper section comparison
- [ ] Custom section templates

---

**Last Updated:** February 5, 2026
