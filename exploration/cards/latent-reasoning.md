# Can a model reason in continuous vectors instead of words?

Status: stub
Last updated: 2026-11-20
Related: [multi-agent communication](multi-agent-communication.md)

## L0 Headline

Latent reasoning skips writing out a chain of thought token by token. Instead,
the model feeds continuous vectors back into itself: hidden states, or
probability-weighted mixtures of token embeddings. This can keep several
options open at once, but it is harder to read and to check.

## Seed notes (to expand with `/investigate latent-reasoning`)

- Coconut feeds the last hidden state back as the next input embedding.
  The authors report that it can keep several next steps open at once,
  like a breadth-first search, and that it beats chain of thought on
  planning-heavy logic tasks. Training is required (Hao et al. 2024,
  arXiv:2412.06769, verified).
- Soft Thinking feeds the probability-weighted average of token embeddings
  instead of one sampled token, without training (Zhang et al. 2025,
  arXiv:2505.15778, NeurIPS, verified).
- Stream of Belief passes Soft Thinking tokens between agents. Over the
  cycles, these tokens drift close to real word embeddings (arXiv:2611.21250).
  See [multi-agent communication](multi-agent-communication.md).

## Evidence from the 2026-W47 radar update

- **Hidden-state feedback wins in pretraining at matched compute.** Latent
  feedback (Huang, Dwivedi, Ma, Moreno & Liu 2026, arXiv:2611.20404) feeds
  each token's top-layer state into the next token's input. It is trained
  with one or two fixed-point passes and costs about 1.2x a Transformer's
  training FLOPs. `[empirical, self-reported]`
  - At equal unique data, it saves up to 48% of the compute that a
    Transformer would spend on more epochs.
  - At equal epochs, it saves up to 47% of the unique data.
  - It loses when unique data is scarce: below about 75 unique tokens per
    parameter at a one-epoch budget, and below about 33 at two.
  - Evidence:
    - models from 60M to 778M;
    - a scaling law fitted on 60M–271M predicts the held-out 778M within
      0.3%;
    - three seeds, at 134M only.
  - Caveats:
    - It measures pretraining loss and downstream bits per byte, with no
      reasoning test and no Coconut comparison.
    - When model size is free, a Transformer about 1.2x larger gets slightly
      lower loss. That model costs more per decoding step, though.
- **Longer latent chains can hurt.** Rethinking Fixed-Horizon Latent
  Reasoning (Chen et al. 2026, arXiv:2611.24001, abstract only)
  `[empirical]`:
  - Running a latent chain to its full preset length can lower accuracy:
    later steps reshuffle the candidates and weaken the right one.
  - Stopping adaptively gives up to +7.2 points with 29% less latent compute.
  - Arithmetic benchmarks only.
- **Lineage: recurrence in depth.** Looped models rerun their layers within
  one token instead of feeding states across tokens:
  - Loopback Transformer (Ouyang et al. 2026, arXiv:2611.07226, abstract
    only);
  - Late Entry in Looped Language Models (Jin et al. 2026, arXiv:2611.24576,
    abstract only).

  The latent-feedback paper draws the cost difference: a looped model pays
  its extra compute at every decoding step, while latent feedback pays it only
  in training and prefill.

## Open questions

- [ ] Do latent chains of thought beat text chains of thought at equal
      compute on tasks that need search, beyond small logic benchmarks?
- [ ] Does hidden-state feedback that helps pretraining (arXiv:2611.20404)
      also give Coconut-style reasoning gains without a separate latent
      training stage?

## Log

- 2026-11-19: stub created from the multi-agent-communication card.
- 2026-11-20: added latent feedback, the fixed-horizon result and looped
  models from the [2026-W47 radar update](../radar/2026-W47.md).
  - Spot-checked the latent-feedback numbers against the paper with alphaXiv.
  - The other three papers are from abstracts only.
  - Status stays stub.
