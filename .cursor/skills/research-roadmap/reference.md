# Roadmap reference

## File map

| File | Role |
|------|------|
| `ROADMAP.md` | Product phases P0–P6, task statuses, next task, changelog |
| `KNOWLEDGE_SOURCES_EXPANSION_PLAN.md` | Technical spec for source adapters (P1 implements first slice) |
| `.cursor/skills/research-roadmap/SKILL.md` | Agent workflow for navigate / adjust / work |

## Task ID registry (do not renumber)

### P0 — done
P0-001 … P0-004

### P1 — source expansion
P1-001 … P1-006

### P2 — company profiles
P2-001 … P2-005

### P3 — surprise risk
P3-001 … P3-004

### P4 — technology radar
P4-001 … P4-004

### P5 — briefings
P5-001 … P5-003

### P6 — SaaS packaging
P6-001 … P6-004

## Status semantics

| Status | Meaning |
|--------|---------|
| `todo` | Ready when dependencies satisfied |
| `in_progress` | Actively being worked |
| `done` | Acceptance criteria met |
| `deferred` | Intentionally postponed |
| `cancelled` | Will not do; ID retired |

## Phase completion

A phase is **done** when all non-cancelled tasks are `done`.
When the active phase completes, set **Active phase** to the next phase with open `todo` tasks.
