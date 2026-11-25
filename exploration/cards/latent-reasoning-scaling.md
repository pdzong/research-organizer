# Can in-context latent reasoners like BDH-CQ scale to frontier models?

Status: draft
Last updated: 2026-11-25
Related: [latent reasoning](latent-reasoning.md) ·
[looped transformers](looped-transformers.md) ·
[associative memory](associative-memory.md) ·
[attention efficiency](attention-efficiency.md)

## L0 Headline

Not shown yet. BDH-CQ's claim of scaling from 1B to 600B parameters is one
sentence with no data, and the paper lists it as untested. Outside
evidence points both ways. At 1 to 3B, looping buys reasoning per parameter.
But it adds no stored knowledge, and latent chains in pretrained models fall
behind written ones as size grows.

## Core ideas

Proposed on 2026-11-25. They take effect only after the user approves them
(see `curation-policy.md`).

1. **The scaling claim has no data behind it.** BDH-CQ reports one 150M
   model. The 1B–600B sentence has no figure or table, and the recipe is
   proprietary. `[empirical: full-text read]`
2. **Reasoning depth and knowledge are separate budgets.** Looping improves
   how a model uses what it knows, not how much it stores (about 2 bits per
   parameter either way). A small latent reasoner cannot stand in for the
   parameters a frontier model uses for knowledge. `[empirical,
   self-reported, synthetic data]`
3. **Latent depth wins clearly only when the model is built or trained for
   it,** and mainly on depth extrapolation in synthetic or puzzle tasks.
   `[empirical, small scale]`
4. **In pretrained language models above about 1B, latent chains trail
   written ones, and the gap grows with size,** unless each latent step is
   supervised against a written chain. `[empirical, self-reported, math
   only]`
5. **A fixed-size memory caps in-context learning.** It cannot hold
   arbitrarily long or detailed context. `[proven]` for arbitrary recall.

## L1 Intuition

Analogy: **a chess prodigy raised only on puzzles.** BDH-CQ is like a child
who learned to calculate brilliantly on puzzles. Shown three examples of a
new kind of puzzle, they get the rule and solve the next one in their head,
fast and cheap. A frontier model is more like a well-read adult who thinks
out loud. Scaling BDH-CQ means sending the prodigy through a whole library
(pretraining) without losing the habit of silent calculation.

The evidence so far: the library is where silent calculation tends to get
lost (core idea 4). Calculation does not replace reading (core idea 2). And
a working memory can only hold so many examples at once (core idea 5).

Where the analogy breaks:

- **BDH is a general architecture, not a puzzle machine.** Its 2025 paper
  trains it on language and translation (core idea 1 is about the reasoning
  variant, not the base model).
- **Frontier models also compute silently** within each token. The
  difference is how much depth they can add at test time without writing.
- **"Losing the habit" is a training effect, not a law.** No theorem says
  pretraining must destroy latent reasoning; see Boundary.

## The seven questions

### 1. Scarce resource

- **Pretraining compute for a new model family.** If latent reasoning must
  be built in from scratch (core idea 3), scaling it means a full frontier
  pretraining run of an unproven architecture, not a fine-tune.
- **Serial depth at inference.** Each latent step is a full pass through
  the recurrent block. It saves output tokens, but the passes cannot run in
  parallel.
- **State bytes.** BDH-CQ keeps the task in a recurrent memory with no
  growing cache. That is cheap, but its size bounds what it can hold.

### 2. Trade-off

Does the work move the frontier, or pick a different point on it?

- **At 150M on ARC: it moves the cost frontier** (29.5% pass@2 at about
  $0.0007 per task), not the accuracy frontier. See
  [latent reasoning](latent-reasoning.md#bdh-cq-in-context-learning-plus-recurrent-latent-reasoning-pathway-2026).
  `[empirical, self-reported]`
- **At 1–3B with a looped language model: more reasoning per parameter,
  paid in FLOPs.** Ouro's 1.4B and 2.6B models match 4B and 8B standard
  transformers on most benchmarks, a claimed 2–3x parameter efficiency
  (Zhu et al. 2025, arXiv:2510.25741). Each loop costs another forward
  pass, and the comparison is not FLOP-matched. `[empirical, self-reported]`
- **At 3B with a latent chain grafted onto a pretrained model: parity at
  lower latency, when supervised.** LOTUS reports near-parity with a
  written chain on GSM8K and 2.5–6.9x less time spent thinking (Fan, Svete
  & Lee 2026, arXiv:2606.31779). That is a latency gain, not an accuracy
  gain. `[empirical, self-reported]`

None of these shows a latent method beating a written chain at matched
compute and at scale.

### 3. Boundary

- `[proven]` **A fixed memory has a recall ceiling.** To recall `n`
  arbitrary `b`-bit associations a memory needs at least `n·b` bits.
  Fixed-state models provably need state that grows with the length of
  what they copy (Jelassi et al. 2024, arXiv:2402.01032). The details are
  on the [associative memory](associative-memory.md) card. This bounds
  BDH-CQ's memory `S`, whose size the paper does not disclose.
- `[empirical, self-reported, synthetic]` **Looping does not add knowledge
  capacity.** Looped and non-looped models store about 2 bits per
  parameter. Looping improves manipulation and multi-hop questions
  (Ouro, synthetic biographies). On MMLU, going from 1 to 4 loops raises
  elementary mathematics by 155.6% but global facts by only 8.3% (Ouro,
  Table 15).
- `[empirical, self-reported]` **The latent-chain gap grows with scale.**
  The LOTUS abstract states that existing latent chain-of-thought methods
  (CODI, SIM-CoT) underperform written chains beyond 1B parameters, and
  that the gap widens with size. Evidence: GPT-2, Llama-3.2 1B and 3B, on
  GSM8K-family math only.
- `[empirical]` **Depth extrapolation runs out.** BDH-CQ fails ordering
  beyond 6 objects and nesting at depth 5. A latent loop retrofitted into
  Qwen2.5-0.5B holds up to about 1.5x its training depth, then falls
  (Shapiro 2026, arXiv:2608.11233; numbers from a summary, unverified).
  Ouro degrades beyond its 4 trained loops.
- `[interpretation]` **No known result rules out scaling.** Every obstacle
  above is empirical or a capacity bound that a larger state can relax.

### 4. Lineage

- **Recurrent depth and adaptive computation:** Universal Transformers and
  their successors. See [looped transformers](looped-transformers.md).
- **Fast weights and Hebbian memory:** BDH stores context as a synaptic
  state written during the forward pass, as in
  [associative memory](associative-memory.md).
- **Huginn** (Geiping et al. 2025, arXiv:2502.05171): the first open 3.5B
  recurrent-depth language model, trained on about 800B tokens.
- **BDH** (Kosowski et al. 2025, arXiv:2509.26507): the base architecture.
  Its abstract reports parity with GPT-2 on language and translation from
  10M to 1B parameters, with the same data.

### 5. Measurement

What would settle the question, in order of cost:

- **Publish the curves.** Loss against compute for BDH and a matched
  transformer at 1B and above, with the latent-effort curve (accuracy
  against latent steps) at each size. If effort stops helping at larger
  sizes, latent reasoning did not survive pretraining.
- **Text demonstrations.** Does the memory `S` learn a task from textual
  examples? The paper lists this as its next test (Sec. 9.1).
- **Matched compute against a written chain.** Same parameters, same FLOPs,
  on math and code, with a deletion test on the latent steps.
- **Memory stress test.** Multi-query associative recall (MQAR) or
  needle-in-a-haystack at growing context lengths, to find where `S` runs
  out.
- **A caveat on the current dose-response.** BDH-CQ's own minimum-effort
  setting solves 111 of 400 tasks against 118 at the standard setting, a
  difference the paper calls statistically unresolved (McNemar p = 0.167).
  The low/medium/high effort result (21%, 27%, 29.5%) is the stronger
  evidence.

### 6. Adoption

- **Pathway** says it is pretraining at 1B to 600B (BDH-CQ Sec. 9.2). Press
  reports a funding round at a $500M valuation to scale the architecture
  (Unite.AI, unverified). No larger model or result is public.
- **The 29.5% ARC score was reproduced by co-authors** from Bielik AI and
  NYU. That is a different institution, not an independent group.
- **Open looped models exist:** Ouro 1.4B and 2.6B (trained on 7.7T tokens)
  and Huginn 3.5B are released. Nothing similar is open for BDH-CQ.
- **No frontier lab ships a latent-first reasoner** in the sources read.
  `[interpretation]`

### 7. Combination

- **Latent workspace plus written steps.** BDH-CQ's authors suggest it
  themselves (Sec. 9.1). Latent loops would handle depth, and text would
  handle checking and oversight.
- **Hybrid memory.** A fixed recurrent memory for the gist of the context
  plus a few exact-access attention layers, as on the
  [attention efficiency](attention-efficiency.md) card. This addresses
  core idea 5.
- **Step-grounded training.** LOTUS-style supervision of each latent step
  against a written chain, which addresses core idea 4.
- **Looping for reasoning, parameters for knowledge.** By core idea 2, a
  scaled design would need both, not one in place of the other.
  `[speculation]`

## L2 Mechanism

### What scaling would have to preserve

BDH-CQ works through three parts, and each must survive at scale:

| Part | At 150M (ARC) | Evidence at scale |
|---|---|---|
| Base model quality (loss vs. compute) | Not reported for BDH-CQ | BDH: GPT-2 parity up to 1B (abstract only). 1B–600B: claimed, no data. |
| Memory `S` learns the task from demonstrations | Works with 3 demonstrations; 96/96 on held-out color bindings | Text demonstrations untested. Capacity of `S` undisclosed. |
| Workspace `H` uses its latent steps | Accuracy rises with latent effort | Not reported. In pretrained language models, latent steps tend to collapse (see [latent reasoning](latent-reasoning.md), L2). |

### What other groups found, by route

There are three ways to get latent reasoning into a large model, and the
evidence differs by route:

1. **Train from scratch for latent reasoning.**
   - Small models on synthetic graphs: latent models generalize to longer
     reasoning chains than written-chain or pause-token models. A sparse
     recurrent search circuit does the work (Cheng & Zhang 2026,
     arXiv:2609.35643, abstract only).
   - Looped language models at 1–3B (Ouro, Huginn) gain most on math and
     multi-step tasks, and little on facts.
   - This is the route BDH-CQ takes. It works, but every published case
     beyond 150M is a looped transformer, not BDH.
2. **Retrofit a loop into a pretrained model.**
   - On Qwen2.5-0.5B, a retrofitted loop is used, extrapolates past its
     training depth and keeps the original ARC-Easy/Challenge scores, on
     generated tasks (Shapiro 2026, single author, single seed for key
     results).
   - This softens the "retrofits fail" reading, but only on synthetic tasks.
3. **Graft a latent chain onto a pretrained model** (Coconut, CODI).
   - Trails written chains beyond 1B, with the gap growing (LOTUS).
   - LOTUS closes most of the gap at 3B by looping the whole model and
     supervising each latent position against a written-chain token.

`[interpretation]` Taken together: latent computation scales when it is
part of the architecture and training from the start, and when its steps
get a learning signal. Grafting it on afterward without supervision is
what fails. BDH-CQ is on the promising route, but the unknowns are its
memory, which nobody outside Pathway has measured, and whether its latent
steps keep working after language pretraining.

## L3 Math

Planned outline (fill with `/deepen latent-reasoning-scaling L3`):

- The counting bound for a fixed state, and what size `S` would need for a
  given number of demonstrations.
- Bits-per-parameter knowledge capacity (the Physics of Language Models
  line of work) and why looping leaves it unchanged.
- FLOP accounting for looped models: when does `R` loops of a small model
  cost less than one pass of a larger one?

## L4 Sources (reading order)

| # | Source | Why read it | Verified |
|---|---|---|---|
| 1 | Engdahl, Kosowski, Chorowski et al. 2026, "BDH-CQ: In-Context Learning with Recurrent Latent Reasoning", arXiv:2608.09888 | The claim under test; Sec. 9 on scaling and future work. | yes (full text) |
| 2 | Kosowski, Uznański, Chorowski, Stamirowska & Bartoszkiewicz 2025, "The Dragon Hatchling", arXiv:2509.26507 | Base architecture; GPT-2 parity from 10M to 1B. | yes (abstract) |
| 3 | Zhu et al. 2025, "Scaling Latent Reasoning via Looped Language Models" (Ouro), arXiv:2510.25741 | Largest open looped models; knowledge storage versus manipulation. | partly (intro and appendix verbatim; benchmark tables from a summary) |
| 4 | Fan, Svete & Lee 2026, "Bridging the Gap Between Latent and Explicit Reasoning with Looped Transformers" (LOTUS), arXiv:2606.31779 | The latent-chain gap grows with scale; step-grounded fix. | partly (abstract and Sec. 3; table numbers unverified) |
| 5 | Shapiro 2026, "Retrofitting Recurrent Depth into a Pretrained Language Model", arXiv:2608.11233 | Retrofitting a loop at 0.5B, on synthetic tasks. | partly (abstract and first part) |
| 6 | Cheng & Zhang 2026, "Not All Thinking is Created Equal", arXiv:2609.35643 | From-scratch latent models learn a search circuit. | abstract only |
| 7 | Geiping et al. 2025, "Scaling up Test-Time Compute with Latent Reasoning: A Recurrent Depth Approach", arXiv:2502.05171 | Huginn 3.5B. | yes (full text, via the looped-transformers card) |
| 8 | Jelassi et al. 2024, "Repeat After Me: Transformers are Better than State Space Models at Copying", arXiv:2402.01032 | The fixed-state copying bound. | yes (via the associative-memory card) |
| 9 | Unite.AI, "Pathway Raises New Funding at $500M Valuation to Scale Post-Transformer AI", https://www.unite.ai/pathway-raises-new-funding-at-500m-valuation-to-scale-post-transformer-ai/ | Press report on the scaling plan. | no (search result only) |

## Open questions

- [ ] Will Pathway publish loss and latent-effort curves for BDH or BDH-CQ
      at 1B and above, against a matched transformer?
- [ ] Can BDH-CQ's memory learn tasks from textual demonstrations?
- [ ] At matched FLOPs on math or code, does a BDH-style latent reasoner
      beat a same-size transformer that writes its chain?
- [ ] How much context can a BDH-CQ memory hold before recall fails
      (MQAR-style test)?
- [ ] Does step-grounded latent training (LOTUS) keep parity with written
      chains above 3B, or does the gap reopen?
- [ ] Does looping stay neutral for knowledge and positive for reasoning
      at 7B and above?

## Superseded

## Archive

## Log

- 2026-11-25: created by `/investigate` on whether BDH-CQ-style latent
  reasoning scales.
  - Read BDH-CQ Sec. 9 in full: the 1B–600B claim has no data.
  - Added Ouro, LOTUS, Shapiro and Cheng & Zhang (partly read or abstract
    only; see L4), plus BDH and press coverage.
  - alphaXiv was not connected in this session; sources were found with web
    search and read from arXiv HTML.
  - Core ideas proposed, awaiting approval.
