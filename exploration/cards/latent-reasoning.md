# Can a model reason in continuous vectors instead of words?

Status: stub
Last updated: 2026-11-19
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

## Open questions

- [ ] Do latent chains of thought beat text chains of thought at equal
      compute on tasks that need search, beyond small logic benchmarks?

## Log

- 2026-11-19: stub created from the multi-agent-communication card.
