# Research Paper Analyzer

A full-stack web application for turning research papers into **codegen-ready system plans**.

The pipeline goes:

1. **Collect** papers from ArXiv or HuggingFace daily papers.
2. **Parse** the PDF to markdown (optional local vLLM OCR service).
3. **Analyze** the paper with a structured-output LLM call (novelty, methodology, benchmarks, applications).
4. **Derive** concrete application ideas from the analysis.
5. **Plan**: turn each application (+ its grounding papers) into a concrete `SolutionPlan` — architecture, modules, APIs, milestones, tech stack, and a self-contained `code_generation_prompt` ready to hand to a downstream code-gen agent.
6. **Automate**: run steps 1-5 continuously on newly-published papers, with optional plan-worthiness gating so only concrete ideas get turned into plans.

Each LLM role can be routed to **OpenAI**, **Anthropic Claude**, or **Google Gemini** from a Settings modal in the UI.

## Features

- **Manage papers** — curated local list, add any paper by ArXiv URL.
- **PDF parsing** — PyMuPDF by default; pluggable local OCR service (vLLM) available via Docker.
- **Structured analysis** — novelty, methodology, applications, benchmarks, and citation-backed quotes via native Structured Outputs.
- **Rich metadata** — Semantic Scholar citations, recommendations, influential citation counts.
- **Relevance scoring** — visual color gradients over related papers. See [RELEVANCE_SCORING.md](RELEVANCE_SCORING.md).
- **Applications view** — LLM-derived application ideas per paper, with human-in-the-loop related-paper filtering.
- **Solutions view** — generate codegen-ready `SolutionPlan` for an application; renders as markdown + downloadable artifact + copyable codegen prompt.
- **Auto-research mode** — background runner that walks HuggingFace daily papers, pushes each through the full pipeline, and (optionally) escalates plan-worthy applications into full `SolutionPlan`s. Limitable and continuous.
- **Pluggable LLM providers** — per-role provider / model config (OpenAI / Anthropic / Gemini), persisted to disk, editable from the UI.
- **Smart caching** — parsed PDFs, metadata, analyses, applications, and plans are all cached on disk.
- **Observability** — LLM call tracing with Arize Phoenix.
- **Modern UI** — React + Vite + Mantine.

## Architecture

```
research_agent/
├── backend/                  # FastAPI Python backend
│   ├── data/
│   │   ├── papers.json       # Paper list
│   │   ├── cache/            # Per-paper cache (markdown, sections, analysis)
│   │   │   ├── applications.json
│   │   │   └── solutions/    # SolutionPlan JSON + .md artifacts
│   │   └── llm_config.json   # (runtime-generated) per-role provider/model
│   ├── services/
│   │   ├── llm_config.py     # Per-role provider/model config
│   │   ├── llm_clients.py    # Multi-provider adapter (OpenAI/Anthropic/Gemini)
│   │   ├── openai_service.py # summarize / section-extract / relevance filter
│   │   ├── solution_planner.py # application → SolutionPlan (agentic)
│   │   ├── auto_research.py  # background runner (HF → full pipeline → plans)
│   │   ├── huggingface.py    # Paper management
│   │   ├── pdf_parser.py     # PDF to markdown
│   │   ├── semantic_scholar.py
│   │   ├── deep_analysis.py  # Related-paper enrichment
│   │   └── cache_service.py  # JSON cache layer
│   ├── routers/
│   │   ├── papers.py
│   │   ├── solutions.py      # /api/applications/{id}/plan, /api/solutions
│   │   ├── auto_research.py  # /api/auto-research/{start,stop,status,sources}
│   │   └── config.py         # /api/config/llm
│   └── main.py
├── web_ui/                   # React + Vite + Mantine frontend (NOTE: named web_ui, not frontend)
│   └── src/
│       ├── components/
│       │   ├── Layout.tsx
│       │   ├── PaperList.tsx / PaperDetail.tsx
│       │   ├── ApplicationList.tsx / ApplicationDetail.tsx
│       │   ├── SolutionList.tsx / SolutionDetail.tsx
│       │   ├── AutoResearchView.tsx
│       │   └── LlmConfigModal.tsx  # Provider & model settings
│       └── services/api.ts
├── ocr/                      # Optional local vLLM-based OCR service
├── docker-compose.yml
└── .env.example
```

## Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- At least one LLM provider API key (OpenAI, Anthropic, or Google Gemini)
- (Optional) Docker, for the containerised stack and the local vLLM OCR service

### Environment

```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

Then fill in at least one of:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...           # or GEMINI_API_KEY
TAVILY_API_KEY=              # optional — enables the deep-research extension
```

OpenAI is the default provider for every role; any role can be routed to a different provider from the Settings modal in the UI (gear icon in the header) once that provider's key is set.

### Run with Docker (recommended)

```bash
docker compose up --build
```

This starts:

- Backend (FastAPI) on `http://localhost:8000`
- Frontend (Vite → nginx) on `http://localhost` (port 80)
- (Optional) OCR service on `http://localhost:8001`

Phoenix UI is available at `http://localhost:6006` once the backend is up.

### Run locally

**Backend:**

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**

```bash
cd web_ui
npm install
npm run dev
```

The app is then available at `http://localhost:5173`.

Shortcut scripts:

```bash
./start-frontend.sh      # or start-frontend.bat on Windows
```

## Usage

### Browse & analyze papers

1. Open the **Papers** tab. The default list ships with several curated papers; add new ones via "Add Paper" (paste any ArXiv URL).
2. Select a paper → "Load Paper Content" parses the PDF. "Analyze Paper" runs the structured-output LLM pass.
3. The analysis screen shows novelty, methodology, applications, and benchmark results with source quotes.

### Derive applications

Each analysis surfaces concrete application ideas. Open **Applications** to browse saved application entries (application idea + source paper + related papers you curated).

### Generate codegen-ready plans

From an application's detail view, click **"Generate System Plan"**.

The planner does two agentic steps:

1. A cheap brief-drafting pass aggregates all paper contexts into a tight technical brief.
2. A structured synthesis pass emits a full `SolutionPlan` (architecture diagram, 3-7 modules with paper grounding, data models, APIs, milestones, risks, success metrics, plus a self-contained `code_generation_prompt`).

Plans appear in the **Solutions** tab. You can copy the codegen prompt, download the full markdown artifact, or regenerate.

### Auto-research mode

Open the **Auto-Research** tab to start a background runner that walks HuggingFace daily papers and pushes each through the full pipeline. Options:

- **Limit** — max papers per batch.
- **Continuous mode** — keep looping, sleeping `interval_seconds` between batches.
- **Generate target plans** — after each paper's applications are saved, run a cheap LLM plan-worthiness gate and, if the application passes (`confidence ≥ plan_min_confidence`), automatically build a full `SolutionPlan`. Generated plans show up in the Solutions tab in real time.

The status panel streams live logs and shows processed / skipped / error / application / plan counters.

### Settings: provider & model per role

Click the gear icon in the header. The modal lists every LLM role used by the backend:

- `deep_analysis` — full paper analysis (novelty, benchmarks, applications).
- `sections` — cheap segmentation of raw OCR markdown.
- `relevance` — yes/no filter for "is this paper relevant to an application?"
- `plan_brief` — cheap aggregation pass before plan synthesis.
- `plan_synthesis` — structured SolutionPlan generation.
- `plan_worthy` — auto-research plan-worthiness gate.

For each role, pick a provider and a model. Model names are free-form (suggestions are provided per provider, but you can type any model id). Overrides are persisted to `backend/data/llm_config.json` and take effect immediately.

## API endpoints

Papers:

- `GET  /api/papers`
- `POST /api/papers/add`
- `GET  /api/papers/{paper_id}/parse`
- `GET  /api/papers/{arxiv_id}/metadata`
- `GET  /api/papers/{arxiv_id}/analyze`
- `POST /api/papers/analyze`

Applications:

- `GET  /api/applications`
- `POST /api/applications/add`

Solutions:

- `POST /api/applications/{application_id}/plan` — generate (or force-regenerate) a plan
- `GET  /api/applications/{application_id}/plan` — fetch cached plan
- `GET  /api/solutions` — list all generated plans

Auto-research:

- `GET  /api/auto-research/sources`
- `POST /api/auto-research/start`
- `POST /api/auto-research/stop`
- `GET  /api/auto-research/status`

LLM config:

- `GET  /api/config/llm`
- `PUT  /api/config/llm`
- `POST /api/config/llm/reset`

Interactive docs: `http://localhost:8000/docs`.

## Technologies

### Backend

- FastAPI, Uvicorn
- OpenAI Python SDK (Structured Outputs via `responses.parse`)
- Anthropic SDK (structured via forced `tool_use`)
- `google-genai` (structured via `response_schema`)
- PyMuPDF — PDF parsing
- Semantic Scholar API
- Arize Phoenix — LLM tracing

### Frontend

- React 18 + TypeScript + Vite
- Mantine UI 7
- `react-markdown` for plan rendering
- Axios

## Development

```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd web_ui && npm run dev

# Type-check
cd web_ui && npx tsc --noEmit

# Production build (frontend)
cd web_ui && npm run build
```

## Troubleshooting

- **`OPENAI_API_KEY not set`** — set at least one provider key in `.env`, or route all roles in the Settings modal to a provider whose key is present.
- **Anthropic / Gemini SDK missing** — if you routed a role to Anthropic or Gemini but didn't install the SDK, `pip install -r backend/requirements.txt` to pick up `anthropic` and `google-genai`.
- **OCR service crashes** — the upstream `vllm/vllm-openai:nightly` image sometimes drops transitive deps; the provided `ocr/Dockerfile` pins `pandas>=2.0,<3` to work around this.
- **CORS errors** — make sure the backend is on 8000 and the frontend on 5173 / 80.
- **Frontend build errors** — `rm -rf web_ui/node_modules && cd web_ui && npm install`.

## License

MIT

## Contributing

Pull requests are welcome. For major changes, open an issue first to discuss the scope.
