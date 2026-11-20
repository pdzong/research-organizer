# What limits how much an associative memory can store and retrieve?

Status: draft
Last updated: 2026-11-20
Related: [attention efficiency](attention-efficiency.md) ·
[test-time training](test-time-training.md) ·
[state space models](state-space-models.md) ·
[mixture of experts](mixture-of-experts.md)

## L0 Headline

Attention, linear attention and Hopfield networks are all associative
memories: they store key-to-value pairs and return a value for a cue. If the
memory squeezes everything into one fixed matrix, it is cheap but holds only
about as many clean associations as its dimension. If it keeps every item
separately, as attention's KV cache does, recall is exact but memory grows with
every item stored.

## L1 Intuition

A Hopfield network is a memory you query with a partial or noisy version of
something it stored, and it returns the full stored item.

Analogy:

- **Classic Hopfield network: one composite photo.** All your photos are
  overlaid into one image. To find a face, you stare at the composite until a
  familiar one emerges. After too many overlays it is just mush.
- **Modern Hopfield network: a photo album.** You compare your blurry snapshot
  with every page and point to the best match.

Where the analogy breaks:

- The classic network does not "stare" once. It updates itself step by step,
  sliding downhill on an energy surface until it settles in a valley, which is
  a stored pattern.
- The modern network does not strictly pick one page. With a soft softmax it
  returns a blend of similar pages. That blend is useful inside a transformer,
  but it is not a clean lookup.
- The album needs more pages as you store more. That is exactly the growing
  cost of a key-value cache.

## The seven questions

### 1. Scarce resource

- **State bytes per stored association.**
  - A fixed matrix memory (linear attention, DeltaNet) has `d_k × d_v` numbers
    per head, whatever the context length.
  - A KV cache stores one key and one value per token, so it grows linearly
    with the number of items.
- **Key dimension.** In a fixed matrix, the number of nearly orthogonal key
  directions limits how many items can be stored without crosstalk.
  Correlated real-world keys use these directions up faster (see "Capacity
  under correlated keys" below).
- **Read compute.**
  - A softmax readout compares the cue with every stored item: `O(M)` per
    query.
  - A matrix readout costs `O(d_k d_v)`, whatever the number of items.

### 2. Trade-off

- The core exchange is **memory size against recall exactness**:
  - Superposition (one matrix, Hebbian or delta-rule writes) is fixed-size and
    cheap, but items interfere.
  - Separate storage (softmax over all items) is exact, but it grows with the
    number of items. This is the recall-versus-throughput frontier on the
    [attention card](attention-efficiency.md).
- **Sharpness `β` in a modern Hopfield network trades clean lookup against
  blending.**
  - A large `β` retrieves one pattern.
  - A small `β` averages many patterns: a global average, or "metastable"
    averages over subsets.
  - Ramsauer et al. 2020 (arXiv:2008.02217) report that transformer heads in
    early layers mostly average, and heads in later layers mostly sit in
    metastable states `[empirical]`.
  - A `β` that is tuned at one size fails as the number of items grows
    (Mohsenvand 2026, "Attention at Absolute Zero", arXiv:2611.11937, on the
    card game SET) `[empirical, self-reported, one task family]`:
    - with weights set by hand, a temperature tuned for 8 cards fails from 48
      cards;
    - trained scores multiplied by 1, 2, 4 and 8 (that is, a larger `β`) give
      72.0, 83.1, 98.7 and 99.7% at 364 cards;
    - the zero-temperature read gives 99.8%.
- **Recent work mostly changes the cost of a big state, not the frontier
  itself:**
  - Delta-rule writes use the same state better: they correct an old entry
    instead of piling a new one on top.
  - Sparse Delta Memory (Cabannes et al. 2026, arXiv:2607.07386) and
    Fast-weight Product Key Memory (Zhao & Jones 2026, arXiv:2601.00671) make
    the state much larger at fixed compute per token by reading and writing
    only a few slots. SDM reports better in-context learning and long-context
    retrieval at equal FLOPs and equal parameters `[empirical, self-reported]`.
  - Kernelized feature maps (KATA, Ghriss & Chakraborty 2026,
    arXiv:2607.17419) enlarge the effective state without adding parameters.
    The authors report 0.985 MQAR at 16x the training length, with about a
    quarter of the KV-cache entries `[empirical, self-reported]`.
  - **Richer write rules win mainly through a bigger state.**
    `[empirical, self-reported]`
    - Kernel Ridge Attention (KRA; Chen, Wang & Xu 2026, arXiv:2611.23896)
      replaces the delta rule with recursive least squares.
      - At about 31M parameters, rare-repeat top-1 is 25.41%, against 6.69%
        for Gated DeltaNet.
      - Caveats: KRA uses about 1.9x the state (1.165 against 0.615 MiB at
        8K), the result is from one seed, and there is no MQAR test.
    - Toaster (Li et al. 2026, Google Research, arXiv:2611.23648) stores a
      two-layer MLP as its state. It beats KDA at all five sizes from 0.2B
      to 1.6B, with 8x KDA's state.
      - Its own state-matched control: KDA given 8x state reaches 15.79,
        against 15.69 for Toaster and 16.00 for default KDA (C4 perplexity,
        145M, single runs).
      - So about two-thirds of the gain comes from the larger state.
- `[interpretation]` These methods move the compute-per-state-byte curve.
  None of them escapes the bytes-per-association limit in the Boundary
  section.

### 3. Boundary

- `[proven]` **Counting bound.** To recall `n` arbitrary associations of `b`
  bits each, a memory must hold at least `n · b` bits. No architecture escapes
  this. A fixed state therefore always has a ceiling on arbitrary recall.
  - This is elementary information theory, stated here as the vault's own
    framing, not quoted from a paper.
  - The copying result on the attention card is a sharper form of the same
    limit (Jelassi et al. 2024, arXiv:2402.01032).
- `[proven]` **Rank bound for linear matrix memory.**
  - A `d × d` linear map can return arbitrary values exactly for at most `d`
    keys, and only if those keys are linearly independent.
  - Pure Hebbian writing (`S = Σ v kᵀ`) is exact only for orthonormal keys.
    Any key overlap becomes crosstalk.
  - Schlag, Irie & Schmidhuber 2021 (arXiv:2102.11174) derive this capacity
    limit for linear attention, and use it to motivate the delta rule.
- `[proven, if the replica-symmetric ansatz holds]` **Classic Hopfield
  capacity.**
  - For random binary patterns, a classic Hopfield network stores about
    `0.138 N` patterns before retrieval collapses (Amit, Gutfreund &
    Sompolinsky 1985, PRL 55:1530, doi:10.1103/PhysRevLett.55.1530).
  - The replica method is a statistical-physics calculation, not a rigorous
    proof; simulations agree with it.
  - A later replica-symmetry-breaking analysis gives about `0.144`. The value
    also depends on how many retrieval errors are tolerated. Both points come
    from secondary sources found by web search; the PDFs were not read
    (unverified).
- `[proven]` **Dense associative memories.**
  - With an exponential interaction function, the generalised Hopfield model
    of Krotov & Hopfield stores exponentially many patterns in `N`.
  - Its basins of attraction are nearly as large as the classic model's.
  - Rigorous proof: Demircigil et al. 2017, J. Stat. Phys., arXiv:1702.01929.
- `[proven, under the paper's assumptions on pattern separation]` **Modern
  continuous Hopfield networks** (Ramsauer et al. 2020):
  - They store exponentially many patterns in the dimension.
  - They converge in one update, with exponentially small retrieval error.
- `[interpretation]` **"Exponential capacity" counts something different.**
  - It counts how many separately stored patterns can be told apart in
    dimension `N`.
  - It does not mean a fixed number of bytes holds exponentially many items:
    the modern network keeps every pattern in `X`, which grows with `M`.
  - So it does not contradict the counting bound. It is the "photo album"
    side of the trade-off.
- `[proven, for unit keys and values]` **Hebbian crosstalk.** With orthonormal
  values, no key set keeps the mean squared crosstalk within `ε²` once
  `n > d(1+ε²)` (Abdulla et al. 2026, TANSAR, arXiv:2611.12374). Details below.
- `[empirical]` **How pretrained linear-attention models degrade.** In
  pretrained GLA and Gated DeltaNet models:
  - Recall and editability fall as **memory load** grows. The elapsed context
    length matters much less.
  - Stored facts are causally coupled rather than independent.
  - In hybrid models, recall shifts mainly to the full-attention KV cache.
  - Source: Lee et al. 2026, arXiv:2609.33093. The evidence comes from a few
    models and controlled interventions.
- `[proven]` **Zero-temperature limit of softmax.**
  - As `β → ∞`, `β⁻¹ log Σ exp(β s_w)` tends to the best score `s*`.
  - The sum divided by `exp(β s*)` tends to the number of items tied at
    `s*`.
  - So a hard read that keeps the best score and its tie count keeps
    everything a cold enough softmax can see. This is the large-`β` end of the
    modern Hopfield trade-off.
  - Source: Mohsenvand 2026, arXiv:2611.11937, Proposition 1. The proof is
    short and elementary; the paper notes that it is not machine-checked.

### 4. Lineage

- **Statistical physics.**
  - Hopfield (1982) mapped memory to energy minima of an Ising-like spin
    system.
  - Capacity results come from spin-glass theory (Amit et al. 1985).
  - Intuitions that transfer: energy landscapes, basins of attraction,
    metastable states, and a signal-to-noise view of crosstalk.
- **Fast weights and Hebbian learning.**
  - Linear attention equals a 1990s "fast weight programmer": a slow network
    writes outer products into a fast weight matrix (Schlag et al. 2021).
  - Outer-product writing is Hebb's rule.
  - The delta rule is the Widrow-Hoff LMS rule from adaptive filtering (see
    the [attention card](attention-efficiency.md)).
- **Dense associative memory and deep nets.** Krotov & Hopfield (2016,
  arXiv:1606.01164) gave a duality between dense associative memories and
  one-hidden-layer feedforward networks.
- **Feed-forward layers.** Geva et al. (arXiv:2012.14913, EMNLP) found that a
  transformer's feed-forward layers act as key-value memories. That is
  parametric memory, written during training rather than in context.
- **Regression.** "Test-time regression" (Wang, Shi & Fox 2025,
  arXiv:2501.12352) treats storing as a regression problem solved during
  inference.
  - Linear attention, SSMs, fast-weight programmers, online learners and
    softmax attention fall out as special cases of three design choices: the
    regression weights, the function class and the optimiser.
  - The framework also explains why linear attention misses correlations
    between tokens.
  - This links the card to [test-time training](test-time-training.md).
- **Kalman filtering and Gaussian processes.**
  - KRA's write is recursive least squares, and with a learned decay it is a
    Kalman filter.
  - Its output equals kernel ridge regression over the prefix, with a content
    kernel times an exponential time kernel. `[proven]` (arXiv:2611.23896,
    Proposition 2.)
  - Intuition that transfers: a running covariance tells the memory which key
    directions are already pinned down.
- **Tropical (max-plus) algebra.** The zero-temperature limit of log-sum-exp
  is Maslov's dequantisation: sums become maxima and products become sums
  (arXiv:2611.11937). This is the algebra of hard attention and of counting
  shortest paths.

### 5. Measurement

- **Capacity curve at fixed state.** Run MQAR at one state size while
  increasing the number of key-value pairs. Report the number of pairs at
  which accuracy drops, not a single accuracy.
- **Correlated keys.** Compare real (semantic) keys with random keys at the
  same dimension. TANSAR shows a large drop: 58 against 257 pairs at
  `ε = 0.5`.
- **Overwrite.** Test repeated-key overwrite: the same key with a new value.
  This exposes whether the write rule can erase. Hebbian writing cannot; the
  delta rule can.
- **Load versus length.** Hold the number of facts fixed and add filler, then
  do the reverse. Lee et al. 2026 find that load matters more.
- **State-matched control.** Compare any richer write rule at equal state
  bytes, not only at equal parameters.
  - Toaster gives the template: widen the baseline's state, by trading heads
    for wider heads at a fixed backbone, until it matches the new method.
  - Then report both gaps: at matched parameters and at matched state.
- **Falsifiers.**
  - If a delta-rule model's capacity curve matched a Hebbian model's at the
    same state size, the delta rule's claimed advantage would fail.
  - If a sparse-addressed memory lost its advantage once compared at equal
    state bytes, not only equal FLOPs, its claim to move the frontier would
    fail.

### 6. Adoption

- **Delta-rule associative memories ship in production hybrids.** Gated
  DeltaNet and Kimi Delta Attention appear in Raschka's 2026 architecture
  gallery; see the [attention card](attention-efficiency.md) for sources.
- **Research activity in 2026 is dense.** Many variants change how the matrix
  memory is written. Affiliations below are from alphaXiv metadata; the
  author lists were not checked:
  - Gated DeltaNet-2 (NVIDIA, arXiv:2605.22791).
  - Erase-then-Delta Attention (Qwen team, arXiv:2606.26560).
  - KronLSTM (NXAI, arXiv:2610.26834).
  - Kalman Delta Networks (arXiv:2609.07816).
- **Sparse large-state memories come from big labs:** Meta's SDM and Sakana
  AI's FwPKM.
- **Hopfield layers as a drop-in module.** Ramsauer et al. released a PyTorch
  "Hopfield" layer for pooling, memory and attention.
- **Tutorial-level maturity.** There is a 2025 tutorial with coding notebooks
  (Krotov et al., arXiv:2507.06211) and a Nature Reviews Physics perspective
  (Krotov 2023, doi:10.1038/s42254-023-00595-y).

### 7. Combination

- **Sparse addressing plus delta-rule writes** (SDM, FwPKM) give a large
  memory at fixed compute per token. It is close in spirit to the routing in
  [mixture of experts](mixture-of-experts.md), applied to memory slots instead
  of feed-forward experts. `[interpretation]`
- **Three memories in one model:**
  - parametric memory (feed-forward layers, written in training);
  - compressed in-context memory (recurrent state);
  - exact in-context memory (KV cache in a few layers).
  - Lee et al.'s hybrid result suggests that the KV layers do most of the
    recall, which raises the question of how small the recurrent state can
    be.
- **Delta rule against correlated keys.** `[speculation]`
  - A delta-rule write is one step of online least squares.
  - Least squares compensates for correlated keys, roughly what mean-centring
    does in TANSAR.
  - So delta-rule writing may recover part of the capacity that semantic keys
    lose.
  - KRA (arXiv:2611.23896) now builds the exact version as a layer. It keeps
    a covariance `P` of past keys and writes along `P k` instead of `k`.
  - It has not measured capacity at matched state, so the capacity claim stays
    a speculation.
- **Test-time regression as a design map.** Picking a richer regressor (an MLP
  state) or a better optimiser is how [test-time training](test-time-training.md)
  layers try to raise capacity per byte of state.

## L2 Mechanism

Notation: the stored patterns are `ξ_1 … ξ_M`, each a vector of length `N`; the
cue is `x`.

**Classic Hopfield network** (Hopfield 1982, PNAS,
[DOI 10.1073/pnas.79.8.2554](https://doi.org/10.1073/pnas.79.8.2554)).

- Neurons are `±1` values.
- Storing (Hebbian): `W = Σ_μ ξ_μ ξ_μᵀ`. All patterns are superimposed in one
  fixed `N × N` matrix.
- Recalling: repeat `x_i ← sign(Σ_j W_ij x_j)` until nothing changes. Each
  update lowers an energy `E = −½ xᵀ W x`, so the state rolls into the nearest
  valley.
- Capacity: about `0.138 N` random patterns before the patterns interfere and
  recall fails (Amit et al. 1985; see Boundary).

**Modern (continuous) Hopfield network** (Ramsauer et al. 2020,
arXiv:2008.02217).

- The patterns are kept separately as the columns of `X = [ξ_1 … ξ_M]`.
- Recalling, in one step: `x_new = X · softmax(β Xᵀ x)`.
  - Compare the cue with every stored pattern (`Xᵀ x`).
  - Turn the scores into weights with a softmax of sharpness `β`.
  - Return the weighted mix of patterns.
- This is one attention operation: the cue is the query, and the stored
  patterns are both the keys and the values. With learned projections for
  queries, keys and values, it is the transformer's attention layer.
  `[proven]`, an exact algebraic identity for one update step (Ramsauer et al.
  2020).
- A large `β` snaps to the single closest pattern (exact recall). A small `β`
  returns an average of similar patterns.
- Capacity grows exponentially in `N`, because patterns are not superimposed
  (Krotov & Hopfield 2016; Demircigil et al. 2017; Ramsauer et al. 2020 for
  the continuous version).

**Matrix memory in sequence models: Hebbian versus delta-rule writes.**

- Hebbian (linear attention): `S ← S + v kᵀ`. New pairs are added on top of
  the old ones, and nothing is ever corrected.
- Delta rule (DeltaNet): `S ← S + β (v − S k) kᵀ`.
  - First read what is currently stored under `k`.
  - Then write only the error.
  - With unit `k` and `β = 1`, the update makes `S k = v` exactly for the
    newest key. It disturbs older keys only through their overlap with `k`.
- Readout for both: `ŷ = S q`.

**Mapping to sequence-model layers** (see
[attention efficiency](attention-efficiency.md)):

| Hopfield network | Sequence-model layer | Memory |
|---|---|---|
| Classic: all patterns summed into one matrix `W` | Linear attention / DeltaNet: state `S` is a sum of `v kᵀ` outer products | Fixed size; items interfere; limited capacity |
| Modern: every pattern kept, softmax lookup | Full attention: the key-value cache keeps every token | Grows with what is stored; exact recall |

`[interpretation]` The fixed-state-versus-exact-recall trade-off on the
attention card is this old associative-memory trade-off. The identity holds
exactly for one update step; the rest of the mapping is a framing. One
difference: the classic network uses `W = Σ ξ ξᵀ` (auto-association, where the
key is the value), while linear attention stores `v kᵀ` (hetero-association,
where the key and value differ).

## Capacity under correlated keys (from the 2026-W47 radar)

Source for this section: Abdulla et al. 2026, "TANSAR", arXiv:2611.12374
([code](https://github.com/abdulhadyabas2/Topology-Aware-Neuro-Symbolic-Associative-Retrieval-for-Multi-Hop-Knowledge-Editing)).
The paper studies a purely additive (Hebbian) matrix memory
`C = Σ β_i k_i v_iᵀ`.

- `[proven, for unit keys and values]` Crosstalk limits capacity:
  - Crosstalk is bounded by key coherence, with no distributional assumption
    on the keys.
  - With orthonormal values, no key set keeps the mean squared crosstalk at or
    below `ε²` once the number of stored pairs `n` exceeds `d(1+ε²)`.
- `[empirical]`, measured at `d = 1024`:
  - Realistic, semantically correlated keys hold far fewer pairs than random
    keys: 58 instead of 257 at `ε = 0.5`. Mean-centring the keys recovers part
    of the gap (101).
  - The worst-case bound is conservative: recall@1 stays at or above 0.98 up
    to `n = 4d` with random values.
- `[empirical]`, in the paper's synthetic multi-hop setup: a softmax (modern
  Hopfield) readout removes the crosstalk that defeats the linear readout. At
  about 3,450 associations, the linear readout is near chance (1.9%), while the
  Hopfield readout decodes most hops (76–78%).
- The paper does not compare Hebbian writing with delta-rule writing, so the
  open question below remains.
- A related theory splits Hebbian retrieval interference into two parts
  (Zhang et al. 2026, arXiv:2610.09056):
  - finite-feature noise, which shrinks as the feature dimension grows;
  - structural interference from overlap between stored keys, which does not.

  The structural part is a capacity ceiling set by the geometry of the
  representation, not by its size.

## L3 Math

Planned outline (fill with `/deepen associative-memory L3`):

- The signal-to-noise argument for the classic Hopfield network: the
  crosstalk variance grows like `M/N`, which gives capacity proportional to
  `N`, and why the replica calculation sharpens this to `0.138`.
- The rank and counting bounds for `d × d` matrix memory.
- The delta rule as online least squares (one Kaczmarz or LMS step), and why
  it does not reach the batch least-squares solution in one pass.
- Ramsauer's energy function, and the separation condition behind
  exponential capacity.

## L4 Sources (reading order)

| # | Source | Why read it | Verified |
|---|---|---|---|
| 1 | Krotov, Hoover, Ram & Pham 2025, "Modern Methods in Associative Memory", arXiv:2507.06211 | Tutorial with notebooks; best entry point | yes |
| 2 | Ramsauer et al. 2020, "Hopfield Networks is All You Need", arXiv:2008.02217, ICLR 2021 | Attention equals a modern Hopfield update; capacity; metastable heads | yes |
| 3 | Schlag, Irie & Schmidhuber 2021, "Linear Transformers Are Secretly Fast Weight Programmers", arXiv:2102.11174, ICML | Linear attention as fast weights; capacity limit; delta rule | yes |
| 4 | Wang, Shi & Fox 2025, "Test-time regression", arXiv:2501.12352 | One framework for attention, SSMs and fast weights as memory | yes |
| 5 | Hopfield 1982, PNAS 79(8):2554, doi:10.1073/pnas.79.8.2554 | The origin | yes |
| 6 | Amit, Gutfreund & Sompolinsky 1985, "Storing infinite numbers of patterns in a spin-glass model of neural networks", PRL 55:1530 | The `0.138 N` capacity (metadata verified; value confirmed from secondary sources, PDF not read) | yes |
| 7 | Krotov & Hopfield 2016, "Dense Associative Memory for Pattern Recognition", arXiv:1606.01164, NeurIPS | Higher-order interactions raise capacity | yes |
| 8 | Demircigil, Heusel, Löwe, Upgang & Vermet 2017, "On a Model of Associative Memory with Huge Storage Capacity", arXiv:1702.01929, J. Stat. Phys. | Rigorous exponential capacity | yes |
| 9 | Krotov 2023, "A new frontier for Hopfield networks", Nature Reviews Physics, doi:10.1038/s42254-023-00595-y | Short perspective | yes (metadata only) |
| 10 | Abdulla et al. 2026, "TANSAR", arXiv:2611.12374 | Hebbian capacity under correlated keys | yes |
| 11 | Lee, Park, Kim & Ko 2026, "How Linear Attention Remembers", arXiv:2609.33093 | How pretrained GLA and GDN store and lose facts | yes |
| 12 | Zhang et al. 2026, "A Geometry-Based Capacity Theory for Finite-Feature Associative Memory", arXiv:2610.09056 | Geometry-dependent capacity ceiling | yes |
| 13 | Cabannes et al. 2026, "Sparse Delta Memory", arXiv:2607.07386 | Much larger state at equal FLOPs | yes |
| 14 | Zhao & Jones 2026, "Fast-weight Product Key Memory", arXiv:2601.00671 | Sparse test-time-trained memory; NIAH to 128K | yes |
| 15 | Ghriss & Chakraborty 2026, "Kernelized Linear Attention (KATA)", arXiv:2607.17419 | Feature geometry and capacity; Welch floor | yes (abstract only) |
| 16 | Geva, Schuster, Berant & Levy, "Transformer Feed-Forward Layers Are Key-Value Memories", arXiv:2012.14913, EMNLP | Parametric associative memory | yes |
| 17 | Jelassi et al. 2024, "Repeat After Me", arXiv:2402.01032, ICML | Fixed-state copying limit | yes |
| 18 | Chen, Wang & Xu 2026, "Kernel Ridge Attention", arXiv:2611.23896 | Recursive-least-squares writes; Kalman and kernel-ridge links | yes (full text) |
| 19 | Li, Behrouz, Deng, Kacham, Al-Rfou, Razaviyayn & Mirrokni 2026, "Toaster", arXiv:2611.23648 | MLP-state memory, with a state-matched control | yes (full text) |
| 20 | Mohsenvand 2026, "Attention at Absolute Zero", arXiv:2611.11937 | Zero-temperature limit of softmax; fixed `β` failing at scale | yes (full text) |

## Open questions

- [ ] What is the capacity of a `d × d` matrix memory written with the delta
      rule versus pure Hebbian (outer-product) writing? (2026-W47: TANSAR
      bounds the Hebbian side under correlated keys; the delta-rule side is
      still missing.)
- [ ] Does delta-rule writing recover the capacity that semantically
      correlated keys lose under Hebbian writing (TANSAR: 58 against 257
      pairs)? (2026-W47 update: KRA builds the least-squares write, but
      tests it only at about 2x state.)
- [ ] At matched state bytes, does a recursive-least-squares write beat the
      delta rule on MQAR capacity, especially with correlated keys? Does
      KRA's gain disappear at matched state, as most of Toaster's does?
- [ ] Does a zero-temperature or adaptive-`β` read help associative recall
      in language models, or only on exact algorithmic tasks?
- [ ] Do sparse-addressed memories (SDM, FwPKM) still beat dense matrix state
      when compared at equal state bytes, not only at equal FLOPs?
- [ ] In hybrids where the KV layers carry recall, how small can the
      recurrent state get before quality drops?

## Log

- 2026-11-17: stub created from the attention-efficiency card.
- 2026-11-18: added the TANSAR capacity bounds from the
  [2026-W47 radar](../radar/2026-W47.md).
- 2026-11-18: added L1 (composite photo versus photo album) and L2 (classic
  and modern Hopfield networks, mapping to linear and full attention).
  Verified Hopfield 1982, Krotov & Hopfield 2016 and Ramsauer et al. 2020
  with Semantic Scholar.
- 2026-11-19: `/investigate`: filled the seven questions, added the Hebbian
  versus delta-rule mechanism, an L3 outline and L4 (17 sources), plus three
  new open questions. Status changed from stub to draft.
  - Verified Amit et al. 1985 and Demircigil et al. 2017 (previously
    unverified). Refined `0.14 N` to `0.138 N`, with the replica caveat.
  - Replaced the seed notes with L4.
- 2026-11-20: applied the [2026-W47 radar update](../radar/2026-W47.md).
  - Added to Trade-off: KRA and Toaster, and the fixed-`β` failure from
    Attention at Absolute Zero.
  - Added to Boundary: the zero-temperature limit of softmax.
  - Added to Lineage: Kalman and Gaussian-process regression, and tropical
    algebra.
  - Added to Measurement: the state-matched control.
  - Updated the Combination speculation on least-squares writes.
  - Added L4 sources 18–20 and two open questions.
  - Spot-checked the Toaster and Absolute Zero numbers against the papers
    with alphaXiv.
