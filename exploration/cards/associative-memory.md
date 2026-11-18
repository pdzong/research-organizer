# What limits how much an associative memory can store and retrieve?

Status: stub
Last updated: 2026-11-18
Related: [attention efficiency](attention-efficiency.md)

## L0 Headline

Attention, linear attention and Hopfield networks can all be read as
associative memories: store key-to-value pairs, retrieve a value from a cue.
Their capacity and retrieval cost explain many architecture trade-offs.

## Seed notes (to expand with `/investigate associative-memory`)

- Classical Hopfield networks store about `0.14 N` patterns in `N` neurons
  before retrieval breaks down (Amit, Gutfreund & Sompolinsky 1985). (unverified)
- Dense associative memories and modern Hopfield networks raise capacity to
  exponential in `N` (Krotov & Hopfield 2016, arXiv:1606.01164; Demircigil et
  al. 2017, arXiv:1702.01929). (unverified)
- Softmax attention equals one retrieval step of a modern Hopfield network
  (Ramsauer et al. 2020, arXiv:2008.02217). (unverified)
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
