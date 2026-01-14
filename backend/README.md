# Research Agent Backend

FastAPI backend for the Research Paper Analyzer.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
- Copy `.env.example` to `.env` (if exists) or create `.env`
- Add your OpenAI API key to `.env`

4. Run the server:
```bash
uvicorn main:app --reload --port 8000
```

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/papers` - Get papers from HuggingFace
- `GET /api/papers/{paper_id}/parse` - Parse paper PDF
- `POST /api/papers/analyze` - Analyze paper with AI
