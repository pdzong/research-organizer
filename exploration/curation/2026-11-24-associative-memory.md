# Curation: associative-memory, 2026-11-24

First run of `/curate`, used as the trial of `curation-policy.md`.

## Summary

- Before: 3,095 words at reading depth (budget 3,000). Over budget on L0
  (68/60 words), Q2 (507 words), Q3 (580 words, 9 bullets), and one extra
  section at reading depth (the 2026-W47 TANSAR section).
- Applied automatically: one Fold and two Demotes (below). After them:
  3,026 words, and Q3 is at 540 words.
- Waiting for approval: 9 proposals. If all are approved, the estimate is
  about 2,650 words at reading depth, with every question except Q2 within
  budget.
- No claim in the card is contradicted by a later source, so there are no
  Supersede proposals. Disproved material would have gone to the card's
  `## Superseded` section, not been removed.
- Tool checks this run:
  - KATA (arXiv:2607.17419), full text: the claims hold.
  - KronLSTM (arXiv:2610.26834), full text: the name and the JKU/NXAI
    affiliation hold.
  - arXiv metadata for the four adoption-list papers.

## Core ideas (approve first)

Proposed `## Core ideas` section, placed after L0:

1. Attention, linear attention and Hopfield networks are one operation:
   associative memory. One modern Hopfield update is exactly one attention
   step. `[proven]`
2. A fixed-size memory has a ceiling on arbitrary recall. Storing `n`
   arbitrary `b`-bit associations needs at least `n · b` bits, and a `d × d`
   linear map is exact for at most `d` keys. `[proven]`
3. Real, correlated keys reach that ceiling far earlier than random keys.
   Interference is set by the geometry of the keys, not only the size of the
   memory. `[proven, for unit keys]` and `[empirical]`
4. "Exponential capacity" in modern Hopfield networks comes from keeping
   every pattern separately. Exact recall therefore costs memory that grows
   with what is stored, which is the KV-cache side of the trade-off.
   `[proven]` and `[interpretation]`
5. Richer write rules (the delta rule, least squares, an MLP state, sparse
   slots, kernel features) mostly buy a bigger or cheaper state, not a new
   frontier. Most of the gain shrinks when the state is matched.
   `[empirical, self-reported]`
6. Read sharpness `β` decides between exact lookup and blending, and a `β`
   tuned at one size fails as the number of items grows. `[proven]` limit
   and `[empirical, one task family]`

## Proposals

| # | Verdict | Unit | Judgment | Destination | Risk |
|---|---|---|---|---|---|
| 1 | Condense | L0 (68 words) | central, strong; over budget | L0 rewritten to about 50 words (draft below) | medium |
| 2 | Condense | Q3: "Dense associative memories", "Modern continuous Hopfield networks" and "'Exponential capacity' counts something different" | central, strong; three bullets make one point (core idea 4) | one bullet with both labels; Q3 goes from 9 to 7 bullets | low |
| 3 | Condense (cross-card) | Q2: Toaster's state-matched numbers (15.79 / 15.69 / 16.00) | central, adequate; the full table is already on [test-time training](../cards/test-time-training.md) | one line ("about two-thirds of the gain comes from the larger state") plus a link | low |
| 4 | Condense | Q7: "Sparse addressing plus delta-rule writes" repeats the SDM/FwPKM explanation from Q2 | supporting; duplicate | keep only the mixture-of-experts link | low |
| 5 | Keep + sharpen | Q2: KATA bullet | was weak (abstract only), now adequate (full text) | add: "KATA-M1 holds a 266,240-entry state against 8,192 for a Gated DeltaNet with the same parameters (d = 64), so its gain is again bought with state." L4 row 15 becomes "yes (full text)". The bullet then supports core idea 5 instead of looking like a counterexample. | low |
| 6 | Close + merge | Open questions 1 and 2 (delta rule versus Hebbian capacity; delta rule versus correlated keys) | same experiment asked twice | one question: "At matched state, how many pairs does a delta-rule memory hold against a Hebbian one, with random and with semantically correlated keys? (TANSAR bounds the Hebbian side: 58 against 257 pairs.)" Also update `INDEX.md`. | low |
| 7 | Archive | Q6: "Hopfield layers as a drop-in module" | peripheral; no source given | `## Archive` | low |
| 8 | Verify | Q6: "Research activity in 2026": affiliations "from alphaXiv metadata, author lists not checked" | supporting, weak | KronLSTM is now checked (JKU and NXAI). Check GDN-2, Erase-then-Delta and Kalman Delta Networks the same way, then drop the caveat. | low |
| 9 | Verify | L3: the `0.144` replica-symmetry-breaking constant (already moved down, still unverified) | supporting, weak | find and read a primary source, or archive it at the next run | low |

Draft for proposal 1 (L0):

> Attention, linear attention and Hopfield networks are all associative
> memories. Packing everything into one fixed matrix is cheap but holds only
> about as many clean associations as its dimension. Keeping every item
> separately, as a KV cache does, gives exact recall at a memory cost that
> grows with every item.

Considered and kept:

- Q4 "Tropical (max-plus) algebra" lineage. It is peripheral, but it is a
  grounded lineage link, which the method asks for.
- Q4 "Feed-forward layers" (Geva et al.). It supports the "three memories"
  combination in Q7.
- Four papers cited in Q6 but not in L4 (GDN-2, Erase-then-Delta, KronLSTM,
  Kalman Delta Networks). They are adoption signals, not reading material, so
  no L4 rows are proposed.

## Applied automatically

All three only move sentences, and leave a pointer behind.

- **Fold:** the extra section "Capacity under correlated keys (from the
  2026-W47 radar)" became a paragraph in L2. The crosstalk bound it repeated
  from Q3 now appears once, in Q3.
- **Demote:** in Q3, the unverified `0.144` refinement of the Hopfield
  constant moved to L3.
- **Demote:** in Q3, the two limits behind the zero-temperature read moved
  to L3. Q3 keeps the claim and its source.

## Verify queue

- Proposals 8 and 9 above.
- Ramsauer et al.'s claim that early heads average and later heads are
  metastable is the only source for that point. Check whether later work on
  pretrained LLMs confirms it.

## Noticed while checking (not curation; for the next radar or update)

- KronLSTM (arXiv:2610.26834, full text) reports that in sliding-window
  hybrids, the baseline recurrent layers retrieve needles mostly when the
  needle is inside the attention window. Accuracy tracks the fraction of the
  context the window covers, "suggesting limited reliance on the recurrent
  architecture's memory". This bears on the open question "how small can the
  recurrent state get" (1.5B models, single paper, `[empirical,
  self-reported]`).

## Decisions

Pending.
