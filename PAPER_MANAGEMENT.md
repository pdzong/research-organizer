# Paper Management Guide

This guide explains how to add and manage research papers in the Research Agent application.

## Overview

The application now uses a local JSON file (`backend/data/papers.json`) to store papers instead of scraping HuggingFace. This gives you full control over which papers are available.

## Adding Papers

### Method 1: Using the Web UI (Recommended)

1. Open the application in your browser
2. Click the **"Add Paper"** button at the top of the paper list
3. Paste an ArXiv URL (e.g., `https://arxiv.org/abs/1706.03762`)
4. Click **"Add Paper"**
5. The system will:
   - Validate the URL
   - Fetch the paper title and authors from ArXiv
   - Add it to your paper list
   - Save it to the JSON file

**Supported URL formats:**
- `https://arxiv.org/abs/1706.03762`
- `https://arxiv.org/pdf/1706.03762.pdf`
- `arxiv.org/abs/1706.03762`

### Method 2: Using the API

```bash
curl -X POST http://localhost:8000/api/papers/add \
  -H "Content-Type: application/json" \
  -d '{"arxiv_url": "https://arxiv.org/abs/1706.03762"}'
```

Response:
```json
{
  "success": true,
  "paper": {
    "id": "1706.03762",
    "title": "Attention Is All You Need",
    "authors": ["Vaswani et al."],
    "arxiv_url": "https://arxiv.org/abs/1706.03762",
    "arxiv_id": "1706.03762"
  },
  "message": "Successfully added paper 1706.03762"
}
```

### Method 3: Manual Editing

1. Open `backend/data/papers.json` in a text editor
2. Add your paper to the array:

```json
{
  "id": "2401.12345",
  "title": "Your Paper Title",
  "authors": ["Author One", "Author Two"],
  "arxiv_url": "https://arxiv.org/abs/2401.12345",
  "arxiv_id": "2401.12345"
}
```

3. Save the file
4. Restart the backend (the file is loaded on startup)

## Finding ArXiv URLs

1. Go to [arxiv.org](https://arxiv.org)
2. Search for a paper
3. Copy the URL from the paper's abstract page
4. Use it in any of the methods above

## Default Papers

The application comes with 8 curated papers:

1. **Attention Is All You Need** (1706.03762) - The Transformer architecture
2. **GPT-4 Technical Report** (2303.08774) - GPT-4 details
3. **Llama 2** (2307.09288) - Meta's open model
4. **GPT-3** (2005.14165) - Language Models are Few-Shot Learners
5. **CLIP** (2103.00020) - Vision-Language model
6. **Vision Transformer** (2010.11929) - ViT architecture
7. **BERT** (1810.04805) - Bidirectional transformers
8. **LoRA** (2106.09685) - Low-Rank Adaptation

## Data Storage

Papers are stored in: `backend/data/papers.json`

Example structure:
```json
[
  {
    "id": "1706.03762",
    "title": "Attention Is All You Need",
    "authors": ["Vaswani et al."],
    "arxiv_url": "https://arxiv.org/abs/1706.03762",
    "arxiv_id": "1706.03762"
  },
  {
    "id": "2303.08774",
    "title": "GPT-4 Technical Report",
    "authors": ["OpenAI"],
    "arxiv_url": "https://arxiv.org/abs/2303.08774",
    "arxiv_id": "2303.08774"
  }
]
```

## Validation

When adding papers, the system validates:
- ✅ ArXiv URL format is correct
- ✅ Paper exists on ArXiv (HTTP check)
- ✅ Paper is not already in the list (no duplicates)

## Tips

- **New papers first**: Newly added papers appear at the top of the list
- **No duplicates**: Can't add the same paper twice (checked by ArXiv ID)
- **Auto-metadata**: Title and authors are fetched automatically
- **Persistent**: Papers are saved to disk and survive restarts

## Troubleshooting

### "Invalid ArXiv URL format"
- Make sure you're using a valid ArXiv URL
- Format: `https://arxiv.org/abs/XXXX.XXXXX`

### "Paper not found on ArXiv"
- Check that the paper ID is correct
- Make sure the paper exists on arxiv.org

### "Paper already exists"
- The paper is already in your list
- Check the existing papers before adding

### Papers not showing up
- Make sure the backend restarted after manual edits
- Check `backend/data/papers.json` exists
- Check console for error messages

## API Endpoints

### Get all papers
```bash
GET /api/papers
```

### Add a paper
```bash
POST /api/papers/add
Body: {"arxiv_url": "https://arxiv.org/abs/1706.03762"}
```

### Parse a paper
```bash
GET /api/papers/{paper_id}/parse
```

### Analyze a paper
```bash
POST /api/papers/analyze
Body: {"markdown": "paper content..."}
```
