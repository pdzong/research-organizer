# How far can attention be cut without losing quality?

Status: draft
Last updated: 2026-11-17
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
- State that grows slowly with context, between constant and linear (for
  example log-linear attention, Guo et al. 2025 (unverified)), could move the
  frontier instead of picking a point on it.

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

## Open questions

- [ ] Is there a scaling law for the minimum fraction of exact-access layers
      (full or sparse) as a function of a task's recall demand?
- [ ] At 1M tokens, do models with no full attention keep their recall only
      because of sparse attention, or do pure fixed-state models also hold up?
- [ ] Does any architecture with sub-linear memory beat the recall-throughput
      frontier from the Based paper, rather than sit on it?
- [ ] How does sparse attention fail: which tasks make the selector skip the
      needed tokens?
- [ ] Do test-time-training layers (state as a small online model) change the
      capacity picture compared with matrix-valued state?

## Log

- 2026-11-17: created as a seed card. Adoption claims verified against
  Raschka's posts; paper citations are from memory and need verification
  (run `/investigate attention-efficiency` to verify and extend).
