# Research Paper Analyzer

A full-stack web application for analyzing research papers from ArXiv. The app allows you to manage a curated list of papers, parse ArXiv PDFs to markdown, and uses OpenAI GPT-4o-mini for intelligent paper summarization.

## Features

- 📚 **Manage Papers**: Add and browse research papers from ArXiv
- ➕ **Add Papers**: Add any paper by pasting its ArXiv URL
- 📄 **PDF Parsing**: Download and convert ArXiv PDFs to readable markdown
- 🤖 **AI Analysis**: Summarize papers using OpenAI GPT-4o-mini with structured outputs
- 🔬 **Semantic Scholar Integration**: Rich metadata including citations, recommendations, and influential citation counts
- 🎯 **Relevance Scoring**: Visual color gradients highlight the most important related papers using Semantic Scholar's metrics
- 💾 **Smart Caching**: Automatic caching of parsed PDFs, metadata, and analysis results
- 🔭 **Observability**: LLM call tracing with Arize Phoenix
- 🎨 **Modern UI**: Beautiful interface built with Mantine components
- ⚡ **Fast Performance**: React + Vite frontend with FastAPI backend

## 🔥 Relevance Scoring

Related papers (citations and recommendations) are displayed with **visual color gradients** that highlight their importance:

- **🔥 Highly Relevant (Gold)**: Papers with high citation counts and many influential citations
- **📈 Very Relevant (Yellow)**: Papers with significant impact
- **📊 Relevant (Light Blue)**: Papers with moderate impact
- **📄 Related (Gray)**: Papers with lower impact

The scoring uses **Semantic Scholar's proprietary metrics**:
- **Citation Count**: Total citations received
- **Influential Citation Count**: High-quality citations (Semantic Scholar's algorithm)
- **Recommendation Position**: For recommended papers, earlier = more relevant

Papers with scores ≥50 are highlighted with **thicker borders** and **icons** for quick identification. See [RELEVANCE_SCORING.md](RELEVANCE_SCORING.md) for detailed algorithm documentation.

## Architecture

```
research_agent/
├── backend/                 # FastAPI Python backend
│   ├── data/               # Paper storage
│   │   └── papers.json     # Paper list
│   ├── services/           # Business logic
│   │   ├── huggingface.py # Paper management
│   │   ├── pdf_parser.py  # PDF to markdown
│   │   └── openai_service.py # AI summarization
│   ├── routers/           # API endpoints
│   └── main.py            # FastAPI app
└── frontend/               # React + Vite + Mantine
    └── src/
        ├── components/    # UI components
        └── services/      # API client
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn
- OpenAI API key

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your OpenAI API key:
```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Then edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=your_actual_api_key_here
```

5. Run the backend server:
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Usage

1. **Browse Papers**: The app loads a curated list of 8 default papers on startup
2. **Add New Papers**: Click "Add Paper" and paste any ArXiv URL (e.g., `https://arxiv.org/abs/1706.03762`)
3. **Select a Paper**: Click on any paper card to view details
4. **Load Content**: Click "Load Paper Content" to download and parse the PDF
5. **Analyze**: Once loaded, click "Analyze Paper" to generate an AI summary

See [PAPER_MANAGEMENT.md](PAPER_MANAGEMENT.md) for detailed guide on managing papers.

## API Endpoints

- `GET /api/papers` - Get all papers from local storage
- `POST /api/papers/add` - Add a new paper by ArXiv URL
- `GET /api/papers/{paper_id}/parse` - Parse a paper's PDF to markdown
- `POST /api/papers/analyze` - Analyze paper content with OpenAI

See [PAPER_MANAGEMENT.md](PAPER_MANAGEMENT.md) for API usage examples.

## Technologies Used

### Backend
- **FastAPI**: Modern Python web framework
- **PyMuPDF**: PDF parsing and text extraction
- **OpenAI API**: GPT-4o-mini for paper summarization with structured outputs
- **Semantic Scholar API**: Rich paper metadata, citations, and recommendations
- **Arize Phoenix**: LLM observability and tracing
- **httpx**: Async HTTP client

### Frontend
- **React 18**: UI framework
- **Vite**: Build tool and dev server
- **Mantine UI**: Component library
- **TypeScript**: Type safety
- **Axios**: HTTP client
- **react-markdown**: Markdown rendering

## Development

### Backend Development
```bash
cd backend
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation.

### Frontend Development
```bash
cd frontend
npm run dev
```

### Building for Production

**Frontend:**
```bash
cd frontend
npm run build
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Backend Issues

- **ModuleNotFoundError**: Make sure you've activated the virtual environment and installed all dependencies
- **OpenAI API Error**: Verify your API key in the `.env` file
- **PDF Parsing Errors**: Some papers may have restricted access or unusual PDF formats

### Frontend Issues

- **CORS Errors**: Ensure the backend is running on port 8000
- **API Connection Failed**: Check that both frontend and backend servers are running
- **Build Errors**: Delete `node_modules` and run `npm install` again

## License

MIT

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.
