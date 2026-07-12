# Research Agent — Product Roadmap

> **Canonical plan file** for evolving this repo into a company-focused research intelligence service.
> Use the project skill `.cursor/skills/research-roadmap/` to navigate, update status, and adjust priorities.

## Quick Status

| Field | Value |
|-------|-------|
| **Last updated** | 2026-07-12 |
| **Vision** | Research-as-a-service: help companies spot relevant advances, weak signals, and disruption risks before they are obvious in product roadmaps |
| **Active phase** | P2 — Company research profiles |
| **Next task** | [P2-003](#p2-003-thread-profile-into-relevance--plan_worthy-prompts) |
| **Blocked by** | — |

### At a glance

| Phase | Name | Status | Progress |
|-------|------|--------|----------|
| P0 | Housekeeping & dev ergonomics | done | 4/4 |
| P1 | Source expansion (OpenAlex slice) | done | 6/6 |
| P2 | Company research profiles | in progress | 3/5 |
| P3 | Surprise-risk & assumption ledger | todo | 0/4 |
| P4 | Technology radar & weak signals | todo | 0/4 |
| P5 | Scheduled briefings | todo | 0/3 |
| P6 | Service packaging (multi-tenant SaaS) | todo | 0/4 |

**Progress rule:** count tasks marked `done` / total tasks in phase.

---

## Vision

Transform the Research Paper Analyzer from an ArXiv-centered ingestion tool into a **research intelligence platform** that:

1. Discovers broadly across scientific sources (not only ArXiv / HuggingFace).
2. Analyzes papers through a **company-specific lens** (industry, product, tech stack, strategic questions).
3. Surfaces **weak signals and converging trajectories** — the kind of cross-domain shifts that caught conversational-AI companies off guard when LLMs matured.
4. Produces actionable outputs: fit scores, impact forecasts, assumption challenges, and codegen-ready plans where appropriate.

### Product tiers (target)

| Tier | Deliverable |
|------|-------------|
| **Watch** | Curated feed + strategic fit scores |
| **Analyze** | Deep dives + application ideas (existing Applications view) |
| **Plan** | SolutionPlans for vetted opportunities (existing Solutions view) |
| **Radar** | Trend clusters, forecasts, assumption challenges (new) |

### Related technical docs

- [KNOWLEDGE_SOURCES_EXPANSION_PLAN.md](KNOWLEDGE_SOURCES_EXPANSION_PLAN.md) — detailed ingestion architecture (OpenAlex, CORE, Europe PMC, etc.). **P1 implements the first vertical slice from that doc.**
- [README.md](README.md) — current feature set and setup.
- [AGENTS.md](AGENTS.md) — agent/dev environment notes.

---

## Task conventions

Each task has:

- **ID** — `P{phase}-{nnn}` (stable; do not renumber — mark cancelled instead).
- **Status** — one of: `todo` | `in_progress` | `done` | `deferred` | `cancelled`
- **Depends on** — optional list of task IDs.
- **Acceptance** — how to know it is complete.

**Next task** = lowest-phase task that is `todo` or `in_progress`, respecting dependencies.
When marking a task `done`, update **Quick Status → Next task** and **Last updated**.

---

## P0 — Housekeeping & dev ergonomics

| ID | Task | Status | Depends | Acceptance |
|----|------|--------|---------|------------|
| P0-001 | Pass multi-provider API keys through Docker Compose backend | done | — | `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY` in `docker-compose.yml` |
| P0-002 | Update AGENTS.md (Docker, multi-provider, roadmap pointer) | done | — | AGENTS.md reflects current stack |
| P0-003 | Add ROADMAP.md + research-roadmap skill | done | — | This file + `.cursor/skills/research-roadmap/SKILL.md` exist |
| P0-004 | Document `spark-vllm-docker/` requirement for local-LLM profile | done | — | README or AGENTS.md notes missing build context |

---

## P1 — Source expansion (OpenAlex first vertical slice)

Implements **Phase 1 + first vertical slice** from [KNOWLEDGE_SOURCES_EXPANSION_PLAN.md](KNOWLEDGE_SOURCES_EXPANSION_PLAN.md).

| ID | Task | Status | Depends | Acceptance |
|----|------|--------|---------|------------|
| P1-001 | Add `SourcePaper` model with source-neutral fields | done | — | Pydantic model; backward-compatible with existing `arxiv_id` records |
| P1-002 | Allow parse from direct `pdf_url` on paper record | done | P1-001 | `GET /api/papers/{id}/parse` works for records with `pdf_url` only |
| P1-003 | Implement OpenAlex discovery provider | done | P1-001 | `GET /api/sources/search?source=openalex&query=…` returns normalized papers |
| P1-004 | Resolve OA content from OpenAlex `best_oa_location` | done | P1-003 | Added paper can fetch and parse OA PDF when available |
| P1-005 | Generalize `POST /api/papers/add` (URL, DOI, source record) | done | P1-001 | Accept arXiv URL, DOI, or `{source, source_record_id}` |
| P1-006 | Frontend: rename add-paper input; show source/OA badges | done | P1-005 | UI supports non-ArXiv adds; badges on paper cards |

### P1-001: Add SourcePaper model

- **Status:** `done`
- **Files:** `backend/services/source_paper.py`, `backend/services/huggingface.py`, `backend/services/cache_service.py`, `backend/test_source_paper.py`
- **Notes:** `SourcePaper` + `normalize_legacy_paper()` + `paper_cache_key()` / `paper_legacy_cache_key()`. Legacy cache dirs unchanged (`cache/{arxiv_id}/`).

### P1-002: Allow parse from direct pdf_url

- **Status:** `done`
- **Files:** `backend/services/pdf_parser.py`, `backend/routers/papers.py`, `backend/services/source_paper.py`, `backend/test_pdf_url_parse.py`

### P1-003: Implement OpenAlex discovery provider

- **Status:** `done`
- **Files:** `backend/services/sources/openalex.py`, `backend/routers/sources.py`, `backend/test_openalex_provider.py`
- **Endpoints:** `GET /api/sources`, `GET /api/sources/search?source=openalex&query=…`

### P1-004: Resolve OA content from OpenAlex

- **Status:** `done`
- **Notes:** OpenAlex works are normalized with `pdf_url` from `best_oa_location` (P1-003); once added to the library, `GET /api/papers/{id}/parse` downloads and parses that PDF (P1-002). Verified live with an ACL Anthology OA PDF.

### P1-005: Generalize POST /api/papers/add

- **Status:** `done`
- **Files:** `backend/routers/papers.py` (dispatch), `backend/services/huggingface.py` (`add_source_paper` with id/DOI/arXiv dedupe), `backend/services/sources/openalex.py` (`get_openalex_work`), `backend/test_add_paper_generalized.py`
- **Accepts:** arXiv URL (legacy flow), DOI or doi.org URL (resolved via OpenAlex), OpenAlex id/URL, `{source, source_record_id}`, or a direct `.pdf` link (minimal `web` record).

### P1-006: Frontend Discover tab + badges

- **Status:** `done`
- **Files:** `web_ui/src/components/DiscoverView.tsx` (new), `web_ui/src/components/Layout.tsx`, `web_ui/src/components/PaperList.tsx`, `web_ui/src/services/api.ts`
- **Notes:** New **Discover** tab: OpenAlex keyword search, company-profile discovery with strategic-fit badges, one-click add to library. Paper list shows source / open-access / DOI badges; add-paper modal accepts any reference type.

## P2 — Company research profiles

| ID | Task | Status | Depends | Acceptance |
|----|------|--------|---------|------------|
| P2-001 | Define `CompanyProfile` schema + JSON storage | done | P1-001 | `backend/data/company_profiles.json` + CRUD API |
| P2-002 | Add strategic-fit scoring LLM role | done | P2-001 | Papers/applications scored with reasoning vs active profile |
| P2-003 | Thread profile into relevance + plan_worthy prompts | todo | P2-002 | Auto-research and manual flows respect active profile |
| P2-004 | UI: profile selector + editor | todo | P2-001 | Header or settings area to switch/create/**edit** profiles |
| P2-005 | Profile-driven discovery (watch topics → OpenAlex) | done | P2-001 | Watch topics drive discovery queries with optional fit scoring |

### P2-001: CompanyProfile schema + storage + CRUD

- **Status:** `done`
- **Files:** `backend/services/company_profiles.py`, `backend/routers/profiles.py`, `backend/test_company_profiles.py`
- **Schema:** name, industry, description, `tech_stack[]`, `strategic_questions[]`, `watch_topics[]` (drive discovery), `assumptions[]` (P3 surprise-risk hook).
- **Endpoints:** `GET/POST /api/profiles`, `GET/PUT/DELETE /api/profiles/{id}`, `POST /api/profiles/{id}/activate`, `GET /api/profiles/active`. First profile becomes active automatically.

### P2-002: Strategic-fit scoring role

- **Status:** `done`
- **Files:** `backend/services/strategic_fit.py`, `backend/services/llm_config.py` (new `strategic_fit` role, default `gpt-5-mini`)
- **Endpoint:** `POST /api/profiles/{id}/score/{paper_id}` — returns `fit_score` 0–100, opportunities, threats, challenged assumptions, recommended action (`ignore`/`watch`/`analyze`/`prototype`). Cached per (paper, profile) at `cache/{key}/strategic_fit_{profile_id}.json`; uses abstract + cached deep analysis as context.

### P2-003: Thread profile into relevance + plan_worthy prompts

- **Status:** `todo` — **this is the next task.**
- **Goal:** auto-research and manual analyze flows should consider the active company profile (e.g. pass profile context into `relevance` and `plan_worthy` prompts, and optionally auto-score processed papers).

### P2-004: UI profile selector + editor

- **Status:** `todo` (partially covered: Discover tab has profile **select + create**; missing: edit/delete UI, header-level selector visible across views)

### P2-005: Profile-driven discovery

- **Status:** `done` (simple version; scope adjusted from "filter paper list & auto-research" — auto-research integration moved under P2-003)
- **Endpoint:** `GET /api/profiles/{id}/discover?limit_per_topic=5&since=YYYY-MM-DD&score_top=N` — searches OpenAlex per watch topic, dedupes, optionally runs strategic-fit scoring on the top N results.
- **UI:** Discover tab → "Discover for company" button.

---

## P3 — Surprise-risk & assumption ledger

Addresses the “we didn’t see LLMs coming” failure mode.

| ID | Task | Status | Depends | Acceptance |
|----|------|--------|---------|------------|
| P3-001 | Assumption ledger on `CompanyProfile` | todo | P2-001 | Profile stores 3–10 testable strategic assumptions |
| P3-002 | `assumption_challenge` LLM role | todo | P3-001 | Structured output: which assumptions a paper challenges, with confidence |
| P3-003 | Surprise-risk score distinct from relevance | todo | P3-002 | Paper card shows both relevance and threat-to-thesis scores |
| P3-004 | Cross-domain adjacent scan config per profile | todo | P2-005 | Profile defines adjacent fields to monitor |

---

## P4 — Technology radar & weak signals

| ID | Task | Status | Depends | Acceptance |
|----|------|--------|---------|------------|
| P4-001 | Topic clustering over ingested paper corpus | todo | P1-003 | Weekly cluster summary stored/exportable |
| P4-002 | Velocity metrics (citation acceleration, author overlap) | todo | P1-003 | Metric fields on paper metadata view |
| P4-003 | Convergence alerts (“N labs, same week, same theme”) | todo | P4-001 | Alert records when cluster density spikes |
| P4-004 | `impact_forecast` LLM role (readiness timeline, build/buy/ignore) | todo | P2-002 | Structured forecast alongside deep analysis |

---

## P5 — Scheduled briefings

| ID | Task | Status | Depends | Acceptance |
|----|------|--------|---------|------------|
| P5-001 | Briefing generator (delta since last run) | todo | P4-001, P2-002 | Markdown briefing artifact per profile |
| P5-002 | Scheduler hook on auto-research runner | todo | P5-001 | Cron-friendly endpoint or CLI |
| P5-003 | Export delivery (email/webhook stub) | todo | P5-001 | Briefing downloadable; webhook POST optional |

---

## P6 — Service packaging

| ID | Task | Status | Depends | Acceptance |
|----|------|--------|---------|------------|
| P6-001 | `company_id` tenancy on papers/applications/plans | todo | P2-001 | Data partitioned per tenant |
| P6-002 | API key auth for external clients | todo | P6-001 | Bearer token gates write endpoints |
| P6-003 | Tiered feature flags (Watch/Analyze/Plan/Radar) | todo | P6-001 | Config disables tiers per tenant |
| P6-004 | Customer-facing briefing PDF/export | todo | P5-001 | Branded export template |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-07-01 | Initial roadmap created from product direction discussion. P0 completed. P1 set as active phase. |
| 2026-07-01 | P1-001 done: `SourcePaper` model, legacy normalization at read time, cache key helpers. |
| 2026-07-01 | P1-002 done: parse from direct `pdf_url`; refactored PDF download/parse helpers. |
| 2026-07-03 | P1-003 done: OpenAlex discovery provider + `/api/sources/search`. |
| 2026-07-12 | P1 complete (P1-004/005/006): generalized add (DOI/OpenAlex/PDF), OA parse verified, Discover tab + badges. |
| 2026-07-12 | P2 started: P2-001 profiles CRUD, P2-002 strategic-fit role + scoring endpoint, P2-005 profile-driven discovery (simple). First end-to-end company-profiled research flow works. Next: P2-003. |

---

## Deferred / ideas backlog

Items not yet scheduled — promote to a phase when ready.

| Idea | Notes |
|------|-------|
| Patent + paper cross-link | Who is filing vs publishing |
| Europe PMC / XML path | See expansion plan Phase 6 |
| bioRxiv / medRxiv adapters | See expansion plan Phase 7 |
| Multi-user auth (OAuth) | After P6 tenancy proves shape |
| `papers.json` as seed-only | Ship defaults; gitignore local runtime mutations |
