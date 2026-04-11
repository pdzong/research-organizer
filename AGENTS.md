# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a **Research Paper Analyzer** — a full-stack web application (Python FastAPI backend + React/Vite/TypeScript frontend) for discovering, parsing, and AI-analyzing research papers from ArXiv. No database is used; all data is stored in flat JSON files under `backend/data/`.

### Services

| Service | Directory | Port | Start Command |
|---------|-----------|------|---------------|
| FastAPI Backend | `backend/` | 8000 | `cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000` |
| Vite Frontend | `web_ui/` | 5173 | `cd web_ui && npm run dev` |

### Important caveats

- **Frontend directory is `web_ui/`**, not `frontend/` as referenced in some docs and `start-frontend.sh`. The start scripts have incorrect paths.
- **Backend `.env` file**: The backend requires a `backend/.env` file with `OPENAI_API_KEY=<key>`. Without a valid key, the server starts and paper listing/adding works, but AI analysis features will fail.
- **Arize Phoenix**: The backend tries to start Phoenix (LLM tracing) on port 6006 during startup. If it fails (e.g., missing deps or port conflict), the server continues gracefully.
- **TypeScript errors**: The codebase has pre-existing TS errors in `src/App.tsx` and `src/components/ApplicationDetail.tsx`. `tsc --noEmit` and `npm run build` will fail, but `npm run dev` (Vite dev server) runs fine.
- **No ESLint or Python linter configured** — TypeScript checking (`npx tsc --noEmit`) is the primary lint tool for the frontend. No Python linting tools are configured.
- **Python venv**: The backend uses a standard Python venv at `backend/venv/`. Always activate it before running backend commands.
- **No Docker** — The app runs directly via Python venv + npm. No Docker files exist in the repo.

### Running tests

No automated test suite exists in this codebase. Manual testing is done via API calls and the web UI. See `TESTING.md` for manual testing guidance.

### API docs

Interactive API documentation is available at `http://localhost:8000/docs` when the backend is running.
