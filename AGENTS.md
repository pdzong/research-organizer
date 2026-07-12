# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a **Research Paper Analyzer** — a full-stack web application (Python FastAPI backend + React/Vite/TypeScript frontend) for discovering, parsing, and AI-analyzing research papers from ArXiv. The pipeline also derives application ideas and codegen-ready system plans. No database is used; all data is stored in flat JSON files under `backend/data/`.

### Services

| Service | Directory | Port | Start Command |
|---------|-----------|------|---------------|
| FastAPI Backend | `backend/` | 8000 | `cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000` |
| Vite Frontend | `web_ui/` | 5173 | `cd web_ui && npm run dev` |
| Docker stack | repo root | 8000 / 5173 / 6006 | `docker compose up --build` (optional OCR on 8080; optional `local-llm` profile on 9001) |

### Important caveats

- **Frontend directory is `web_ui/`**, not `frontend/` as referenced in some docs and `start-frontend.sh`. The start scripts have incorrect paths.
- **Environment / API keys**: Copy `.env.example` to `.env` at the repo root (Docker) or `backend/.env` (local dev). At least one LLM provider key is required (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`/`GEMINI_API_KEY`). Per-role provider/model routing is configured in the UI and persisted to `backend/data/llm_config.json`. Without a valid key for the active provider, listing/adding papers works but AI features fail.
- **PDF parsing can be slow**: The `/api/papers/{id}/parse` endpoint downloads and processes ArXiv PDFs. First-time parsing can take 60+ seconds for large papers. Cached results are stored in `backend/data/cache/{arxiv_id}/markdown.md`.
- **Arize Phoenix**: The backend tries to start Phoenix (LLM tracing) on port 6006 during startup. If it fails (e.g., missing deps or port conflict), the server continues gracefully.
- **TypeScript errors**: The codebase has pre-existing TS errors in `src/App.tsx` and `src/components/ApplicationDetail.tsx`. `tsc --noEmit` and `npm run build` will fail, but `npm run dev` (Vite dev server) runs fine.
- **No ESLint or Python linter configured** — TypeScript checking (`npx tsc --noEmit`) is the primary lint tool for the frontend. No Python linting tools are configured.
- **Python venv**: The backend uses a standard Python venv at `backend/venv/`. Always activate it before running backend commands.
- **Docker Compose**: `docker-compose.yml` runs backend, frontend, and an optional GPU OCR service. An optional `local-llm` profile (`scripts/start-local-vllm.sh`) adds a vLLM Qwen endpoint for cost-free inference. The `spark-vllm-docker/` build context is required for the local-LLM profile and may need to be present separately.
- **Source expansion plan**: See `KNOWLEDGE_SOURCES_EXPANSION_PLAN.md` for the roadmap to move beyond ArXiv-only ingestion (OpenAlex, CORE, Europe PMC, etc.).
- **Product roadmap**: See `ROADMAP.md` for phased product direction (company profiles, surprise-risk, briefings). Use skill `research-roadmap` (`.cursor/skills/research-roadmap/`) to navigate status, pick the next task, or adjust the plan.

### Running tests

Standalone test scripts live in `backend/test_*.py` (source-neutral papers, OpenAlex provider, PDF-URL parsing, generalized add, company profiles). Run each directly with the venv Python (e.g. `backend/venv/Scripts/python.exe backend/test_company_profiles.py` from the repo root, with `backend` as cwd); they print an "all tests passed" line on success and need no API keys (LLM calls are mocked). There is no pytest configuration. Broader manual testing is done via API calls and the web UI — see `TESTING.md` (the "Testing discovery & company-profiled research" section covers the P1/P2 features).

### API docs

Interactive API documentation is available at `http://localhost:8000/docs` when the backend is running.
