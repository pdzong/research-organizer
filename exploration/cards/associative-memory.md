# What limits how much an associative memory can store and retrieve?

Status: stub
Last updated: 2026-11-17
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

## Open questions

- [ ] What is the capacity of a `d × d` matrix memory written with the delta
      rule versus pure Hebbian (outer-product) writing?

## Log

- 2026-11-17: stub created from the attention-efficiency card.
