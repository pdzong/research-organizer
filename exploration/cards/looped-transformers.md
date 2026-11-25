# What do looped (recurrent-depth) transformers buy?

Status: draft
Last updated: 2026-11-25
Related: [latent reasoning](latent-reasoning.md) ·
[latent reasoning at scale](latent-reasoning-scaling.md) ·
[associative memory](associative-memory.md) ·
[test-time training](test-time-training.md) ·
[state space models](state-space-models.md)

## L0 Headline

A looped transformer reruns one block of layers several times per token. It
gets depth without adding parameters, but not without adding compute. At
equal compute it matches a deeper model on reasoning but loses on
memorization. Depth is provably powerful. Whether loops beat a written chain
of thought at equal cost is open.

## Core ideas

Proposed on 2026-11-25. They take effect only after the user approves them
(see `curation-policy.md`).

1. **Looping saves parameters, not FLOPs.** At matched FLOPs, a plainly
   looped 1B model loses on perplexity and closed-book QA. It matches or
   beats the deeper model on reasoning primitives and sometimes on math.
   One residual redesign (Loopback) claims a small loss win at matched
   compute. `[empirical, one group each, up to 3B]`
2. **Loops help reasoning, not memorization.** Looping leaves knowledge
   storage at about 2 bits per parameter. It improves how stored knowledge
   is combined. `[empirical, self-reported, two groups]`
3. **Depth is provably powerful.** Transformers of depth `Θ(log n)` recognize
   regular languages and solve graph connectivity, which fixed-depth ones
   cannot. `T` loops can simulate `T` steps of chain of thought.
   `[proven, if standard complexity conjectures]` and `[proven, under the
   paper's assumptions]`
4. **In small recursive reasoners, the refinement loop and the training
   carry the gains, not elaborate architecture.** `[empirical, independent
   analysis]`
5. **Each loop costs a full pass at inference.** Depth-adaptive tricks
   (routing, early exit, late entry) claim 2 to 8 times throughput gains
   back. `[empirical, self-reported]`

## L1 Intuition

Analogy: **one machine and several passes, against a production line.** A
standard transformer is a production line: each layer is a different machine,
and the part passes each one once. A looped transformer is a workshop with
one machine. You feed the part through it several times, and each pass
refines it further.

- The workshop costs much less to buy (fewer parameters). Each part still
  takes as long to make (each pass costs the same compute).
- Repeated passes suit work that is naturally iterative, like following
  links one hop at a time or carrying digits in addition.
- A single machine has fewer specialized tools on the shelf. It is worse at
  jobs that need many different stored facts.
- You can choose how many passes to make for each part: more for hard
  parts, fewer for easy ones.

Where the analogy breaks:

- **The passes are not identical.** The part changes between passes, and
  most designs re-inject the original input at every pass. So the same
  weights can do different work at different depths.
- **A production line can also iterate.** A deep standard transformer can
  learn the same iterative algorithm. Looping is an inductive bias toward
  it, not a capability the line lacks (core idea 1).
- **Extra passes beyond what was trained can hurt.** A real machine does
  not degrade when you use it more; looped models do (Boundary).

## The seven questions

### 1. Scarce resource

- **Parameters and memory for weights.** This is what looping saves. A
  `k`-layer block looped `L` times stores the weights of `k` layers.
- **FLOPs and latency per token.** Each loop costs a full pass through the
  block, at training and at every decoding step. Looping trades cheap
  storage for serial compute.
- **KV cache.** Each loop can produce its own keys and values, so the cache
  can grow with depth. Mixture-of-Recursions caches only tokens active at
  each depth, or reuses the first loop's cache (Bae et al. 2025,
  arXiv:2507.10524).
- **Training memory.** Backpropagating through many loops is expensive.
  Huginn and TRM backpropagate through only the last few loops
  (Geiping et al. 2025, arXiv:2502.05171; Jolicoeur-Martineau 2025,
  arXiv:2510.04871).

### 2. Trade-off

Does the work move the frontier, or pick a different point on it?

- **Matched parameters: loops win clearly.** In every Saunshi et al. setting
  a looped model beats the same-size model run once (arXiv:2502.17416).
  Ouro's 1.4B and 2.6B match 4B and 8B standard transformers on most
  benchmarks (Zhu et al. 2025, arXiv:2510.25741). The gain is on reasoning:
  Ouro 1.4B beats Qwen3-4B on MATH500 (82.4 vs 59.6) and trails it on MMLU
  (67.4 vs 73.2) (Table 7). `[empirical, self-reported]`
- **Matched FLOPs: a different point, not a better one.** For a 1B language
  model on 250B tokens (Saunshi et al., Table 3):
  - Perplexity: 7.40 for the 24-layer model, against 7.90 for 12 layers
    looped twice.
  - Closed-book QA: 11.2 against 9.3.
  - Reasoning primitives: 47.5 against 51.2.
  - Math: 29.3 against 34.3. The gain on math is not consistent across all
    loop settings.
- **Matched training FLOPs with per-token depth: close to a tie.**
  Mixture-of-Recursions beats a vanilla model at 360M but trails it
  slightly at 1.7B. These numbers come from a summary and are unverified.
- **One claimed matched-compute win, by a small margin.** The Loopback
  Transformer matches training tokens and executed depth, which also
  matches FLOPs to within 0.1%. It reaches lower loss than a standard
  transformer with 40–75% of its parameters, from 191M to 3B (Ouyang et al.
  2026, arXiv:2611.07226). `[empirical, self-reported]`
  - The margins are small: 0.005 to 0.039 nats. At 1.4B and 3B there is
    one run per arm. At 191M the win over the standard model is not
    consistent across three seeds (Sec. E.1).
  - Downstream gains are near noise. The 13-task mean moves from 46.3% to
    46.5% at 1.4B and from 48.6% to 49.5% at 3B, with a standard error of
    0.4 points (Table 9).
  - Fewer parameters do not mean faster: 3B training throughput is 6% lower.
  - `[interpretation]` Why it differs from Saunshi et al.:
    - Residual design: a plain loop does about 0.07 nats worse than
      Loopback at 191M.
    - Less sharing: Loopback loops only a middle stack and keeps 68–75% of
      the parameters at 1.4B and 3B. Saunshi's 12 ⊗ 2 keeps 50%.
    - Shorter training: 20 tokens per parameter, against about 250 in
      Saunshi. The paper does not test any of these explanations.

Verdict: looping moves the parameter-efficiency frontier. For language
modelling at matched compute, the only claimed win is Loopback's small one
from a single group, with single runs at scale.

### 3. Boundary

- `[proven, if standard complexity conjectures hold]` **Log depth beats
  fixed depth.** Uniform transformers of depth `Θ(log n)` recognize regular
  languages and solve graph connectivity. Fixed-depth transformers cannot
  (Merrill & Sabharwal 2025, arXiv:2503.03961, NeurIPS 2025). The abstract
  adds that growing depth is more efficient than growing width or chain-of-
  thought steps for these problems. Looping is a cheap way to get that
  depth. (Abstract read; exact assumptions not checked.)
- `[proven, under the paper's assumptions]` **Loops can simulate a chain of
  thought.** Theorem 5.4 of Saunshi et al.: take any `L`-layer transformer,
  a fixed input length `n` and `m` chain-of-thought steps. A looped
  transformer with `L + O(1)` layers, `Ω(log(n+m))` extra embedding width
  and a constant number of extra heads reproduces the output. It runs `m`
  loops over the input plus `m` padding tokens, at finite precision.
  - Each loop is a whole model, so this shows loops are as expressive as
    chain of thought. It does not show they are cheaper or learnable.
  - The same paper shows that `⌈log₂ n⌉` loops of one layer compose `n`
    group elements. `⌊log₂ p⌋ + 2` loops solve `p`-hop induction, which
    matches a known lower bound for non-looped depth (Theorem 5.1,
    Corollary 5.3).
- `[proven, constructive]` **A fixed looped network is a programmable
  computer.** A 13-layer looped transformer can run programs given in its
  input (Giannou et al. 2023, arXiv:2301.13196). This shows expressivity,
  not learnability.
- `[empirical, self-reported, synthetic]` **Looping adds no knowledge
  capacity.** Looped and non-looped models store about 2 bits per
  parameter (Ouro, Sec. 6.1; GPT-2-style models from 1M to 40M on synthetic
  biographies).
- `[empirical]` **Extrapolating past trained depth runs out.** Ouro peaks
  at its 4 trained loops. Base-model scores slip a few points by 8 loops,
  and Ouro-2.6B-Thinking falls from 76.4% to 39.3% on OlympiadBench
  (Tables 10–13). Loopback degrades less than a plain loop when visits
  are added, but extra visits never lowered its loss. A loop retrofitted
  into a 0.5B model holds to about 1.5x its trained depth (see
  [latent reasoning at scale](latent-reasoning-scaling.md)).

### 4. Lineage

- **Adaptive Computation Time** (Graves 2016, arXiv:1603.08983): an RNN
  learns how many steps to take per input. Almost every looped model with
  a halting rule descends from it.
- **Universal Transformers** (Dehghani et al. 2018, arXiv:1807.03819, ICLR
  2019): one block shared across depth, with per-position dynamic halting.
  Turing-complete under certain assumptions.
- **Iterative algorithms and fixed points.** A loop with input injection is
  an iterated map, like gradient descent or message passing. Looped
  transformers learn in-context learning algorithms with under 10% of the
  parameters of a standard transformer (Yang et al. 2023, arXiv:2311.12424,
  ICLR 2024). `[interpretation]`
- **Recurrent depth in language models:** Huginn 3.5B, then Ouro 1.4B and
  2.6B.
- **Tiny recursive reasoners on puzzles:** HRM (27M, Wang et al. 2025,
  arXiv:2506.21734), then TRM (7M, 2 layers, 45% on ARC-AGI-1 and 8% on
  ARC-AGI-2). Pathway's BDH-CQ also loops a latent workspace; see
  [latent reasoning](latent-reasoning.md).

### 5. Measurement

- **Always report three baselines:** the same model run once (matched
  parameters), a deeper model (matched FLOPs) and a written chain of
  thought at matched inference FLOPs. Most papers report only the first.
- **Split tasks by type.** Saunshi et al. show that the average hides
  opposite effects: memorization drops, reasoning rises.
- **Loop-count sweeps beyond the trained range,** to separate learned
  iteration from a fixed-depth circuit.
- **Ablate the outer loop separately from the architecture.** The ARC Prize
  analysis of HRM is the model to follow:
  - The hierarchical design had minimal impact; a same-size transformer
    came within about 5 points.
  - Going from 1 to 2 outer refinement loops added 13 points.
  - Training only on the evaluation tasks reached 31% pass@2, against 41%
    with the full data, so cross-task transfer is limited.
  - Data augmentation was critical.
  - Source: ARC Prize, "The Hidden Drivers of HRM's Performance on
    ARC-AGI", https://arcprize.org/blog/hrm-analysis (2025). `[empirical,
    independent]`
- **What would falsify core idea 1:** a looped model that beats a
  FLOP-matched deeper model on perplexity at 1B or above.

### 6. Adoption

- **Open models:** Huginn 3.5B and Ouro 1.4B and 2.6B have released
  weights. Ouro was trained on 7.7T tokens.
- **Conversion from pretrained models:** Relaxed Recursive Transformers
  turn Gemma 2B into a model with half the parameters. With per-loop LoRA
  and distillation it recovers 58.4% few-shot accuracy against 58.6% for
  the full model (Bae et al. 2024, arXiv:2410.20672, ICLR 2025; numbers
  from a summary).
- **Serving speedups, all self-reported:**
  - Mixture-of-Recursions: up to 2.06x throughput.
  - Late entry, where new tokens skip the early loops: 5.2x greedy-exact on
    Ouro-2.6B and up to 8.4x on Huginn (Jin et al. 2026, arXiv:2611.24576,
    abstract only).
- **Research volume is rising** in 2026 (Loopback, Late Entry, LLoCoT,
  LOTUS). No frontier lab is known to ship a looped model.
  `[interpretation]`

### 7. Combination

- **Looping plus latent chains.** LLoCoT refines a block of latent slots
  with a looped model, then decodes the answer. It matches its written-chain
  baseline on HumanEval and MBPP with about 42x lower reasoning latency
  (Grau García et al. 2026, arXiv:2610.11472, abstract only). LOTUS does the
  same for math; see [latent reasoning at scale](latent-reasoning-scaling.md).
- **Looping plus latent feedback across tokens.** `[interpretation]` A
  looped model pays its extra compute at every decoding step. Latent
  feedback (arXiv:2611.20404) adds about 1.2x training FLOPs and one fed-
  back state per token. The two spend compute in different places and
  could be combined. The paper does not compare itself with looped models.
- **Looping plus a fixed recurrent memory:** BDH-CQ (memory across the
  context, loops in depth). See [associative memory](associative-memory.md)
  for the memory side.
- **Looping as test-time compute.** Adaptive depth is a dial like sampling
  more chains. Whether it is a cheaper dial at equal FLOPs is open.

## L2 Mechanism

### The basic shape

Notation from Saunshi et al.: `(k ⊗ L)` is a block of `k` distinct layers
run `L` times. Its parameters are those of `k` layers; its FLOPs are those
of `kL` layers.

Most language-model designs (Huginn, Ouro) split the network into three
parts:

1. **Prelude:** a few ordinary layers embed the input into a latent state
   `e`.
2. **Recurrent block:** the same layers run `R` times,
   `s_{r+1} = B(s_r, e)`. The input `e` is re-injected at every loop, so
   the state cannot drift away from the question.
3. **Coda:** a few ordinary layers map the final state to output tokens.

### Training

- **Variable loop counts.** Huginn samples `R` at random for each training
  step, so the model works at many depths and can be run deeper at test
  time.
- **Truncated backpropagation.** Gradients flow through only the last few
  loops. This keeps training memory flat. TRM goes further: it runs all
  loops but one without gradients.
- **Deep supervision (TRM, HRM).** The model is run several times in a row
  on the same puzzle. Each run starts from the previous answer and latent
  state, and each is supervised. This outer loop is what the ARC Prize
  analysis found doing most of the work.

### Choosing the depth

- **Fixed:** the same `R` for every token. Simple, and wasteful on easy
  tokens.
- **Learned halting:** a gate decides when to stop, as in ACT. Ouro uses an
  exit gate trained in two stages. First, an entropy penalty with a uniform
  prior over exit steps keeps the gate from collapsing to always-shallow
  or always-deep. Then a second stage, with the language model frozen,
  trains the gate to exit when another loop stops improving the loss
  (Ouro, Sec. 3). TRM uses a
  single binary halting loss.
- **Per-token routing:** Mixture-of-Recursions lets a router choose how
  many loops each token gets. That saves compute, but it complicates the
  KV cache, because tokens that stop early have no keys at deeper loops.
- **Late entry:** new tokens skip the early loops and join the final `K`
  over a fully computed context (Jin et al. 2026).

### Why loops favour reasoning over memorization

`[interpretation]` A reasoning step like "follow one more link" or "carry
one more digit" is the same operation each time, so shared weights fit it
well. Stored facts are not repeated operations. They need distinct
parameters, and looping does not add any. That is consistent with both the
iso-FLOP results (core idea 1) and the knowledge-capacity result (core
idea 2). It is also the same split as in
[latent reasoning at scale](latent-reasoning-scaling.md): loops for
reasoning, parameters for knowledge.

## L3 Math

Planned outline (fill with `/deepen looped-transformers L3`):

- Merrill & Sabharwal's log-depth constructions for regular languages and
  graph connectivity, and the conjectures behind the lower bound.
- Saunshi et al.'s simulation of `T` chain-of-thought steps with `T` loops,
  with its assumptions (now checked; see Boundary) and the proof sketch.
- Iso-FLOP accounting: when do `L` loops of `k` layers beat `kL` layers, in
  a scaling-law fit of loss against depth?

## L4 Sources (reading order)

| # | Source | Why read it | Verified |
|---|---|---|---|
| 1 | Saunshi, Dikkala, Li, Kumar & Reddi 2025, "Reasoning with Latent Thoughts: On the Power of Looped Transformers", arXiv:2502.17416 (ICLR 2025) | The iso-parameter and iso-FLOP comparison; reasoning against memorization; theory. | yes (abstract, Sec. 1–3, Table 8, Sec. 5 theorems and App. B.3, read with alphaXiv; full proofs skimmed) |
| 2 | Merrill & Sabharwal 2025, "A Little Depth Goes a Long Way: The Expressive Power of Log-Depth Transformers", arXiv:2503.03961 (NeurIPS 2025) | Why depth matters, with proofs. | abstract only |
| 3 | Geiping et al. 2025, "Scaling up Test-Time Compute with Latent Reasoning: A Recurrent Depth Approach", arXiv:2502.05171 (NeurIPS 2025) | Huginn 3.5B: prelude, recurrent block, coda. | yes (full text) |
| 4 | Zhu et al. 2025, "Scaling Latent Reasoning via Looped Language Models" (Ouro), arXiv:2510.25741 | The largest open looped models; knowledge storage. | yes (Sec. 1, 3–6, Tables 7–13 and 15, read with alphaXiv) |
| 5 | ARC Prize 2025, "The Hidden Drivers of HRM's Performance on ARC-AGI", https://arcprize.org/blog/hrm-analysis | Independent ablation: the outer loop matters, the hierarchy does not. | yes (read) |
| 6 | Jolicoeur-Martineau 2025, "Less is More: Recursive Reasoning with Tiny Networks" (TRM), arXiv:2510.04871 | A 7M recursive reasoner; ablations of depth and layers. | partly (abstract and method; tables from a summary) |
| 7 | Bae et al. 2025, "Mixture-of-Recursions", arXiv:2507.10524 | Per-token depth and KV caching. | partly (numbers from a summary) |
| 8 | Bae et al. 2024, "Relaxed Recursive Transformers", arXiv:2410.20672 (ICLR 2025) | Converting a pretrained model into a looped one. | partly (numbers from a summary) |
| 9 | Dehghani et al. 2018, "Universal Transformers", arXiv:1807.03819 (ICLR 2019) | The origin of weight sharing across depth. | abstract only |
| 10 | Graves 2016, "Adaptive Computation Time for Recurrent Neural Networks", arXiv:1603.08983 | The origin of learned halting. | abstract only |
| 11 | Giannou et al. 2023, "Looped Transformers as Programmable Computers", arXiv:2301.13196 | Expressivity by construction. | abstract only |
| 12 | Yang, Lee, Nowak & Papailiopoulos 2023, "Looped Transformers are Better at Learning Learning Algorithms", arXiv:2311.12424 (ICLR 2024) | In-context learning with under 10% of the parameters. | abstract only |
| 13 | Wang et al. 2025, "Hierarchical Reasoning Model", arXiv:2506.21734 | HRM, the model the ARC Prize analysis tested. | partly (abstract and intro) |
| 14 | Ouyang et al. 2026, "Loopback Transformer: Towards a Unified View of Residual Looped Transformers", arXiv:2611.07226 | A small matched-compute loss win from 191M to 3B; residual design for loops. | yes (Sec. 1–5, 7–8, Tables 3, 9, 15, App. E.1, read with alphaXiv) |
| 15 | Jin, Li, Xu & Sun 2026, "Late Entry in Looped Language Models", arXiv:2611.24576 | Inference speedups for Ouro and Huginn. | abstract only |
| 16 | Grau García et al. 2026, "From Chain-of-Thought to Loops: Non-Autoregressive Latent Reasoning via Looped Transformers" (LLoCoT), arXiv:2610.11472 | Looped refinement of latent slots for code. | abstract only |
| 17 | Huang, Dwivedi, Ma, Moreno & Liu 2026, "Latent Feedback Is a Compute and Data Amplifier", arXiv:2611.20404 | Feedback across tokens instead of loops in depth; the cost contrast in Combination. | abstract (this card); spot-checked on the latent-reasoning card |
| 18 | Chen, Zhou, Yang & Yang 2026, "Rethinking Fixed-Horizon Latent Reasoning", arXiv:2611.24001 | Overlong latent chains hurt; covers latent chains, not loops. | abstract only |

## Open questions

- [ ] Does the iso-FLOP split (worse memorization, better reasoning) hold at
      7B and above, and on standard math and code benchmarks?
- [ ] Which explains Loopback's small matched-compute win where Saunshi et
      al.'s plain loops lose: residual design, less weight sharing, or
      shorter training (20 against about 250 tokens per parameter)? Does
      the win survive longer training and more seeds?
- [ ] At matched inference FLOPs, does a looped model beat a written chain
      of thought on math or code?
- [ ] Does running a looped model past its trained depth hurt for the same
      reason overlong latent chains do (arXiv:2611.24001 covers only latent
      chains)? Does learned halting fix it?
- [ ] Do the loop counts trained models need on state-tracking tasks grow
      like `log n`, as the depth theory predicts?
- [ ] Do late-entry and early-exit speedups keep accuracy on harder
      reasoning benchmarks at 7B and above?

## Superseded

## Archive

## Log

- 2026-11-20: stub created from the latent-reasoning card.
- 2026-11-22: added a pointer to BDH-CQ.
- 2026-11-25: added Ouro, from the latent-reasoning-scaling investigation.
- 2026-11-25: `/investigate looped-transformers`, stub to draft.
  - Wrote L0, L1, core ideas (proposed, awaiting approval), the seven
    questions, L2, an L3 outline and L4.
  - Answered the old matched-FLOPs question in part with Saunshi et al.
    Table 3 (read verbatim). It was replaced by a narrower question.
  - Verified from abstracts the three seed entries that were unread or
    abstract only: Loopback (2611.07226), Late Entry (2611.24576) and
    LLoCoT (2610.11472, now with authors).
  - Corrected the latent-feedback note: arXiv:2611.20404 does not compare
    itself with looped models, so the cost comparison is now labelled as
    the vault's interpretation.
  - Noted that arXiv:2611.24001 covers latent chains only, not looped
    models.
  - alphaXiv was not connected; sources were found with web search and read
    from arXiv and the ARC Prize blog.
- 2026-11-25: re-read Saunshi, Ouro and Loopback with alphaXiv (left
  unfinished when alphaXiv was not connected).
  - Saunshi: checked Theorem 5.4's exact assumptions and added Theorem 5.1
    and Corollary 5.3. Table 3 numbers re-confirmed.
  - Loopback: read in full. Its comparison is matched in compute, not only
    in depth. Added margins, seeds and throughput, and three candidate
    explanations for the conflict with Saunshi. Narrowed the open question
    and amended proposed core idea 1.
  - Ouro: verified the extrapolation tables, the exit-gate training and
    the capacity setup; added the MMLU against MATH500 split.
