# Index

## Cards

| Card | Status | One line |
|---|---|---|
| [How far can attention be cut without losing quality?](cards/attention-efficiency.md) | draft | Cheap layers trade exact recall for cost; hybrids keep a few exact-access layers. |
| [What limits associative memory capacity?](cards/associative-memory.md) | draft | One fixed matrix holds about as many clean associations as its dimension; exact recall needs memory that grows with what is stored. |
| [State space models and control theory](cards/state-space-models.md) | stub | Fixed-state sequence models inherited from linear systems; diagonal ones track only commutative structure. |
| [Learning at test time](cards/test-time-training.md) | stub | Recurrent state as a small model trained online. |
| [Does a multimodal model need a separate, pretrained vision encoder?](cards/vision-encoder.md) | draft | Pretrained prior optional, dedicated vision parameters essential, and they can sit in the first backbone layers. |
| [When should parameters be reserved for some tokens?](cards/mixture-of-experts.md) | stub | Mixture of experts and modality-specific parameters. |
| [Do LLM agents reason better together, and does latent talk help?](cards/multi-agent-communication.md) | draft | Voting explains most debate gains (pooled: about 4 points below matched baselines); latent beliefs cut tokens but do not yet beat text debate. |
| [Can a model reason in continuous vectors instead of words?](cards/latent-reasoning.md) | stub | Coconut and Soft Thinking: chain of thought without tokens; hidden-state feedback already wins in pretraining at matched compute. |

## Open questions (collected from cards)

The `/radar` skill checks new papers against this list.

- [attention-efficiency] Scaling law for the minimum fraction of exact-access
  layers versus task recall demand. (FlashMorph2 searches per model; no law.)
- [attention-efficiency] At 1M tokens, is recall in no-full-attention models
  carried by sparse attention or by fixed-state layers?
- [attention-efficiency] Any sub-linear-memory architecture that beats the
  Based recall-throughput frontier? (Bilateral log-linear attention: more
  recall at about 2x state, not settled.)
- [attention-efficiency] Failure modes of sparse attention selectors. Partly
  answered: block pooling misranks needles in a few heads.
- [attention-efficiency] Do token-level selectors (DeepSeek Sparse Attention)
  have their own blind spots on harder multi-key tasks?
- [attention-efficiency] Does bf16 round-to-nearest recurrent state also hurt
  associative recall, not only reasoning length?
- [attention-efficiency] Do test-time-training layers change the capacity
  picture?
- [associative-memory] Capacity of delta-rule versus Hebbian matrix memory.
  (Hebbian side bounded under correlated keys; delta-rule side open.)
- [associative-memory] Does delta-rule writing recover the capacity lost to
  semantically correlated keys? (KRA builds the least-squares write, tested
  only at about 2x state.)
- [associative-memory] At matched state bytes, does a recursive-least-squares
  write beat the delta rule on MQAR capacity? Does KRA's gain vanish at
  matched state, as most of Toaster's does?
- [associative-memory] Does a zero-temperature or adaptive-β read help
  associative recall in language models, or only on exact algorithmic tasks?
- [associative-memory] Do sparse-addressed memories (SDM, FwPKM) beat dense
  matrix state at equal state bytes, not only equal FLOPs?
- [associative-memory] In hybrids where KV layers carry recall, how small can
  the recurrent state get?
- [state-space-models] Useful control-theory analogues for SSM training or
  capacity. (Partly answered: Hankel singular values, for time-invariant
  filters only.)
- [state-space-models] Where do delta-rule (Householder-like) transitions sit
  in the group-tracking picture?
- [test-time-training] Recall capacity per byte of state for MLP versus matrix
  state. (Perplexity: Toaster keeps a small edge at matched state; recall
  untested.)
- [test-time-training] Why are production recurrent states low-rank: unused
  capacity or no need for more?
- [vision-encoder] Does the ~3x encoder-free penalty hold at native
  resolution, on text-rich data, and beyond 6.4B parameters?
- [vision-encoder] Under one compute accounting, do Chen et al.'s extrapolated
  crossover and Brown–Hoang's constant gap still disagree?
- [vision-encoder] On downstream VQA, does modality-aware vision capacity beat
  modality-agnostic MoE routing?
- [vision-encoder] How small can dedicated vision capacity be before VQA drops?
- [vision-encoder] Do encoders pretrained on much more data (SigLIP 2, DINOv3)
  beat a scratch encoder at matched lifetime compute? (V-JEPA-LM: the kind of
  prior matters too.)
- [mixture-of-experts] Do learned routers match hand-reserved vision
  parameters on downstream VQA?
- [multi-agent-communication] Does Stream of Belief beat an `N × K`-sample
  self-consistency vote at equal total compute? (Text methods trail such
  baselines by about 4 points on average.)
- [multi-agent-communication] Does any debate protocol clear the `a/(1−a)`
  selectivity bar in each round?
- [multi-agent-communication] Under a message-replacement audit, how much of
  the gain comes from example-specific belief content?
- [multi-agent-communication] Can latent belief exchange work across model
  families without a trained bridge?
- [multi-agent-communication] Does latent exchange avoid the interaction tax
  (diversity collapse) better than text?
- [latent-reasoning] Do latent chains of thought beat text chains of thought
  at equal compute beyond small logic benchmarks?
- [latent-reasoning] Does hidden-state feedback that helps pretraining also
  give Coconut-style reasoning gains without a separate latent stage?

## Radar reports

- [2026-W47](radar/2026-W47.md): sparse-attention selectors fail in a few
  pooled heads (fixable); proofs that diagonal SSMs track only commutative
  structure; bilateral log-linear attention boosts recall at about 2x state.
  Update 20 Nov: least-squares and MLP-state memory writes win only with a
  bigger state; multi-agent systems trail matched baselines by about 4
  points; zero-temperature attention keeps retrieval exact as item counts
  grow.
