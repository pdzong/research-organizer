# What do looped (recurrent-depth) transformers buy?

Status: stub
Last updated: 2026-11-22
Related: [latent reasoning](latent-reasoning.md) ·
[test-time training](test-time-training.md) ·
[state space models](state-space-models.md)

## L0 Headline

A looped transformer reruns the same block of layers several times for each
token, so it can spend more compute at test time without more parameters or
more written tokens. The open question is whether that extra depth beats
spending the same compute on a wider model or on a written chain of thought.

## Seed notes (to expand with `/investigate looped-transformers`)

- Huginn: a 3.5B model trained on 800B tokens that loops a 4-layer core
  block. Iteration counts are sampled during training.
  `[empirical, self-reported]`
  - On GSM8k with a chain of thought, it goes from 0% at one iteration to
    34.8% strict match at 32. The authors equate that compute to a 50B fixed
    model.
  - Its non-recurrent twin is not matched on FLOPs, so this does not show a
    better trade-off.

  Source: Geiping et al. 2025, arXiv:2502.05171, NeurIPS (verified, full
  text).
- **Ouro** (Zhu et al. 2025, arXiv:2510.25741): open looped language models
  of 1.4B and 2.6B, trained on 7.7T tokens. They match 4B and 8B standard
  transformers on most benchmarks, but the comparison is not FLOP-matched.
  Looping leaves knowledge storage at about 2 bits per parameter and helps
  knowledge manipulation. `[empirical, self-reported]` (partly read). See
  [latent reasoning at scale](latent-reasoning-scaling.md).
- Loopback Transformer (Ouyang et al. 2026, arXiv:2611.07226, abstract
  only).
- Late Entry in Looped Language Models (Jin et al. 2026, arXiv:2611.24576,
  abstract only).
- From Chain-of-Thought to Loops: Non-Autoregressive Latent Reasoning via
  Looped Transformers (arXiv:2610.11472; title from alphaXiv search, not
  read).
- The cost difference with latent feedback across tokens
  (arXiv:2611.20404): a looped model pays its extra compute at every
  decoding step, while latent feedback pays it only in training and prefill.
  See [latent reasoning](latent-reasoning.md).
- BDH-CQ from Pathway (arXiv:2608.09888) iterates a latent workspace over
  depth after writing the demonstrations into a recurrent memory. Its latent
  effort setting scales ARC-AGI-1 pass@2 from 21% to 29.5%. Details are in
  [latent reasoning](latent-reasoning.md). `[empirical, self-reported]`

## Open questions

- [ ] At matched training and inference FLOPs, does a looped transformer beat
      a wider fixed-depth model on reasoning benchmarks?
- [ ] Do looped models need adaptive halting for the same reason latent
      chains do (arXiv:2611.24001)?

## Log

- 2026-11-20: stub created from the latent-reasoning card.
- 2026-11-22: added a pointer to BDH-CQ.
- 2026-11-25: added Ouro, from the latent-reasoning-scaling investigation.
