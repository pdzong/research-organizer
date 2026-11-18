# How far can attention be cut without losing quality?

Status: draft
Last updated: 2026-11-18
Related: [associative memory](associative-memory.md) ·
[state space models](state-space-models.md) ·
[test-time training](test-time-training.md)

## L0 Headline

Full attention is expensive because every token is compared with every other
token. New open models increasingly replace most attention layers with cheaper
ones. What you give up is exact recall of arbitrary details from a long
context, so the real question is how much exact recall a task needs.

## L1 Intuition

Analogy: full attention is a reader who, before writing each word, rereads the
whole book. A linear or recurrent layer is a reader with a notebook of fixed
size who updates notes while reading and never looks back. Sliding-window
attention rereads only the last few pages. Sparse attention uses an index to
reread only the pages that look relevant.

Where the analogy breaks:

- The "notebook" is not a summary in words. It is a matrix in which many
  key-to-value associations are superimposed, so storing more items makes
  retrieval of each one noisier (interference) instead of just dropping old
  pages.
- What gets written and forgotten is learned, through gates, not chosen by a
  person.
- Sparse attention still reads the original text exactly, so it does not lose
  recall the way the notebook does. Its risk is choosing the wrong pages.

## The seven questions

### 1. Scarce resource

- Compute for full attention grows with the square of the sequence length
  `n` (`O(n² d)` per layer, `d` = head dimension).
- Memory for the key-value cache grows linearly with `n` per layer, and at long
  contexts this cache, not compute, often limits batch size and cost during
  generation.

### 2. Trade-off

- Fixed-size state (linear attention, DeltaNet, Mamba-style recurrences) makes
  compute linear in `n` and memory constant, but trades away exact recall.
  The Based paper frames this as a recall-versus-throughput frontier: bigger
  state means better recall and lower throughput `[empirical]` (Arora et al.
  2024).
- Sparse attention keeps exact access to selected tokens and trades away
  coverage: whatever the selector skips is invisible.
- Hybrids keep a few full (or sparse) attention layers for exact lookups and
  use cheap layers elsewhere. Most 2026 open models pick a point on this
  frontier rather than move it.

Test for a "new transformer": does a new design move the recall-versus-cost
frontier, or only pick a different point on it?

### 3. Boundary

- `[proven, if SETH]` Exact self-attention needs quadratic time unless the
  Strong Exponential Time Hypothesis is false; the argument extends to some
  approximate versions (Keles et al. 2022).
- `[proven, if SETH]` Fast approximation is possible only when attention is
  "soft": with query and key entries bounded by `o(√log n)` there is an almost
  linear-time approximation; at `Θ(√log n)` no truly subquadratic algorithm
  exists (Alman & Song 2023). Intuition: sharp, confident lookups are exactly
  the expensive part.
- `[proven]` A model with a fixed-size state cannot copy strings longer than
  its state can hold, while a two-layer transformer can copy strings of length
  exponential in its size (Jelassi et al. 2024). Copying and lookup are where
  the cheap layers fail.
- `[proven, for linear time-invariant filters]` Retrieving one specific token
  is incompressible. For an `n`-state time-invariant filter, the best
  approximation error is at least the `(n+1)`-th Hankel singular value. A pure
  `W`-step delay has all `W` singular values equal to 1, so it needs all `W`
  states, while a window average needs only about `1/(2ε)` states (Pei 2026,
  Zenodo doi:10.5281/zenodo.24191078, a single-author note with no
  experiments). This does not cover data-dependent layers such as Gated
  DeltaNet or Mamba-2.
- `[proven, if logits follow the paper's two-block model]` Sparse selectors
  that score blocks by pooled (averaged) keys have a "blind window". When a
  block holds one decisive needle key and a competitor block is uniformly a
  little stronger, exact attention mass ranks the needle block first, but any
  mean-pooled score ranks the competitor first (Zhang & Chen 2026,
  arXiv:2611.21917, Proposition 1).
- `[empirical]` Most of the quality gap between attention and efficient
  architectures on language modeling is explained by associative recall
  (Zoology, Arora et al. 2023).
- `[interpretation]` This is a memory-capacity argument: storing `N`
  arbitrary associations exactly needs memory that grows with `N`. Classical
  associative memories have capacity proportional to their size; see
  [associative memory](associative-memory.md).

### 4. Lineage

- Attention as associative memory: the attention update is the retrieval step
  of a modern Hopfield network, a model from statistical physics (Ramsauer et
  al. 2020). Classical Hopfield networks (1982) store about `0.14 N` patterns
  in `N` neurons; modern "dense" versions store exponentially many (Krotov &
  Hopfield 2016; Demircigil et al. 2017).
- Linear attention as fast weights: dropping the softmax turns attention into
  an RNN whose state is a matrix written by outer products (Katharopoulos et
  al. 2020), which is a "fast weight programmer" from the early 1990s (Schlag,
  Irie & Schmidhuber 2021). Outer-product writing is Hebbian learning.
- The delta rule: DeltaNet and Gated DeltaNet replace "add the new
  association" with "correct the stored association by its error", which is
  the Widrow-Hoff LMS rule from 1960s adaptive filtering (Yang et al. 2024;
  Yang, Kautz & Hatamizadeh 2025).
- State space models come from control theory and signal processing (Kalman
  filters, linear systems): S4, then Mamba and Mamba-2, which showed a formal
  duality between SSMs and a form of linear attention (Gu & Dao 2023; Dao & Gu
  2024).
- Test-time training: one delta-rule update is one gradient step on
  `‖S k − v‖²`, so the recurrent state is a tiny model trained online during
  inference. TTT layers and Titans build on this view (Sun et al. 2024;
  Behrouz et al. 2025). See [test-time training](test-time-training.md).
- `[interpretation]` Neuroscience analogy for hybrids: complementary learning
  systems, with fast exact episodic memory (hippocampus, like full attention)
  next to slow compressed memory (neocortex, like recurrent state).

### 5. Measurement

- Synthetic associative recall: multi-query associative recall (MQAR, from
  Zoology) and copying or phonebook lookup (Jelassi et al. 2024). These expose
  the fixed-state limit most directly.
- Long-context retrieval: needle-in-a-haystack and RULER (Hsieh et al. 2024),
  which adds multi-hop tracing and aggregation.
- Sparse-selector probe: RULER MK3 (multi-key needle in a haystack of
  look-alike UUIDs). It exposes block-selection failure that single-needle
  tests miss: a single needle among filler flags no failing head (Zhang & Chen
  2026, arXiv:2611.21917). On MiniCPM4.1-8B at 64K, the shipped sparse
  selector scores 54.1 against 97.1 dense `[empirical]`.
- Real tasks: long-document QA, repository-scale code, long agent traces with
  many tool calls.
- Falsifier: a model with no exact-access layers (no full and no sparse
  attention) that matches a hybrid on MQAR and RULER at long lengths and the
  same state budget would contradict the current picture.

### 6. Adoption

- Sebastian Raschka's tracking (Nov 10, 2026): in the second half of 2026,
  new open models split about 50/50 between hybrids with some full attention
  and models with no full attention at all; none use full attention in every
  layer ([From Full to Hybrid Attention](https://sebastianraschka.com/blog/2026/full-to-hybrid-attention.html)).
  Note that his "no full attention" group includes sparse attention, which
  still gives exact access to selected tokens.
- Examples he lists in the gallery: DeepSeek V3.2 adds DeepSeek Sparse
  Attention on top of multi-head latent attention; other hybrids mix full
  attention with Gated DeltaNet, Kimi Delta Attention, Mamba-2, Lightning
  Attention or sliding windows
  ([LLM Architecture Gallery](https://sebastianraschka.com/blog/2026/llm-architecture-gallery.html)).
- The motive is cheap long context for agents, large codebases and long
  documents.

### 7. Combination

- Retrieval (RAG) and tool use act as external exact memory, which may let
  fixed-state models skip in-context recall. `[speculation]`
- Conditional exact access: run expensive attention only when the model
  detects that it needs a lookup (related to routing ideas such as mixture of
  depths). `[speculation]`
- State that grows slowly with context, between constant and linear, could
  move the frontier instead of picking a point on it. Log-linear attention
  keeps a Fenwick-tree hierarchy of `O(log T)` state matrices (Guo et al.
  2025, arXiv:2506.04761, ICLR 2026).
- Newest data point: bilateral log-linear attention adds a second,
  origin-anchored hierarchy, so early context is also kept at fine resolution
  (Islam & Cong 2026, arXiv:2611.18974). `[empirical]`, about 365M-parameter
  models with one training seed:
  - MQAR (512 tokens): 96.1, against 76.4 for log-linear Mamba-2 and 99.5 for
    a Transformer.
  - RULER-NIAH average at 6144 tokens: 50.0, against 27.0 and 58.7.

  Caveat: it holds about twice as many state matrices as forward log-linear
  attention, so the comparison is not at matched state. It has no Gated
  DeltaNet baseline and no runs past 8K tokens.

## L2 Mechanism

Notation: `q_t, k_t, v_t` are the query, key and value vectors at position
`t`; `S_t` is a recurrent state matrix.

- Full (softmax) attention: `o_t = Σ_{i≤t} softmax_i(q_t · k_i / √d) v_i`.
  Every new token compares with all previous keys.
- Linear attention: remove the softmax (or replace it with a feature map), and
  the sum can be kept as a running matrix: `S_t = S_{t-1} + v_t k_tᵀ`,
  `o_t = S_t q_t`. State size is `d × d` regardless of `n`.
- Delta rule: `S_t = S_{t-1} − β_t (S_{t-1} k_t − v_t) k_tᵀ`. First read
  what is currently stored at key `k_t`, then correct it toward `v_t`, with
  learning rate `β_t`.
- Gated delta rule: `S_t = α_t S_{t-1} (I − β_t k_t k_tᵀ) + β_t v_t k_tᵀ`,
  where `α_t` is a learned forgetting gate.
- Sliding window: full attention restricted to the last `w` tokens, cost
  `O(n w)`.
- Sparse attention: a cheap scorer selects the top blocks or tokens, then
  exact attention runs only on them (for example Native Sparse Attention,
  Yuan et al. 2025, and DeepSeek Sparse Attention).

## L3 Math

To fill on request (`/deepen attention-efficiency L3`). Planned content:

- Why softmax prevents the running-sum trick, and what the feature-map
  approximation loses.
- The SETH reduction behind Keles et al. and the bounded-entries threshold in
  Alman & Song.
- Capacity of a `d × d` linear associative memory under interference, and how
  the delta rule reduces interference compared with pure Hebbian writing.

## L4 Sources (reading order)

Verified: "yes" means checked against the source during this session; "no"
means cited from memory and must be checked before being relied on.

| # | Source | Why read it | Verified |
|---|---|---|---|
| 1 | Raschka 2026, [From Full to Hybrid Attention](https://sebastianraschka.com/blog/2026/full-to-hybrid-attention.html) | The adoption trend in one chart | yes |
| 2 | Raschka 2026, [LLM Architecture Gallery](https://sebastianraschka.com/blog/2026/llm-architecture-gallery.html) | Diagrams and a diff tool per model | yes |
| 3 | Arora et al. 2023, "Zoology", arXiv:2312.04927 | Recall explains the quality gap | no |
| 4 | Jelassi et al. 2024, "Repeat After Me", arXiv:2402.01032 | Proof of the fixed-state copying limit | no |
| 5 | Arora et al. 2024, "Simple linear attention language models balance the recall-throughput tradeoff" (Based), arXiv:2402.18668 | The frontier, measured | no |
| 6 | Keles et al. 2022, "On the Computational Complexity of Self-Attention", arXiv:2209.04881 | Quadratic lower bound under SETH | no |
| 7 | Alman & Song 2023, "Fast Attention Requires Bounded Entries", arXiv:2302.13214 | Soft versus sharp attention threshold | no |
| 8 | Ramsauer et al. 2020, "Hopfield Networks is All You Need", arXiv:2008.02217 | Attention as associative memory | no |
| 9 | Katharopoulos et al. 2020, "Transformers are RNNs", arXiv:2006.16236 | Linear attention | no |
| 10 | Schlag, Irie & Schmidhuber 2021, "Linear Transformers Are Secretly Fast Weight Programmers", arXiv:2102.11174 | Fast weights and the delta rule | no |
| 11 | Yang et al. 2024, "Parallelizing Linear Transformers with the Delta Rule over Sequence Length", arXiv:2406.06484 | DeltaNet | no |
| 12 | Yang, Kautz & Hatamizadeh 2025, "Gated Delta Networks", arXiv:2412.06464 | Gated DeltaNet | no |
| 13 | Gu & Dao 2023, "Mamba", arXiv:2312.00752; Dao & Gu 2024, "Transformers are SSMs", arXiv:2405.21060 | SSM lineage and duality | no |
| 14 | Yuan et al. 2025, "Native Sparse Attention", arXiv:2502.11089 | Trainable sparse attention | no |
| 15 | Sun et al. 2024, "Learning to (Learn at Test Time)", arXiv:2407.04620; Behrouz et al. 2025, "Titans", arXiv:2501.00663 | State as an online-trained model | no |
| 16 | Hsieh et al. 2024, "RULER", arXiv:2404.06654 | Long-context benchmark | no |
| 17 | Guo, Yang, Goel, Xing, Dao & Kim 2025, "Log-Linear Attention", arXiv:2506.04761 (ICLR 2026) | State that grows as `log T` | yes (metadata) |
| 18 | Islam & Cong 2026, "Bilateral Log-Linear Attention", arXiv:2611.18974 | Recall gain from a second hierarchy, at about 2x state | yes |
| 19 | Zhang & Chen 2026, "Lost in a Few Heads: Diagnosing and Repairing Block Selection in Sparse Attention", arXiv:2611.21917 ([code](https://github.com/zhangwenhe1007/blind-attention-heads)) | How sparse selectors fail, and cheap fixes | yes |
| 20 | Pei 2026, "Kernel, Transport, Support: A Unified Prescription for Attention, State-Space and Delta-Rule Sequence Mixers", Zenodo doi:10.5281/zenodo.24191078 | One formula for all mixers; Hankel bound on retrieval | yes (read via alphaXiv; not on arXiv) |

## Open questions

- [ ] Is there a scaling law for the minimum fraction of exact-access layers
      (full or sparse) as a function of a task's recall demand?
- [ ] At 1M tokens, do models with no full attention keep their recall only
      because of sparse attention, or do pure fixed-state models also hold up?
- [ ] Does any architecture with sub-linear memory beat the recall-throughput
      frontier from the Based paper, rather than sit on it? (2026-W47:
      bilateral log-linear attention gains a lot of recall, but with about 2x
      state, so it does not settle this.)
- [ ] How does sparse attention fail: which tasks make the selector skip the
      needed tokens? Partly answered (2026-W47): block-pooled selectors
      misrank a needle block among look-alike competitors on multi-key tasks.
      The loss sits in a few heads and is fixable cheaply (arXiv:2611.21917).
      For token-level selectors, see the next question.
- [ ] Do token-level selectors (such as DeepSeek Sparse Attention) have their
      own blind spots in harder multi-key settings, or is block pooling the
      whole story? Their only evidence so far is one near-ceiling multi-key
      task per model (arXiv:2611.21917).
- [ ] Does storing recurrent state in bf16 with round-to-nearest also hurt
      associative recall (MQAR, RULER), not only reasoning length? It makes 5
      of 6 hybrid reasoning models think 7–27% longer (arXiv:2611.12127), so
      the state dtype is a hidden variable in hybrid comparisons.
- [ ] Do test-time-training layers (state as a small online model) change the
      capacity picture compared with matrix-valued state?

## Log

- 2026-11-17: created as a seed card. Adoption claims verified against
  Raschka's posts; paper citations are from memory and need verification
  (run `/investigate attention-efficiency` to verify and extend).
- 2026-11-18: applied the [2026-W47 radar](../radar/2026-W47.md) updates:
  - Boundary: pooled-selector blind window and the Hankel retrieval bound.
  - Measurement: the RULER MK3 selector probe.
  - Combination: the verified log-linear citation and bilateral log-linear
    attention.
  - L4 sources 17–20 and notes on two open questions.
- 2026-11-18: added open questions raised by the 2026-W47 radar.
