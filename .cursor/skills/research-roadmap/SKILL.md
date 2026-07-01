---
name: research-roadmap
description: >-
  Navigate and update ROADMAP.md for the research_agent project. Shows phase
  progress, task list, and the single next actionable task. Adjusts priorities,
  adds/defers/cancels tasks, and marks work complete. Use when the user asks
  about the roadmap, what to work on next, plan status, priorities, or wants
  to update the product plan.
---

# Research Roadmap

Canonical plan: **`ROADMAP.md`** at the repo root.
Technical ingestion detail: **`KNOWLEDGE_SOURCES_EXPANSION_PLAN.md`** (reference for P1 only).

## One skill, two modes

Use **one skill** (this file) for both navigation and adjustment — they share the same file format and status fields. Splitting into two skills would duplicate conventions and drift out of sync.

| User intent | Mode | Action |
|-------------|------|--------|
| "What's next?", "roadmap status", "what should I work on?" | **Navigate** | Read ROADMAP.md → report status |
| "Mark P1-001 done", "defer P4", "add a task for X", "reprioritize" | **Adjust** | Edit ROADMAP.md → confirm diff |
| "Work on the roadmap", "start next task" | **Work** | Navigate → implement → Adjust (mark done) |

Default to **Navigate** unless the user clearly wants edits or implementation.

---

## Navigate workflow

1. Read `ROADMAP.md` (at minimum: Quick Status, At a glance, active phase tasks).
2. Find **Next task** from Quick Status; verify it is still `todo` or `in_progress` and dependencies are `done`.
3. If Next task is stale, recompute: lowest phase, first `todo`/`in_progress` task whose dependencies are all `done`.
4. Reply using **Status template** below.

### Status template

```markdown
## Roadmap status

**Active phase:** P{n} — {name}
**Next task:** [{ID}](ROADMAP.md#{anchor}) — {title} (`{status}`)

### Phase progress
| Phase | Status | Done |
|-------|--------|------|
(copy from At a glance table)

### Next task detail
- **Acceptance:** …
- **Depends on:** …
- **Likely files:** … (from task notes if present)

### Suggested action
One concrete sentence: what to implement or decide next.
```

Keep the response short unless the user asks for the full task list.

---

## Adjust workflow

1. Read `ROADMAP.md` fully (task tables + changelog).
2. Apply the requested change using **edit rules** below.
3. Update **Quick Status** (`Last updated`, `Next task`, `Active phase` if phase completed).
4. Recalculate **At a glance → Progress** for affected phases.
5. Append a row to **Changelog**.
6. Show the user what changed (task ID, old → new status, new Next task).

### Edit rules

| Request | Action |
|---------|--------|
| Mark done | Set status `done`; advance Next task |
| Start work | Set status `in_progress` (only one `in_progress` per phase recommended) |
| Defer / pause | Set status `deferred`; pick next `todo` |
| Cancel | Set status `cancelled`; never reuse ID |
| New task | Add row with next free ID in phase (`P{n}-{nnn}`); status `todo` |
| New phase | Add section with table; add row to At a glance |
| Reprioritize | Reorder within phase **or** move task to another phase (update ID only if pre-todo; otherwise add new ID and cancel old) |
| Promote backlog | Move item from "Deferred / ideas backlog" into a phase table |

**Never renumber existing task IDs.** Cancel and add a replacement if needed.

### P1 and expansion plan

When adding ingestion/source tasks, prefer linking to `KNOWLEDGE_SOURCES_EXPANSION_PLAN.md` rather than duplicating API details. If a task completes a slice of that doc, note it in Changelog.

---

## Work workflow

When the user wants to execute the plan (not just read it):

1. **Navigate** — confirm Next task and acceptance criteria.
2. **Implement** — follow repo conventions (`AGENTS.md`, minimal scope).
3. **Adjust** — mark task `done`, update Quick Status, log changelog.
4. If implementation reveals new work, **Adjust** — add tasks to current or backlog section before closing.

If Next task is large, propose splitting into subtasks (new IDs) and set the first to `in_progress`.

---

## Quick commands (user phrases)

| Phrase | Mode |
|--------|------|
| "roadmap" / "plan status" | Navigate |
| "what's next" | Navigate |
| "mark {ID} done" | Adjust |
| "defer {ID}" | Adjust |
| "add task: …" | Adjust |
| "reprioritize P2 before P3" | Adjust |
| "work on next roadmap task" | Work |

---

## Validation checklist

Before finishing an Adjust or Work session:

- [ ] Quick Status **Next task** points to a valid `todo`/`in_progress` item
- [ ] **Last updated** is today's date
- [ ] Phase progress counts match task statuses
- [ ] Changelog entry added for non-trivial edits
- [ ] No duplicate Next task pointers
