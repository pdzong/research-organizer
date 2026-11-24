---
name: curate
description: Propose a clean-up of exploration vault cards that keeps the reading layer short and on topic. It judges each unit against the card's core ideas and the strength of its evidence, and moves weak, off-topic or disproved material to the card's shelf instead of deleting it. Use when the user asks to clean up, prune, tidy or curate cards, when a card is over budget, or after a radar update.
argument-hint: <card slug | all> [--challenge] | apply <report> <decisions>
---

# Curate

Arguments: $ARGUMENTS

Follow `curation-policy.md` (verdicts, budgets, approval tiers) and the
evidence rules in `CLAUDE.md`. Curation never deletes content.

## Mode 1: propose (`/curate <slug>` or `/curate all`)

1. **Measure.** Run `py curation/measure.py <slug>` (or with no slug for the
   summary, then the detailed report for each card over budget or with weak
   items). For `all`, skip cards that are within budget, have no weak items,
   and were curated since their last update, unless the user asked for them.
2. **Spine.** Read the card. If it has no `## Core ideas` section, draft three
   to six core ideas from L0, the seven questions and the open questions,
   each with its evidence label. If it has one, check whether new material
   since the last curation changes it.
3. **Judge each unit** at reading depth (L0, L1, the seven questions, L2 and
   extra sections), plus the open questions:
   - relevance to the spine (central, supporting, peripheral, elsewhere);
   - grounding (strong, adequate, weak, contradicted).
   Check grounding with tools, not memory: `viewer/papers.json` for metadata,
   alphaXiv `get_paper_content` or `answer_pdf_queries` to check that a
   source supports the claim, and Asta `get_citations` for replications or
   contradictions of results that a core idea rests on. Keep the tool work
   proportional: check every weak central unit and every proposed Supersede;
   sample the rest.
4. **Assign verdicts** with the table in the policy. Look across cards too:
   units that answer another card's question better (Move), and papers cited
   by several cards that are explained in full in more than one (Condense
   into one card, link from the others).
5. **Apply the automatic tier** from the policy (duplicates, formatting,
   missing L4 rows, Demote and Fold that keep every sentence). Do not apply
   anything else.
6. **Optional keeper review.** If `--challenge` was given, start one agent
   with the proposed Supersede and Archive units, the card's core ideas and
   open questions, but not your reasons. Ask it to argue for keeping each
   unit. Mark items it makes a good case for as "contested".
7. **Write the report** `curation/<YYYY-MM-DD>-<slug or all>.md` with the
   sections listed in the policy. Number every proposal. Quote at most a line
   of each unit; locate it by section.
8. **Rebuild the reader** (`py viewer/build.py`) if the automatic tier
   changed anything, and show the user:
   - how far each card was over budget and what that is after the
     automatic changes;
   - the proposed core ideas;
   - the proposals, one line each, grouped by verdict;
   - how to answer ("approve 1-6, reject 7").
   Stop and wait for the answer.

## Mode 2: apply (`/curate apply <report> <decisions>`)

Also used when the user answers a proposal in the same session.

1. Apply the approved items exactly as proposed, or as the user modified
   them:
   - **Supersede:** add an H3 entry under `## Superseded` with the claim,
     what replaced it and why it still matters, then remove the unit from the
     reading layer (leave a one-line pointer if a central question depended
     on it).
   - **Archive:** add an H3 entry under `## Archive` with the text as it was
     and where it came from, then remove it from the reading layer.
   - **Move:** add it to the target card, leave a one-line link behind, and
     log it in both cards.
   - **Close:** check the open question off with the answer and source.
   - Create the `## Superseded` or `## Archive` section, between
     `## Open questions` and `## Log`, if it does not exist yet.
2. Add a log line to each touched card: `- YYYY-MM-DD: curated (report
   curation/<file>): ...`, listing what moved where. Update `Last updated`.
3. Update `INDEX.md`: one-line summaries if L0 changed, and the open
   questions list.
4. Record the decisions at the end of the report (approved, rejected,
   modified).
5. Run `py curation/measure.py <slug>` again and report the new numbers.
6. Rebuild the reader and republish it as described in `CLAUDE.md`.
7. Commit the whole run as one commit (`vault: curate <slug>`), body listing
   the decisions and any sources checked, and push.
