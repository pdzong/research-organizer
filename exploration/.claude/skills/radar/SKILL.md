---
name: radar
description: Weekly scan of new and trending papers against the open questions in the exploration vault, to spot work that moves a trade-off frontier or answers an open question. Use when the user asks for the weekly radar, what is new, or whether anything changed for their cards.
argument-hint: [optional ISO week like 2026-W47, defaults to the past 7 days]
---

# Radar

Period: $ARGUMENTS (default: the last 7 days)

1. **Load the watch list.** Read the open questions in `INDEX.md` and the
   seven-question sections of each non-stub card.
2. **Collect candidates** for the period, aiming for about 30 to 60 papers:
   - Hugging Face trending papers:
     `https://huggingface.co/api/daily_papers?sort=trending&week=<YYYY-Www>`
     (or `date=` per day).
   - alphaXiv `discover_papers` for each card's topic, with
     `prioritize: recency` and `published_after` set to the period start.
   - Emergent Mind trending in `cs.LG`, `cs.CL`, `cs.AI` (one batched call;
     the free plan is limited).
   - Web search for posts in the period by Sebastian Raschka, Maarten
     Grootendorst and Epoch AI.
3. **Triage.** For each candidate, decide from the abstract whether it touches
   a card. Keep only those that do. For each kept paper, classify:
   - **Moves a frontier**: claims a better trade-off, not just a different
     point on it. Check whether the comparison is at equal compute, memory or
     state budget.
   - **Answers or sharpens an open question.**
   - **New boundary**: a theorem or a consistent negative result.
   - **Adoption signal**: a shipped model or widely used code.
   - **New lineage link** to an older field.
4. **Verify** each kept paper's title, authors and id with a tool before
   writing about it.
5. **Write `radar/<YYYY-Www>.md`** with:
   - A three-sentence summary of the week for this reader.
   - "Worth your attention": at most three papers, each with the card it
     affects, the classification, and why in two sentences.
   - "Also relevant": a short list, one line each.
   - "Suggested card updates": concrete edits, not yet applied.
   - "New questions" that came up.
6. **Do not edit cards automatically.** Ask the user which suggested updates to
   apply, then apply them with `/investigate` or directly.
7. Add the report to the "Radar reports" section of `INDEX.md`, then commit
   and push files under `exploration/`.
