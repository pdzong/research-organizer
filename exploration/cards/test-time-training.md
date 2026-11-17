# What does it mean for a layer to learn at test time?

Status: stub
Last updated: 2026-11-17
Related: [attention efficiency](attention-efficiency.md) ·
[associative memory](associative-memory.md)

## L0 Headline

Some recurrent layers treat their state as a small model that is trained by
gradient descent on the sequence while the main model runs. The delta rule is
one such gradient step, which ties linear attention to online learning.

## Seed notes (to expand with `/investigate test-time-training`)

- One delta-rule update equals one gradient step on `‖S k − v‖²`.
  `[interpretation]`, standard derivation; verify a source that states it.
- TTT layers use a small model as the hidden state (Sun et al. 2024,
  arXiv:2407.04620). (unverified)
- Titans adds a learned long-term memory updated at test time (Behrouz et al.
  2025, arXiv:2501.00663). (unverified)

## Open questions

- [ ] Does a more expressive state model (an MLP instead of a matrix) raise
      recall capacity per byte of state?

## Log

- 2026-11-17: stub created from the attention-efficiency card.
