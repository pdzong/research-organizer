# What are state space models, and what do they inherit from control theory?

Status: stub
Last updated: 2026-11-18
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

## Boundary notes (from the 2026-W47 radar)

- `[proven, within the paper's model]` What a linear recurrence can track
  depends on the group its transitions generate. The update is a
  representation of the input monoid, and a channel can track a group only if
  that group is a quotient of the group its transitions generate. The model
  assumes compact reachable states, a continuous readout and no decay.
  (Shikder, Dey, Mináč & Muller 2026, "Symmetry in Time", arXiv:2611.17162,
  [code](https://github.com/anifshikder/HyperSSM).)
  - Diagonal real or complex SSMs (Mamba-1/2 style) commute, so they track
    only abelian groups: parity and counting modulo `n`, but not S3 or A5.
  - A stack of `L` commutative layers tracks a finite group only if the group
    is solvable with derived length at most `L`, so no such stack reaches S5.
  - One quaternion channel (4 numbers of state) tracks A5. On synthetic tasks
    it stays exact up to 25 times the training length `[empirical]`. Whether
    this helps large models is the paper's own main open question.
- `[proven, for linear time-invariant filters]` Hankel singular values bound
  how well an `n`-state filter can approximate a target response: the error is
  at least `σ_{n+1}` (Eckart–Young, Adamjan–Arov–Krein). A delay line, which
  recalls one exact past token, needs all its states, while averaging
  compresses well (Pei 2026, Zenodo doi:10.5281/zenodo.24191078). This does not
  cover data-dependent (selective) SSMs.

## Open questions

- [ ] Which control-theory results (stability, controllability, observability)
      have useful analogues for SSM training or capacity? Partly answered
      (2026-W47): Hankel singular values and balanced truncation (model-order
      reduction) give a retrieval lower bound for time-invariant filters.
      Still open for selective SSMs.
- [ ] Where do delta-rule transitions (Householder-like, not diagonal) sit in
      the representation-theory picture? Gated DeltaProduct scores near chance
      on S5 with 32 generators (1.23% against 0.83% chance; baseline copied
      from prior work in arXiv:2611.17162). That suggests being non-diagonal
      is not enough on its own.

## Log

- 2026-11-17: stub created from the attention-efficiency card.
- 2026-11-18: added boundary notes from the
  [2026-W47 radar](../radar/2026-W47.md): group-tracking limits of diagonal
  SSMs and the Hankel retrieval bound.
- 2026-11-18: added open questions raised by the 2026-W47 radar.
