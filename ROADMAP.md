# Research Agent — Product Roadmap

> **Canonical plan file** for evolving this repo into a company-focused research intelligence service.
> Use the project skill `.cursor/skills/research-roadmap/` to navigate, update status, and adjust priorities.

## Quick Status

| Field | Value |
|-------|-------|
| **Last updated** | 2026-07-01 |
| **Vision** | Research-as-a-service: help companies spot relevant advances, weak signals, and disruption risks before they are obvious in product roadmaps |
| **Active phase** | P1 — Source expansion (first vertical slice) |
| **Next task** | [P1-001](#p1-001-add-sourcepaper-model) |
| **Blocked by** | — |

### At a glance

| Phase | Name | Status | Progress |
|-------|------|--------|----------|
| P0 | Housekeeping & dev ergonomics | done | 4/4 |
| P1 | Source expansion (OpenAlex slice) | todo | 0/6 |
| P2 | Company research profiles | todo | 0/5 |
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
| P1-001 | Add `SourcePaper` model with source-neutral fields | todo | — | Pydantic model; backward-compatible with existing `arxiv_id` records |
| P1-002 | Allow parse from direct `pdf_url` on paper record | todo | P1-001 | `GET /api/papers/{id}/parse` works for records with `pdf_url` only |
| P1-003 | Implement OpenAlex discovery provider | todo | P1-001 | `GET /api/sources/search?source=openalex&query=…` returns normalized papers |
| P1-004 | Resolve OA content from OpenAlex `best_oa_location` | todo | P1-003 | Added paper can fetch and parse OA PDF when available |
| P1-005 | Generalize `POST /api/papers/add` (URL, DOI, source record) | todo | P1-001 | Accept arXiv URL, DOI, or `{source, source_record_id}` |
| P1-006 | Frontend: rename add-paper input; show source/OA badges | todo | P1-005 | UI supports non-ArXiv adds; badges on paper cards |

### P1-001: Add SourcePaper model

- **Status:** `todo`
- **Files likely touched:** `backend/services/models.py`, `backend/services/huggingface.py`, `backend/data/papers.json` schema
- **Notes:** Keep `arxiv_id` optional; add `doi`, `source`, `source_record_id`, `pdf_url`, `oa_status`.

---

## P2 — Company research profiles

| ID | Task | Status | Depends | Acceptance |
|----|------|--------|---------|------------|
| P2-001 | Define `CompanyProfile` schema + JSON storage | todo | P1-001 | `backend/data/company_profiles.json` + CRUD API |
| P2-002 | Add strategic-fit scoring LLM role | todo | P2-001 | Papers/applications scored 0–1 with reasoning vs active profile |
| P2-003 | Thread profile into relevance + plan_worthy prompts | todo | P2-002 | Auto-research and manual flows respect active profile |
| P2-004 | UI: profile selector + editor | todo | P2-001 | Header or settings area to switch/create profiles |
| P2-005 | Filter paper list and auto-research by profile watch topics | todo | P2-004 | Watch topics drive discovery queries |

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
