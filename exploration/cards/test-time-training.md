# What does it mean for a layer to learn at test time?

Status: stub
Last updated: 2026-11-20
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

## Richer state or richer optimiser (from the 2026-W47 radar update)

- **An MLP state at matched state size.** Toaster (Li et al. 2026, Google
  Research, arXiv:2611.23648) does this:
  - It chains two delta-rule memories with a GELU between them, and trains
    the hidden one by target propagation.
  - Each layer still runs on the existing KDA kernel.
  - Results `[empirical, self-reported]`, single runs:
    - C4 perplexity at 1.2B is 9.94, against 10.00 for KDA and 9.96 for
      attention.
    - The state is about 8x KDA's.
    - Its state-matched control at 145M, in C4 perplexity:

      | State (x default KDA) | 2x | 4x | 8x |
      |---|---|---|---|
      | KDA, wider heads | 15.96 | 15.84 | 15.79 |
      | Toaster, wider hidden layer | 15.90 | 15.76 | 15.69 |

      Default KDA scores 16.00. About two-thirds of Toaster's gain comes from
      the larger state. The MLP shape adds the remaining 0.06–0.10 at every
      matched size.
  - This is the first partial answer to the open question below about recall
    per byte. It measures perplexity, though, not recall capacity. On RULER
    single-needle at 4K, Toaster scores 62.7 against KDA's 37.3 on S-NIAH-2,
    and 27.3 against 28.0 on S-NIAH-3.
- **A better optimiser on a matrix state.** Kernel Ridge Attention (Chen,
  Wang & Xu 2026, arXiv:2611.23896) keeps a matrix state but writes with
  recursive least squares, a second-order online step, instead of one
  gradient step.
  - It wins on rare-token recall at about 31M parameters, but with about 1.9x
    Gated DeltaNet's state. `[empirical, self-reported]`
  - See [associative memory](associative-memory.md).
- **Template for this card.** Any claim that a richer state model helps
  should come with a baseline given the same state bytes, as Toaster does.

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
      recall capacity per byte of state? (2026-W47 update: for perplexity,
      Toaster keeps a small edge at matched state; recall capacity is still
      untested.)
- [ ] Why are production recurrent states effectively low-rank
      (arXiv:2611.14246)? Is capacity left unused because of training, or do
      the tasks simply not need more? A test would be to train a model so it
      fills its state, then check whether recall improves at the same state
      size.

## Log

- 2026-11-17: stub created from the attention-efficiency card.
- 2026-11-18: added the SinkState low-rank evidence and the naming caution
  from the [2026-W47 radar](../radar/2026-W47.md).
- 2026-11-18: added open questions raised by the 2026-W47 radar.
- 2026-11-20: added Toaster's state-matched control and KRA, from the
  [2026-W47 radar update](../radar/2026-W47.md). Spot-checked Toaster's
  Table 16 against the paper with alphaXiv.
