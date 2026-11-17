# What are state space models, and what do they inherit from control theory?

Status: stub
Last updated: 2026-11-17
Related: [attention efficiency](attention-efficiency.md)

## L0 Headline

State space models (S4, Mamba, Mamba-2) process sequences with a fixed-size
state updated at each step, an idea taken from linear systems and signal
processing. They are fast and memory-light but share the fixed-state recall
limit.

## Seed notes (to expand with `/investigate state-space-models`)

- Mamba makes the state update input-dependent ("selective") (Gu & Dao 2023,
  arXiv:2312.00752). (unverified)
- Mamba-2 shows a duality between structured SSMs and a form of linear
  attention (Dao & Gu 2024, arXiv:2405.21060). (unverified)
- Lineage to trace: Kalman filter, linear time-invariant systems, HiPPO
  memory projections, S4.

## Open questions

- [ ] Which control-theory results (stability, controllability, observability)
      have useful analogues for SSM training or capacity?

## Log

- 2026-11-17: stub created from the attention-efficiency card.
