# When should parameters be reserved for some tokens and not others?

Status: stub
Last updated: 2026-11-18
Related: [vision encoder](vision-encoder.md) ·
[attention efficiency](attention-efficiency.md)

## L0 Headline

Mixture-of-experts layers give each token only some of the model's parameters,
chosen by a router or fixed by token type such as modality. This trades total
parameters for compute per token. In multimodal models it is also a way to
give image tokens dedicated capacity inside a shared model.

## Seed notes (to expand with `/investigate mixture-of-experts`)

- Fixed routing by modality:
  - VLMo's mixture-of-modality-experts shares attention and gives each
    modality its own feed-forward expert (Bao et al. 2021,
    arXiv:2111.02358).
  - BEiT-3 calls this a multiway Transformer (Wang et al. 2022,
    arXiv:2208.10442).
  - Mixture-of-Transformers separates all non-embedding parameters by
    modality (Liang et al. 2024, arXiv:2411.04996).
- `[empirical]` Vision-only parameters in the first 8 layers of a dense
  backbone match a separate vision encoder on VQA. Spreading the same
  parameters over all tokens does worse (Brown, Hoang et al. 2026,
  arXiv:2611.17334). See [vision encoder](vision-encoder.md).
- `[empirical]` In native multimodal models trained from scratch, sparse MoE
  beats dense at equal active parameters. Modality-agnostic routing beats
  modality-aware routing on loss (Shukor et al. 2025, arXiv:2504.07951;
  numbers from alphaXiv's summary, check the PDF).
- `[empirical]` In encoder-free MoE models, routing for visual tokens is more
  concentrated than for text, consistent with visual experts forming (Chen et
  al. 2026, arXiv:2609.35457; from alphaXiv's summary).

## Open questions

- [ ] Do learned routers discover modality specialisation that matches
      hand-reserved vision parameters on downstream VQA, or does reservation
      still win?

## Log

- 2026-11-18: stub created from the vision-encoder card.
