# Do LLM agents reason better together, and does talking in latent space help?

Status: draft
Last updated: 2026-11-20
Related: [latent reasoning](latent-reasoning.md) ·
[associative memory](associative-memory.md) ·
[attention efficiency](attention-efficiency.md)

## L0 Headline

Several copies of an LLM that discuss a problem do often beat one copy, but
most of that gain comes from voting over independent answers. The discussion
itself adds little unless it surfaces a correct answer the vote missed.
Sending "latent beliefs" (soft-token embeddings) instead of text makes the
exchange shorter and cheaper. So far it does not reliably beat plain text
debate on accuracy.

## L1 Intuition

Analogy: a panel of experts who must agree on an answer.

- **Text debate:** each expert writes a memo, reads the others' memos, and
  rewrites their own. Memos are slow to write, and writing forces each expert
  to commit to one wording.
- **Latent beliefs (Stream of Belief):** instead of memos, the experts pass
  each other quick sketches that keep their hedges, such as "probably A,
  maybe C". The panel keeps exchanging sketches until nobody's sketch changes
  much.

Where the analogy breaks:

- The "experts" are copies of one model with different one-sentence persona
  prompts. They share the same knowledge and the same blind spots, so a
  panel is less diverse than a real committee.
- A "sketch" is not a private language. Each soft token is a
  probability-weighted average of ordinary word embeddings, so it stays close
  to text.
- "Nobody's sketch changes" does not mean "agreed" or "correct". The
  equilibrium can hold a 3-to-1 split, and stable beliefs can be wrong.

## The seven questions

### 1. Scarce resource

- **Sequential generation depth (latency).** Text debate makes each agent
  write a full reasoning trace every round, token by token.
- **Total compute.**
  - Every agent is a full model forward pass, so `N` agents in `K` rounds
    cost about `N × K` times a single answer.
  - Latent methods cut the number of text tokens, but not the total compute.
    The SoB authors say so explicitly (arXiv:2611.21250, Sec. 4.3).
- **Diversity of errors.** Voting and debate help only if agents make
  different mistakes. Copies of one model share most of theirs.
- **Context window.** In text debate each agent reads all peers' traces, so
  the context grows with `N` and with the number of rounds. SoB keeps a fixed
  `L × d` belief block per agent and rebuilds the context each cycle.

### 2. Trade-off

- **Information per message against interpretability and portability.**
  - Text is readable, auditable, and works across different models.
  - Latent messages carry the whole next-token distribution instead of one
    sampled token (the CIPHER argument, Pham et al., arXiv:2310.06272). They
    are less interpretable, and they usually need the same model on both
    sides.
- **Interaction against diversity.**
  - Reading peers' full answers makes agents converge within about one round,
    erasing the independent proposals that made voting work. Ann, Liu & Tan
    (arXiv:2608.23541) call this "the interaction tax", measured on 11
    verifier-scored tasks at matched budgets `[empirical]`.
- **Where SoB sits:**
  - Against other latent methods, SoB moves the frontier: higher accuracy and
    fewer sequential steps than LatentMAS, Soft Thinking and the others on
    most cells. This is `[empirical, self-reported]`, with baselines run by
    the authors.
  - Against text debate, it picks a different point: fewer tokens, and
    accuracy that is equal or lower on most tasks. Examples on Qwen3-8B:
    MATH-500 77.2 against 86.4, and GPQA-Diamond 44.9 against 53.0.
  - Equal total compute against debate is not established.

### 3. Boundary

- `[proven, under the paper's model of debate as a stochastic belief
  process]` **Debate alone does not raise expected correctness.**
  - Under this model, an agent's belief in the correct answer is a martingale
    over debate rounds: on average it stays where it started.
  - Measured gains therefore come from voting, or from interventions that bias
    updates toward correction.
  - Source: Choi, Zhu & Li 2025, "Debate or Vote", arXiv:2508.17536, NeurIPS.
  - `[empirical]` The same paper finds that majority voting accounts for most
    of the gain attributed to debate, across seven NLP benchmarks.
- `[empirical]` **Debate beats voting only in two cases:**
  - a correct proposal exists while the majority is wrong (their
    "recoverable headroom");
  - and the final readout can recognise it.

  Source: Zhao et al. 2026, "When Debate Helps", arXiv:2610.04686.
- `[proven, in the paper's stylized model where all agents see the same
  evidence]` **Communication adds no information when evidence is shared.**
  - Positive returns need one of three things: evidence split across agents,
    an external verifier, or models that make different errors.
  - The result says nothing about compute, so it does not rule out debate
    beating voting at equal tokens.
  - Source: Sajjadi Mohammadabadi 2026, arXiv:2611.17610, Proposition 3.1.
- `[empirical]` **Pooled evidence supports the L0 headline.**
  - The same paper pools nine studies, 516 multi-agent configurations in
    all.
  - Against baselines matched on sample count or budget, multi-agent systems
    average −0.042 in accuracy. They equal or trail the baseline in 74% of
    474 contrasts.
  - A multilevel model gives −0.195 on the log-odds scale (95% CI −0.320 to
    −0.070).
  - Caveats: the author calls it exploratory; it is not a systematic search,
    and heterogeneity is high (I² = 93%). All included methods talk in text,
    so latent methods such as SoB are not covered.
- `[proven, for binary decisions]` **Selectivity bar for revision.**
  - Let `a` be the initial accuracy. Revising answers raises accuracy only if
    the model reverses wrong answers more than `a/(1−a)` times as often as
    right ones: nine times at 90%.
  - This is an exact accounting identity, not a deep theorem.
  - Source: Tang & Lin 2026, arXiv:2611.16694, NeurIPS.
  - `[empirical]` Expert-attributed disagreement on 1,989 evidence-grounded
    yes/no items:
    - None of the five main models clears the bar, and accuracy falls by 1.9
      to 16.1 points.
    - In a smaller 250-item pool with a different protocol, Claude-Opus-4.8
      is the only model above the bar (1.33 times break-even), and its
      accuracy does not fall.
  - Every debate round is a revision step, so the same bar applies per
    round. `[interpretation]`
- `[empirical]` **Accuracy does not prove that a latent message is used.** A
  causal audit of latent relay on Qwen3-4B and 8B found a large share of the
  "gain" persists even when the receiver gets a message generated for a
  *different* example. Example: on MATH-500 with 4B, 8.33 of 15.00 points.
  Source: Zhang & Emu 2026, arXiv:2607.26773.
- **SoB's equilibrium is a definition, not a theorem.**
  - The paper proves no convergence result. Its stopping rule is "the
    majority probe answer is unchanged for 2 cycles", not the residual
    falling below a threshold.
  - The authors note that stable decoded answers do not guarantee a latent
    fixed point.
- `[interpretation]` Classic opinion-dynamics models such as DeGroot (1974)
  do converge to consensus under averaging. Consensus is the wrong target,
  though: averaging also averages away the one agent who was right. SoB's
  ablation that forces consensus each cycle points the same way, but the
  paper reports it only as PCA plots, with no accuracy numbers.

### 4. Lineage

- **Ensembles and the Condorcet jury theorem.** Voting helps if errors are
  independent and each voter is better than chance. Self-consistency is this
  idea applied to one model's samples (Wang et al. 2022, arXiv:2203.11171).
- **Opinion dynamics** in social science, which the SoB paper cites as its
  motivation:
  - DeGroot 1974, "Reaching a Consensus": repeated weighted averaging of
    neighbours' beliefs.
  - Friedkin–Johnsen and Hegselmann–Krause: stubborn agents, and bounded
    confidence.
  - What transfers: the network topology and stubbornness decide where beliefs
    settle.
- **Multi-agent debate** for LLMs: Du, Li, Torralba, Tenenbaum & Mordatch
  2023 (arXiv:2305.14325, ICML). Yilun Du is also last author on SoB (same
  name; not checked by author ID).
- **Latent reasoning inside one model:** Coconut (Hao et al. 2024,
  arXiv:2412.06769), which feeds hidden states back as inputs, and Soft
  Thinking (Zhang et al. 2025, arXiv:2505.15778, NeurIPS), which feeds
  probability-weighted mixtures of token embeddings. SoB's "beliefs" are Soft
  Thinking tokens passed between agents. See
  [latent reasoning](latent-reasoning.md).
- **Fixed points and energy minima.** SoB's picture of beliefs settling into
  basins borrows Hopfield-network language; see
  [associative memory](associative-memory.md). The paper labels this picture
  schematic. `[interpretation]`

### 5. Measurement

- **Always include a voting baseline at equal total compute.** Run `N × K`
  independent samples with a majority vote (self-consistency). Without it, a
  debate gain may be an ensemble gain. SoB reports no self-consistency
  baseline, and it also majority-votes its agents' final answers.
  - The pooled synthesis (arXiv:2611.17610) shows why this matters. Swapping
    a greedy baseline for a sampled one moves the multi-agent difference by
    −0.038 on average, and it moves the same way in all five studies that
    report both.
  - A budget-matched sampled baseline is now the bar for SoB.
- **Selectivity per round.** Track how often each round reverses wrong
  answers (`b`) and right answers (`h`). Compare `b/h` with `a/(1−a)`
  (arXiv:2611.16694).
- **Message-replacement controls.** Swap a message for one generated for a
  different example, or for one from the agent itself (Zhang & Emu 2026).
  This tells whether the content of a message matters.
- **Recoverable headroom.** Count the cases where some agent was right and the
  vote was wrong. Debate can only help there.
- **Diversity over rounds.** Track how far apart the agents' answers are
  across rounds, to detect the interaction tax.
- **Report total FLOPs or tokens, not only sequential depth.** SoB's latency
  gains (1.1–2.6x against LatentMAS) are in sequential generation depth.
- **Falsifiers.**
  - If SoB loses its advantage over a no-communication `N`-agent vote at equal
    compute, the "belief dynamics" claim fails.
  - If replacing peers' beliefs with beliefs from another example costs
    nothing, the same holds.

### 6. Adoption

- **Text multi-agent debate** is widely used in research. A 2026 systematic
  review counts 141 primary studies. It finds the field has converged by
  convention on fully connected topologies, verbatim exchange and voting
  (Motger et al. 2026, arXiv:2607.26212).
- **Latent multi-agent communication** is a fast-growing 2026 research topic
  with open code. Examples:
  - LatentMAS: Zou et al. 2025, arXiv:2511.20639, training-free, shared
    latent working memory. It reports up to 70.8–83.7% fewer output tokens
    and a 4–4.3x speed-up `[self-reported]`.
  - Cross-model KV-cache alignment: Chen et al. 2026, arXiv:2606.13594.
  - Several follow-ups on model replacement, compression and safety (from an
    alphaXiv search; not each verified).

  The vault has no evidence of production use.
- **SoB code:** "Embodied-Minds-Lab/Stream-of-Belief" is named on the paper's
  first page; the exact URL was not checked.

### 7. Combination

- **Mixed-model panels.** Panels of different model families give real error
  diversity, which is what voting needs. Today they require text, or a
  learned bridge between hidden spaces (Chen et al. 2026 align KV caches
  across Qwen3 pairs and from Mistral to Qwen). SoB is tested with
  homogeneous agents only.
- **Hybrid protocols.** Generate independent proposals first, which keeps
  diversity, then exchange beliefs only to verify. This follows "When Debate
  Helps" (proposal supply plus verification-aware readout). `[speculation]`
- **Debate with a verifier.** A verifier scores answers on the tasks where one
  exists (code, math). This is likely stronger than any belief dynamics on
  those tasks. `[speculation]`
- **Open problem:** what a latent message adds beyond voting and beyond the
  receiver's own sampling. Causal audits are the tool; SoB has not been
  audited.

## L2 Mechanism

Stream of Belief (Yao, Dong & Du 2026, arXiv:2611.21250; numbers from the
full text, read by a subagent, with the key cells checked against the
extracted tables).

- **Agents.**
  - `N` copies of one frozen model, each with its own one-sentence persona
    prompt and a shuffled option order.
  - No training.
  - Default settings: `N = 4`, `L = 384` belief tokens, at most 16 cycles.
- **Belief.** A block `z ∈ R^{L × d}` of soft tokens.
  - Each soft token is `z_l = Σ_v p_l(v) E[v]`: the model's next-token
    distribution, restricted to its top 50 tokens, used to average the input
    embeddings `E`.
  - So beliefs lie inside the convex hull of real word embeddings. No learned
    projection is needed, but sender and receiver must share an embedding
    space.
- **One cycle**, `Φ_m = L^m ∘ G`:
  - **Global step `G`:** each agent sees the problem, its own belief, and all
    other agents' beliefs inserted as soft input embeddings. It then
    generates a fresh `L`-token belief, which replaces the old one.
  - **Local step `L`, repeated `m` times:** the same, but the agent sees only
    the problem and its own belief.
- **Equilibrium.** This is a fixed point `Z* = Φ_m(Z*)`. It is measured by
  the residual `r_k = ‖Z(k+1) − Z(k)‖_F / (‖Z(k)‖_F + δ)`.
- **Stopping rule in practice.**
  - After each cycle, every agent decodes a 24-token probe answer.
  - The run stops when the majority probe has been unchanged for 2 cycles.
- **Final answer.** Each agent decodes up to 512 tokens from its own belief,
  then the agents' answers are majority-voted.
- **Ablations** (Qwen3-8B):
  - Belief length `L` matters most.
  - More agents helps on some tasks.
  - More cycles or more local steps give no consistent gain.
  - Over the cycles, beliefs drift closer to real token embeddings: the
    distance to the nearest token falls from 0.020 to about `3 × 10⁻⁴`.

## L3 Math

Planned outline:

- The martingale argument of Choi et al. 2025: when debate updates are
  unbiased, expected correctness is constant.
- DeGroot averaging as a Markov chain: consensus, and the limit determined by
  the stationary distribution of the trust matrix.
- The Condorcet jury theorem, and what correlated errors do to it.

## L4 Sources (reading order)

| # | Source | Why read it | Verified |
|---|---|---|---|
| 1 | Choi, Zhu & Li 2025, "Debate or Vote", arXiv:2508.17536, NeurIPS | The key boundary: voting explains most gains; martingale result | yes |
| 2 | Yao, Dong & Du 2026, "Stream of Belief", arXiv:2611.21250 | The paper this card was opened for | yes (full text) |
| 3 | Du, Li, Torralba, Tenenbaum & Mordatch 2023, "Improving Factuality and Reasoning in Language Models through Multiagent Debate", arXiv:2305.14325, ICML | Origin of LLM debate | yes |
| 4 | Pham et al. 2023, "Let Models Speak Ciphers" (CIPHER), arXiv:2310.06272, ICLR | First embedding-based debate; information-loss argument | yes |
| 5 | Zou et al. 2025, "Latent Collaboration in Multi-Agent Systems" (LatentMAS), arXiv:2511.20639 | Main latent baseline | yes |
| 6 | Zhao et al. 2026, "When Debate Helps", arXiv:2610.04686 | When debate can beat voting | yes |
| 7 | Ann, Liu & Tan 2026, "The Interaction Tax", arXiv:2608.23541 | Interaction erases diversity | yes |
| 8 | Zhang & Emu 2026, "Do Latent Channels Actually Communicate?", arXiv:2607.26773 | Causal audit method for latent messages | yes |
| 9 | Zhang et al. 2025, "Soft Thinking", arXiv:2505.15778, NeurIPS | The soft-token belief representation | yes |
| 10 | Hao et al. 2024, "Coconut", arXiv:2412.06769 | Latent reasoning in one model | yes |
| 11 | Chen et al. 2026, "Dense Latent Communication Across Heterogeneous Agents", arXiv:2606.13594 | Cross-model KV-cache communication | yes |
| 12 | Motger et al. 2026, "Multi-Agent Debate Strategies: Survey, Taxonomy, and Challenges", arXiv:2607.26212 | Survey of 141 studies | yes |
| 13 | Wang et al. 2022, "Self-Consistency", arXiv:2203.11171, ICLR | The voting baseline | yes |
| 14 | DeGroot 1974, "Reaching a Consensus", JASA | Opinion-dynamics origin | yes (metadata only) |
| 15 | Sajjadi Mohammadabadi 2026, "More Agents, More Samples, or More Thinking?", arXiv:2611.17610 | Pooled evidence against matched baselines; no-new-information proposition | yes (full text) |
| 16 | Tang & Lin 2026, "When Expert Disagreement Hurts", arXiv:2611.16694, NeurIPS | The `a/(1−a)` selectivity bar | yes (full text) |

## Open questions

- [ ] Does Stream of Belief beat an `N × K`-sample self-consistency vote at
      equal total compute? (2026-W47 update: text methods trail such
      baselines by about 4 points on average; latent methods are untested.)
- [ ] Does any debate protocol, latent or text, clear the `a/(1−a)`
      selectivity bar in each round?
- [ ] Under a message-replacement audit, how much of SoB's gain comes from
      example-specific belief content?
- [ ] Can latent belief exchange work across model families, where error
      diversity is real, without a trained bridge?
- [ ] Does latent exchange avoid the interaction tax, keeping proposals
      diverse longer than text exchange does?

## Log

- 2026-11-19: created from `/investigate` on arXiv:2611.21250 (Stream of
  Belief). Verified 14 sources with Semantic Scholar (Asta). Read the SoB
  full text from alphaXiv with a subagent, and checked key table cells
  (Qwen3-8B row, debate row) and the "rather than a reduction in total
  computational cost" sentence against the extracted text.
  - Semantic Scholar lists the SoB authors as Yu-Sheng Yao, Jia-Kai Dong and
    Yi-Lun Du. The paper's title page gives Yu Yao, Jiayi Dong and Yilun Du;
    the card uses the paper's names.
- 2026-11-20: applied the [2026-W47 radar update](../radar/2026-W47.md).
  - Boundary: Proposition 3.1, the pooled −0.042 result and the selectivity
    bar.
  - Measurement: the sampled-baseline shift and per-round selectivity.
  - Added L4 sources 15–16 and one open question.
  - Spot-checked the numbers against both papers with alphaXiv. This added
    the Claude-Opus-4.8 exception, which the radar did not mention.
