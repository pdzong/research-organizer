# Does a multimodal model need a separate, pretrained vision encoder?

Status: draft
Last updated: 2026-11-18
Related: [mixture of experts](mixture-of-experts.md) ·
[attention efficiency](attention-efficiency.md)

## L0 Headline

A vision encoder bundles three separate choices:
- a visual prior learned in separate pretraining;
- parameters reserved for image tokens;
- the placement of those parameters before images and text mix.

The strongest controlled study so far finds the prior optional and the
reserved parameters essential. The parameters can also move inside the
language model's first layers, which cuts the time to the first output token.

## L1 Intuition

Analogy: a team that works in English receives documents in a foreign
language.

- **Pretrained encoder.** The team hires an experienced outside translation
  agency. Every document is translated before the team sees it.
- **Encoder trained from scratch.** The team builds its own translation desk
  and trains it on the job.
- **Encoder-free.** Every team member reads the raw foreign text. Nobody
  specialises.
- **In-fusion capacity.** A few specialists sit in the team's first meetings
  and only handle the foreign documents.

The study's answer, in this picture: an in-house desk is as good as the outside
agency at the same total cost, and having specialists matters. Whether they
work in a separate room or in the first meetings matters little, and the first
meetings are faster.

Where the analogy breaks:

- A translator outputs a fixed language. A jointly trained encoder's outputs
  co-adapt with the language model, so there is no fixed "translation".
- "Specialists" are parameters that only image tokens pass through, not
  people. In-fusion specialists also share attention with the text tokens in
  the same layers.
- "Same total cost" is a compute-accounting choice: the agency's training
  FLOPs are charged to the team. If the agency is treated as free, the picture
  changes a little, but not in the agency's favour in this study
  (arXiv:2611.17334, §6.1).

## The seven questions

### 1. Scarce resource

- **Lifetime training compute**, counting every stage, including the encoder's
  own pretraining. Comparisons that ignore encoder pretraining favour
  pretrained encoders.
- **Time to first token at inference.** A separate encoder runs before the
  language model can start.
- **Vision tokens in the context.** One 448×448 image is 1,024 tokens in the
  main study, so images compete with text for sequence length.
- **Text-rich training data** (documents, charts, OCR). This is where the
  options differ most.

### 2. Trade-off

All results here are from Brown, Hoang et al. 2026 (arXiv:2611.17334), 1.7B
and 4B dense backbones with 0.4B of vision parameters, at matched lifetime
compute. `[empirical]`, single study, self-reported.

| Option | What you gain | What you give up |
|---|---|---|
| Encoder-free | Simplest design; fastest first token (146 ms against 210 ms at 1.7B on one H200) | Visual understanding: it needs about 3x the compute to match a scratch encoder on visual question answering (VQA), worst on OCR and charts (25.2 against 38.2 at 1.7B) |
| Encoder trained from scratch | Same quality as a pretrained encoder, with no separate pretraining stage | Nothing measurable against pretrained, at matched lifetime compute |
| In-fusion capacity (layers 1–8) | Matches the encoder on VQA; 13–27% lower time to first token at 1.7B | Another architectural choice: where the parameters go matters (late layers lose) |

Does the work move the frontier? The pretrained-versus-scratch result does not:
it is an accounting result that removes a training stage at no quality cost.
In-fusion placement does move a small frontier, visual quality against time
to first token: it keeps the same VQA with a faster first token.
`[empirical]`, measured at 1.7B and 4B only.

### 3. Boundary

No theorem is known. The evidence is empirical, and the studies disagree.

- `[empirical]` Giving the parameters to the shared backbone does not
  substitute for reserved vision capacity.
  - Encoder-free with the backbone enlarged by the encoder's 0.4B parameters
    (wider, deeper, or both): Avg. VQA 38.6–38.8, against 44.4 for the scratch
    encoder. Text improves instead.
  - Spreading the same parameters over all tokens in layers 1–8 recovers less
    than reserving them for vision tokens: 40.1–42.3 against 45.0.
  - Source: arXiv:2611.17334, Table 2 and §5.2.
- `[empirical]` The encoder-free penalty did not shrink with scale. Across 1.7B
  to 6.4B backbones, encoder-free needs 2.6–3.1x the compute to match the
  encoder on Avg. VQA (arXiv:2611.17334, §5.4).
- The studies disagree:
  - **Shukor et al. 2025** (arXiv:2504.07951) find early fusion (no separate
    encoder) and late fusion reach near-identical validation loss at equal
    FLOPs, with early fusion slightly ahead at all scales tested (0.3B to 4B).
    `[empirical]`
  - **Chen et al. 2026** (arXiv:2609.35457) find encoder-free models behind
    on multimodal loss but improving faster: the loss-compute exponent is
    0.378, against 0.300 for the encoder. A crossover is extrapolated near
    6.1e21 FLOPs, with an 80% bootstrap interval of 4.2e21 to 1.0e22. Their
    largest downstream model still trails (51.2 against 57.7). `[empirical]`
    for the measured range, `[speculation]` for the crossover, since it is
    extrapolated. These numbers come from alphaXiv's structured summary and
    still need checking against the PDF.
  - **Brown, Hoang et al. 2026** (arXiv:2611.17334) ran budgets up to 2.9e22
    FLOPs, above that projected crossover, and still found the roughly 3x
    downstream gap. Their explanation for Shukor et al.'s result (§D.4):
    averaged loss hides the vision signal, and the scratch encoder there may
    have been undertrained. That explanation is `[interpretation]` and was not
    tested directly.
  - Which is stronger: for downstream visual understanding, the
    Brown–Hoang study. It has a separate vision metric, five sizes, matched
    lifetime compute, and a parameter-matched control. Chen et al. agree on a
    remaining downstream gap at their largest scale.
  - Caveats on both sides: Chen et al. count compute differently (decoder FLOPs
    per token; whether encoder FLOPs count is not stated), so their crossover
    and the Brown–Hoang budgets are not directly comparable. All three studies
    use about 224px training images.
- `[empirical]` Encoder-free models build an encoder anyway (Harwath et al.
  2026, arXiv:2610.24239).
  - In Gemma-4 12B, image and audio representations stay nearly independent
    of context up to about layer 12 (linear CKA above 0.9), and later layers
    mix modalities.
  - Distilling those layers for audio keeps most of the performance at about
    7% of the size. The implicit encoder is much larger than it needs to be.
  - Analysis of two models only, with no matched-compute comparison.

### 4. Lineage

- **Patch embeddings.** The Vision Transformer (ViT) cuts an image into 16×16
  patches and treats them as tokens (Dosovitskiy et al. 2020,
  arXiv:2010.11929). An encoder-free model is a ViT patch embedding fed
  straight into a language model.
- **Pretrained priors.** CLIP learns image features from image–text pairs with
  a contrastive loss (Radford et al. 2021, arXiv:2103.00020). SigLIP and
  SigLIP 2 use a sigmoid loss (Zhai et al. 2023, arXiv:2303.15343; Tschannen
  et al. 2025, arXiv:2502.14786). LLaVA connected such an encoder to a
  language model through a projection (Liu et al. 2023, arXiv:2304.08485),
  and that became the default recipe.
- **Encoder-free models.**
  - Fuyu-8B fed raw patches to the decoder (Adept AI 2023, blog
    <https://www.adept.ai/blog/fuyu-8b/>, unverified, cited by 2611.17334).
  - EVE and EVEv2 (Diao et al. 2024, arXiv:2406.11832; Diao et al. 2025,
    arXiv:2502.06788).
  - Chameleon, which tokenizes images as discrete codes in one early-fusion
    model (Chameleon Team 2024, arXiv:2405.09818).
- **Modality-specific parameters inside a shared model.** This is the direct
  ancestor of "in-fusion capacity".
  - VLMo's mixture-of-modality-experts and BEiT-3's multiway Transformer share
    attention but give each modality its own feed-forward expert (Bao et al.
    2021, arXiv:2111.02358; Wang et al. 2022, arXiv:2208.10442).
  - Mixture-of-Transformers separates all non-embedding parameters by modality
    (Liang et al. 2024, arXiv:2411.04996).
  - See [mixture of experts](mixture-of-experts.md).
- `[interpretation]` Neuroscience: the visual cortex runs dedicated,
  vision-only processing before multimodal association areas. Brown–Hoang's
  best layout (vision-only parameters early in a shared stack) looks like that.
  The analogy breaks because the in-fusion layers already let image and text
  tokens attend to each other.

### 5. Measurement

- **Text-rich benchmarks expose the loss first:** OCRBench, ChartQA, DocVQA
  and TextVQA. Averaged VQA, and especially averaged validation loss, can hide
  the gap.
- **Matched lifetime compute, with encoder pretraining charged.** Without
  this, a pretrained encoder looks free.
- **Separate vision and text metrics.** Encoder-free models can gain on text
  while losing on vision.
- **Falsifiers:**
  - An encoder-free model, with the encoder's parameters added to the shared
    backbone, that matches a scratch encoder on OCR and charts at equal
    lifetime compute, at 6B or more and at native resolution.
  - In-fusion capacity in late layers matching early layers.
  - Longer encoder pretraining improving downstream VQA when its compute is
    free. In the Brown–Hoang study it did not: ImageNet probe accuracy rose
    from 80.4% to 84.4%, but VQA was best with the shortest pretraining
    (§6.1).

### 6. Adoption

- **Most production models still use a pretrained encoder** (SigLIP- or
  CLIP-style), according to Brown–Hoang's survey (arXiv:2611.17334, §1).
- **Gemma 4 is encoder-free.** Harwath et al. analyse Gemma-4 12B as feeding
  linearly projected 48×48 patches straight into the decoder
  (arXiv:2610.24239). Gemma 4 Technical Report: arXiv:2607.02770.
- **Inkling-Small** (Thinking Machines) embeds 40×40 patches with a 4-layer MLP,
  which is a small amount of dedicated vision capacity (arXiv:2610.24239).
- **Kimi K3 trains its vision encoder from scratch**, jointly with the
  backbone, according to Brown–Hoang (Kimi K3 report: arXiv:2607.24653, not
  read here).
- No released checkpoints or code accompany the Brown–Hoang study. Only a
  blog exists: <https://unbundling.github.io>.

### 7. Combination

- **Mixture-of-experts backbones.** Brown–Hoang name sparse MoE as the next
  step, with experts that could host modality-routed vision capacity. There is
  a tension: Shukor et al. found modality-agnostic routing beats
  modality-aware routing (on loss), while Brown–Hoang find reserving
  parameters for vision tokens matters (on VQA).
- **Unified understanding and generation.** Pixel-embedding models such as
  Tuna-2 drop the encoder so one representation serves both directions (Liu et
  al. 2026, arXiv:2604.24763, read from the abstract only).
- **Efficient attention.** Images add about 1,000 tokens each, and video far
  more, so the [attention efficiency](attention-efficiency.md) trade-offs
  apply to vision tokens too. Hybrid attention is already used in a unified
  multimodal model (UniSpark, arXiv:2611.16517). `[speculation]`: in-fusion
  vision layers and cheap-attention layers may need to be placed together.
- **Smaller implicit encoders.** Distillation results suggest dedicated
  vision capacity could be much smaller than today's 0.4B encoders.
  `[speculation]`, the evidence is for audio.

## L2 Mechanism

Notation: `z` is a token's hidden vector, `m` is 1 for vision tokens and 0 for
text tokens, and `W` is a shared weight matrix. All variants share a
Qwen3-style decoder (arXiv:2611.17334, §2.1).

- **Pretrained or scratch encoder (pre-fusion).** A separate 27-layer, 0.4B
  ViT turns patches into vectors, and a linear map projects them into the
  backbone. Pretrained means the ViT was first trained on its own objective
  (for example MetaCLIP); scratch means it starts random and trains jointly.
- **Encoder-free.** Each 14×14 patch goes through one linear layer, then
  RMSNorm and a learned scalar gate, straight into the backbone.
- **In-fusion.** Inside layers 1–8 of the 28-layer backbone, vision tokens get
  extra, vision-only weights added to the shared ones. Text tokens pass
  through unchanged.
  - Attention projections Q, K, V and O: `P(z) = W z + m · ΔW z`.
  - Feed-forward: `h' = h + F(N(h)) + m · ΔF(N(h))`.
  - The extra parts start at zero.
- **Attention pattern.** Vision tokens attend to each other bidirectionally,
  and text attends causally to everything before it.
- **Lifetime compute.** `C_lifetime = Σ_s C_s` over all training stages,
  including encoder pretraining. A frozen encoder is charged its forward pass
  only.

## L3 Math

To fill on request (`/deepen vision-encoder L3`). Planned content:

- The fitted scaling laws in Brown–Hoang (§G, Table 30). For example,
  Avg. VQA ≈ `a + b ln N + c ln D` per recipe, where encoder-free has a lower
  intercept and a lower data coefficient than the scratch encoder. What
  "about 3x compute to match" means in these coordinates.
- Shukor et al.'s `L = E + A/N^α + B/D^β`, and why an averaged loss can hide a
  modality-specific gap.
- Chen et al.'s loss-compute exponents, and how sensitive the extrapolated
  crossover is to compute accounting.

## L4 Sources (reading order)

| # | Source | Why read it | Verified |
|---|---|---|---|
| 1 | Brown, Hoang, Qian, Li, Lewis, Ghazvininejad, Zettlemoyer, Beyer, Ren, Verbeek, Xie & Xu 2026, "Unbundling Multimodal Vision Encoding", arXiv:2611.17334 ([blog](https://unbundling.github.io)) | The controlled study this card is built on | yes |
| 2 | Chen et al. 2026, "How Far Are We from Removing the Visual Encoder? Scaling Laws for Encoder-Free Multimodal Pretraining", arXiv:2609.35457 | Encoder-free scaling and the extrapolated crossover | yes (metadata); numbers from alphaXiv summary |
| 3 | Shukor, Fini, Turrisi da Costa, Cord, Susskind & El-Nouby 2025, "Scaling Laws for Native Multimodal Models", arXiv:2504.07951 | The opposing loss-based result | yes (metadata); numbers from alphaXiv summary |
| 4 | Harwath et al. 2026, "Encoder-Free Multimodal LLMs Learn Implicit Encoders", arXiv:2610.24239 | What encoder-free models build internally | yes |
| 5 | Liang et al. 2024, "Mixture-of-Transformers", arXiv:2411.04996; Bao et al. 2021, "VLMo", arXiv:2111.02358 | Modality-specific parameters in a shared model | yes (metadata) |
| 6 | Diao et al. 2024, "Unveiling Encoder-Free Vision-Language Models" (EVE), arXiv:2406.11832; EVEv2, arXiv:2502.06788 | Earlier encoder-free recipes | yes (metadata) |
| 7 | Liu et al. 2023, "Visual Instruction Tuning" (LLaVA), arXiv:2304.08485; Radford et al. 2021, CLIP, arXiv:2103.00020 | The default encoder recipe | yes (metadata) |
| 8 | Raschka 2024, [Understanding Multimodal LLMs](https://magazine.sebastianraschka.com/p/understanding-multimodal-llms) | Explainer of the two main architecture families | yes (found by search; content not re-read) |
| 9 | Liew, Suzuki & Tokui 2026, "Scaling Laws for Vision-Language Fusion", arXiv:2611.22351 | When to add vision (fusion timing), always with a pretrained encoder | yes (full text) |

## Open questions

- [ ] Does the roughly 3x encoder-free penalty hold at native resolution, on
      text-rich data, and beyond 6.4B parameters, where all current controlled
      studies stop?
- [ ] Under one compute accounting, do Chen et al.'s extrapolated crossover and
      Brown–Hoang's constant gap still disagree?
- [ ] On downstream VQA rather than loss, does modality-aware vision capacity
      beat modality-agnostic MoE routing in a sparse backbone?
- [ ] How small can dedicated vision capacity be before VQA drops (distilled
      implicit encoders, narrower in-fusion branches)?
- [ ] Do encoders pretrained on much more or different data (SigLIP 2,
      DINOv3) beat a scratch encoder at matched lifetime compute, which
      Brown–Hoang did not test?

## Log

- 2026-11-18: created from arXiv:2611.17334 via `/investigate`. Main paper read
  in full. Four related scaling and analysis papers were read: two in full and
  two through alphaXiv summaries, which are flagged. Metadata for 18 sources
  checked with Semantic Scholar (Asta) and alphaXiv.
