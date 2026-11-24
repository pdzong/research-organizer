# Curation policy

How `/curate` keeps the cards clear as they grow. The goal is a short,
on-topic reading layer (L0 to L2), not a smaller vault. **Curation never
deletes content.** It decides where each piece belongs: in the reading layer,
deeper in the card, in another card, or on the card's shelf (Superseded or
Archive). Git history keeps every earlier version as well.

## The spine: core ideas

Every card has a `## Core ideas` section after L0: three to six claims, each
with its evidence label. Everything else in the card is judged against it.

- `/curate` proposes the core ideas on its first run over a card. They take
  effect only after the user approves them.
- Changing a core idea later always needs approval, because it changes what
  the card is about.
- Open questions count as part of the spine. Material that bears on an open
  question is relevant even if it serves no core idea yet.

## Units

Curation judges units, not whole sections:

- one top-level bullet, with its nested bullets;
- one paragraph;
- one L4 source row;
- one open question.

## Two separate judgments

Relevance and grounding are scored separately. Mixing them would either drop
good research that sits off to the side, or keep weak work because it is on
topic.

**Relevance** (to the spine):

- **Central:** supports, challenges or bounds a core idea, or answers an open
  question.
- **Supporting:** context the central units need (a definition, a lineage
  link, a measurement detail).
- **Peripheral:** true and grounded, but no core idea or open question
  depends on it.
- **Elsewhere:** it answers another card's question better than this one's.

**Grounding** (of the claim, from its source and label):

- **Strong:** `[proven]`, or `[empirical]` from a full-text read with matched
  baselines, or replicated by an independent group.
- **Adequate:** `[empirical]` from a full-text read, one group, reasonable
  controls; or `[proven, if X]` with a standard assumption.
- **Weak:** abstract only, title only, `(unverified)`, self-reported without
  matched baselines, a single small-scale run, or a claim whose source does
  not say what the card says.
- **Contradicted:** a later source of equal or stronger grounding reports the
  opposite, or the claim was retracted or corrected.

Signals for research quality, gathered with tools, not guessed:

- How the source was checked (full text, abstract, metadata).
- Matched comparisons: equal compute, parameters, state bytes or samples.
- Independent replication or contradiction: Semantic Scholar citations (Asta
  `get_citations`) that reproduce, extend or refute the result.
- Venue or review status, as a weak signal only. Preprints are normal here.
- Reproducibility: code and weights released, or key details withheld.

Citation counts on their own are not a quality signal. Recent papers have few
citations by definition.

## Verdicts

| Relevance | Grounding | Verdict |
|---|---|---|
| central or supporting | strong or adequate | **Keep** (maybe **Condense**) |
| central | weak | **Verify**: stays, flagged, checked with tools on the next run |
| any | contradicted | **Supersede**: moves to the shelf with the replacing result |
| peripheral | strong or adequate | **Archive**, or **Demote** to L3/L4 if it is detail behind a central claim |
| peripheral | weak | **Archive** |
| elsewhere | any | **Move** to the other card, with a link left behind |

Other verdicts:

- **Condense:** two or more units say the same thing, or one unit is longer
  than its depth level needs. Merge into one, keeping every source.
- **Demote:** detail at the reading depth that belongs in L3 (math) or L4
  (sources). Move it down a level with a one-line pointer left behind.
- **Fold:** an extra section at reading depth (for example "Evidence from the
  2026-W47 radar update") is split into the seven questions or L2 it belongs
  to. Radar additions should not pile up as their own sections.
- **Close:** an open question that a source now answers is checked off
  (`- [x]`) with the answer and source, not removed.

Disproved ideas are always **Supersede**, never Archive and never deleted. A
claim that turned out wrong, together with the evidence that settled it, is
research worth keeping.

## Budgets

These trigger a curation proposal. They do not force cuts. A card over budget
gets a proposal, and the user decides. `curation/measure.py` checks them.

| Part | Budget |
|---|---|
| L0 | 60 words |
| Core ideas | 3 to 6 |
| L1 | 300 words |
| Each of the seven questions | 350 words or 8 top-level bullets |
| L2 | 900 words |
| Everything at reading depth (L0 to L2, including extra sections) | 3,000 words |
| Open questions (unanswered) | 8 |

L3, L4, the shelf and the log have no budget.

## Approval tiers

**Applied without asking** (listed in the report as already done):

- exact or near-exact duplicates inside one card, merged with every source
  kept;
- formatting and broken internal links;
- adding a missing L4 row for a paper the card already cites as evidence
  for a claim (not for papers named only as adoption signals);
- Demote and Fold that keep every sentence intact and only move it.

**Needs approval** (proposed, numbered, not applied):

- Core ideas, first time or any change;
- Condense when wording changes;
- Supersede, Archive, Move, Close;
- any change to L0 or to a card's one-line summary in `INDEX.md`;
- dropping an evidence label to a weaker one, or raising it.

**Never:**

- deleting a unit outright;
- changing a claim's evidence label without a tool check behind it;
- touching a source row's verification state without re-verifying it.

## The proposal report

Each run writes `curation/YYYY-MM-DD-<scope>.md`:

1. **Summary:** cards checked, how far each is over budget, what changed
   automatically, and how many items wait for approval.
2. **Core ideas:** proposed or changed spines, for approval first, because
   the other verdicts depend on them.
3. **Proposals:** numbered items. Each gives the verdict, the unit (quoted
   briefly or located by section), the relevance and grounding judgments, the
   evidence for them (tool checks, sources), the destination, and a risk
   level (low, medium, high).
4. **Applied automatically:** what was done without asking.
5. **Verify queue:** weak but central claims and what check would settle
   them.

The user answers with item numbers, for example "approve 1-6, 9; reject 7;
8 as archive instead". Approved items are applied, each touched card gets a
log line (`curated: ...`), `INDEX.md` is updated, the report records the
decisions, and the run is committed as one commit so it can be reverted in
one step.

## Optional keeper review

With `--challenge`, a separate agent reads every proposed Supersede and
Archive item without seeing the reasons, and argues for keeping it. Items it
makes a good case for are marked "contested" in the report. This costs more
tokens; use it for large runs or when a card's core ideas change.
