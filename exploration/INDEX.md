# Index

## Cards

| Card | Status | One line |
|---|---|---|
| [How far can attention be cut without losing quality?](cards/attention-efficiency.md) | draft | Cheap layers trade exact recall for cost; hybrids keep a few exact-access layers. |
| [What limits associative memory capacity?](cards/associative-memory.md) | stub | Attention and Hopfield networks as memories; capacity from statistical physics. |
| [State space models and control theory](cards/state-space-models.md) | stub | Fixed-state sequence models inherited from linear systems; diagonal ones track only commutative structure. |
| [Learning at test time](cards/test-time-training.md) | stub | Recurrent state as a small model trained online. |

## Open questions (collected from cards)

The `/radar` skill checks new papers against this list.

- [attention-efficiency] Scaling law for the minimum fraction of exact-access
  layers versus task recall demand.
- [attention-efficiency] At 1M tokens, is recall in no-full-attention models
  carried by sparse attention or by fixed-state layers?
- [attention-efficiency] Any sub-linear-memory architecture that beats the
  Based recall-throughput frontier? (Bilateral log-linear attention: more
  recall at about 2x state, not settled.)
- [attention-efficiency] Failure modes of sparse attention selectors. Partly
  answered: block pooling misranks needles in a few heads; open for
  token-level selectors.
- [attention-efficiency] Do test-time-training layers change the capacity
  picture?
- [associative-memory] Capacity of delta-rule versus Hebbian matrix memory.
  (Hebbian side bounded under correlated keys; delta-rule side open.)
- [state-space-models] Useful control-theory analogues for SSM training or
  capacity. (Partly answered: Hankel singular values, for time-invariant
  filters only.)
- [test-time-training] Recall capacity per byte of state for MLP versus matrix
  state.

## Radar reports

- [2026-W47](radar/2026-W47.md): sparse-attention selectors fail in a few
  pooled heads (fixable); proofs that diagonal SSMs track only commutative
  structure; bilateral log-linear attention boosts recall at about 2x state.
