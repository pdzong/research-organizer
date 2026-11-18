# What does it mean for a layer to learn at test time?

Status: stub
Last updated: 2026-11-18
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

## Evidence on state size (from the 2026-W47 radar)

- `[empirical]` Recurrent states in production hybrid models are effectively
  low-rank (Jiang et al. 2026, "SinkState", arXiv:2611.14246).
  - Where: Gated DeltaNet and Mamba-2 layers of Nemotron-3, Qwen3.5-9B and
    Qwen3-Next.
  - Why: the queries, keys and values of these layers lie in a stable
    low-dimensional subspace.
  - What it buys: keeping each state in adaptive low-rank SVD form cuts peak
    state memory 1.9x on average (up to 2.6x), with at most −0.1 points on
    RULER NIAH at 16K.
  - Caveat: the rank depends on the data, and Gated DeltaNet states keep a
    higher rank than Mamba-2 states.

  This matters for "recall per byte of state": real matrix states seem to use
  far less than their nominal capacity. `[interpretation]`

## Naming caution

"Test-time training" names two different things:

- **A test-time-training layer** (Sun et al. 2024; Titans): the recurrent
  state is itself a small model, updated online for every token. This card is
  about this one.
- **Test-time fine-tuning of the weights.** Example: Microfitting (Ryan et al.
  2026, arXiv:2611.20258) trains and caches one LoRA adapter per document on a
  frozen DeepSeek V4 Flash. That is per-document adaptation, not a
  test-time-training layer.

## Open questions

- [ ] Does a more expressive state model (an MLP instead of a matrix) raise
      recall capacity per byte of state?

## Log

- 2026-11-17: stub created from the attention-efficiency card.
- 2026-11-18: added the SinkState low-rank evidence and the naming caution
  from the [2026-W47 radar](../radar/2026-W47.md).
