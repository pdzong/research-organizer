# What limits how much an associative memory can store and retrieve?

Status: stub
Last updated: 2026-11-18
Related: [attention efficiency](attention-efficiency.md)

## L0 Headline

Attention, linear attention and Hopfield networks can all be read as
associative memories: store key-to-value pairs, retrieve a value from a cue.
Their capacity and retrieval cost explain many architecture trade-offs.

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
- Capacity: about `0.14 N` patterns before the patterns interfere and recall
  fails. This is a classic result, see the seed notes; not yet verified in the
  vault.

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
  (Krotov & Hopfield 2016, arXiv:1606.01164, for dense associative memories;
  Ramsauer et al. 2020 for the continuous version).

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

## Seed notes (to expand with `/investigate associative-memory`)

- Classical Hopfield networks store about `0.14 N` patterns in `N` neurons
  before retrieval breaks down (Amit, Gutfreund & Sompolinsky 1985). (unverified)
- Dense associative memories and modern Hopfield networks raise capacity to
  exponential in `N` (Krotov & Hopfield 2016, arXiv:1606.01164, verified;
  Demircigil et al. 2017, arXiv:1702.01929, unverified).
- Softmax attention equals one retrieval step of a modern Hopfield network
  (Ramsauer et al. 2020, arXiv:2008.02217, verified).
- Physics angle: capacity results come from the statistical mechanics of spin
  glasses, a direct bridge from physics to architecture limits.

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

## Open questions

- [ ] What is the capacity of a `d × d` matrix memory written with the delta
      rule versus pure Hebbian (outer-product) writing? (2026-W47: TANSAR
      bounds the Hebbian side under correlated keys; the delta-rule side is
      still missing.)

## Log

- 2026-11-17: stub created from the attention-efficiency card.
- 2026-11-18: added the TANSAR capacity bounds from the
  [2026-W47 radar](../radar/2026-W47.md).
- 2026-11-18: added L1 (composite photo versus photo album) and L2 (classic
  and modern Hopfield networks, mapping to linear and full attention).
  Verified Hopfield 1982, Krotov & Hopfield 2016 and Ramsauer et al. 2020
  with Semantic Scholar.
