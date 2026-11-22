# Can a model reason in continuous vectors instead of words?

Status: draft
Last updated: 2026-11-22
Related: [multi-agent communication](multi-agent-communication.md) ·
[looped transformers](looped-transformers.md) ·
[associative memory](associative-memory.md) ·
[state space models](state-space-models.md) ·
[test-time training](test-time-training.md)

## L0 Headline

Latent reasoning replaces a written chain of thought with continuous vectors
that the model feeds back into itself. In theory a continuous "thought" can
hold several partial solutions at once, and this is proven for graph search.
In practice, pretrained models mostly do not use that room: their latent
chains collapse to one path, or only carry an answer they already computed
while reading the question. Today latent reasoning buys fewer tokens and some
sampling diversity, not better reasoning than text chains of thought at scale.

## L1 Intuition

Analogy:

- **Text chain of thought: walking a maze while saying each turn out loud.**
  At every junction you must name one corridor. If it is a dead end, you
  have to notice and walk back.
- **Latent chain of thought: shading a map instead of walking.** At each
  step you shade every square you could have reached so far. When the exit
  gets shaded, you are done, and you never had to choose a corridor. This is
  a breadth-first search.

Where the analogy breaks:

- **Pretrained models rarely shade the map.** Given a blend of options, they
  behave as if only the most likely one was there. They pick a corridor in
  the first layers of the network, like the person who says "I'm keeping my
  options open" and has already decided.
- **Often there is no walk at all.** In many fine-tuned models the answer is
  already readable from the question before the latent chain starts. The
  chain only carries it to the output.
- **The map has a fixed size.** One vector of dimension `d` can only hold
  about as many cleanly separable options as it has dimensions. This is the
  same limit as in [associative memory](associative-memory.md).
- **Nobody can read the shading.** A spoken walk can be checked; a shaded
  vector needs probes, and probes can mislead.

## The seven questions

### 1. Scarce resource

- **Sequential decoding steps.** A text chain of thought costs one full
  forward pass per token, plus a growing KV cache. Latency grows with chain
  length.
  - Coconut on ProsQA: 14.2 generated tokens against 49.4 for a text chain
    of thought, and 0.15 s against 0.47 s per problem on one A100 (GPT-2;
    Hao et al. 2024, arXiv:2412.06769).
  - CODI compresses GSM8k chains of thought 3.1x, which gives a 2.7x
    speedup, and 8.2x on verbose natural-language chains (Shen et al. 2025,
    arXiv:2502.21074).
- **Bandwidth between steps.** A sampled token passes at most `log2 |V|`
  bits to the next step (about 17 bits for a 128k vocabulary). A hidden
  state passes `d` floats. Latent reasoning removes this quantization.
  `[interpretation]`
- **Training signal.** Latent steps have no target text, so the model must
  learn what to put in them from the final answer alone. This turns out to be
  the binding constraint (see Boundary).
- **Human oversight.** A written chain can be read and monitored; a latent
  chain cannot without probes.

### 2. Trade-off

The exchange is tokens and latency against accuracy and readability.

- **Small synthetic logic tasks: better point, same frontier.** On ProsQA,
  Coconut reaches 97.0% with 14.2 tokens, against 77.5% for the text chain of
  thought with 49.4 tokens. But the same paper shows that the continuous
  thoughts are not what wins: `[empirical]`
  - iCoT, with no latent thoughts at all, gets 98.2% with 8.2 tokens.
  - Coconut with `<pause>` tokens in place of thoughts gets 96.6%.
  - The gain comes from the training curriculum that removes text steps
    gradually.
- **Math: below the text chain of thought, but cheaper.**
  - Coconut on GSM8k with GPT-2: 34.1% against 42.9% for text, but 8.2
    tokens against 25.0. `[empirical]`
  - CODI, trained by self-distillation, reaches 43.7% with GPT-2, about 99%
    of the text model, and 90% with LLaMA-3.2-1B. Self-reported.
    `[empirical]`
- **Reinforcement learning with soft tokens: parity at pass@1, more
  diversity.** `[empirical, self-reported]`
  - Training continuous chains with RL on Llama and Qwen up to 8B matches
    discrete training at pass@1 and beats it at pass@32 (Butt et al. 2025,
    arXiv:2509.19170).
  - The best setup trains with soft tokens and then decodes ordinary hard
    tokens. So the soft tokens act as a training regularizer, not as a
    reasoning medium at inference.
- **Training-free soft tokens at 32B: vanilla is worse, noisy is slightly
  better.** `[empirical, self-reported]`
  - On three 32B reasoning models and eight benchmarks, vanilla Soft Thinking
    averages below ordinary token sampling: 72.1 against 78.5 on
    R1-Distill-Qwen-32B (Wu et al. 2025, arXiv:2508.03440).
  - Adding Gumbel-softmax noise to the soft token lifts it 0.4–1.1 points
    above token sampling.
- **Pretraining is the one place where hidden-state feedback wins at matched
  compute** (latent feedback, arXiv:2611.20404; see the radar evidence
  below). That result is about loss, not reasoning tasks.
- **Small purpose-built reasoners: a cost frontier on ARC.** Pathway's
  BDH-CQ is a 150M model that reasons with no written chain. It reaches
  29.5% pass@2 on ARC-AGI-1 at about $0.0007 per task. That is a new point
  on the cost-versus-accuracy plane, not higher accuracy. See the BDH-CQ
  section below. `[empirical, self-reported, independently reproduced
  score]`

Verdict: latent reasoning moves the token-efficiency frontier on small tasks,
and in BDH-CQ the cost frontier on ARC. It does not yet move the accuracy
frontier for pretrained language models at scale.

### 3. Boundary

- **Serial steps are the resource; text chains of thought already add power.**
  `[proven, if TC0 ≠ NC1, NL ≠ L, P ≠ L]` (Merrill & Sabharwal 2023,
  arXiv:2310.07923, ICLR 2024). For log-precision decoder transformers:
  - With no intermediate steps they sit inside TC0, so they cannot simulate
    all finite automata or decide graph connectivity.
  - With `O(log n)` intermediate steps they stay inside L.
  - With a linear number of steps they recognize all regular languages.
  - With polynomially many steps they recognize exactly P.

  The lower bounds assume saturated attention, strict causal masking and a
  slightly generalized pre-norm. Any latent scheme still needs serial steps
  to gain this power; it changes what each step carries, not the need for
  steps.
- **Continuous thoughts can search in parallel.** `[proven]` A two-layer
  transformer with `D` continuous-thought steps decides directed graph
  reachability, where `D` is the graph's diameter (Zhu et al. 2025,
  arXiv:2505.12514, NeurIPS).
  - Each thought is the normalized sum of the embeddings of all vertices
    reached so far: a breadth-first frontier held in one vector.
  - The construction needs embedding dimension `O(|vocabulary|)` and works
    with sinusoidal positions or RoPE.
  - The best known discrete result for constant-depth transformers needs
    `O(n²)` steps. That is an upper bound only: no lower bound for discrete
    chains of thought is proven, so a strict separation is open.
    `[speculation]`
- **Pretrained models do not use the superposition.** `[empirical]`
  (Rizvi-Martel, Rabusseau & Mosbach 2026, arXiv:2604.06374, COLM 2026)
  - Training-free Soft Thinking on QwQ-32B: the hidden states for a soft
    token and for its top-1 token have cosine similarity 0.996. The blend is
    treated as its most likely token within a few layers.
  - Fine-tuned Coconut on ProsQA (GPT-2, SmolLM2 135M–1.7B): removing the
    latent thoughts costs at most 1.0 point. The model reads the answer off
    the question and copies it through the chain.
  - Only models trained from scratch use their latents: a 2-layer model
    scores 94.5% with them and 13.8% without.
  - Width, not depth, decides it. For graphs about 28 nodes wide, 2-layer
    models need `d` of about 256–384 before the latents matter (64.9% with
    against 62.3% without at `d = 64`; 96.7% against 32.0% at `d = 768`).
- **LLMs are single-threaded readers of soft tokens.** `[empirical]` Vanilla
  Soft Thinking behaves like greedy decoding, because the top-1 component
  dominates the next step (Wu et al. 2025, arXiv:2508.03440).
- **Readable latent states are not evidence of use.** `[empirical]` Qiu et
  al. 2026 (arXiv:2610.21182) ran 21 model-task configurations on GPT-2 and
  Llama-3.2-1B-Instruct.
  - On logic tasks, Coconut's answer is readable before the chain starts,
    and deleting the chain changes at most 3 of 300 answers.
  - Per-step supervision (SIM-CoT) makes the model depend on the chain.
  - On GSM8k arithmetic, every training recipe depends on the chain's
    content.
- **Latent planning has a depth ceiling.** `[empirical]` Xu, Jettkant & Ruis
  2026 (arXiv:2604.06427) test planning inside one forward pass, with no
  chain at all, on star-graph path-finding with supervision on the answer
  only:
  - A small transformer trained from scratch discovers strategies up to 3
    steps deep.
  - Fine-tuned GPT-4o and Qwen3-32B reach 5; GPT-5.4 few-shot reaches 7.
  - With a written backtracking chain of thought, 20 steps are learned in
    about 20 updates.

  The bottleneck is discovering a latent strategy from sparse supervision,
  not executing one.

### 4. Lineage

- **Recurrent networks.** A chain of thought is recurrence through a
  discrete bottleneck: each sampled token is the recurrent state (Merrill &
  Sabharwal make this point). Latent reasoning removes the quantization, so
  the state becomes a full RNN hidden state again.
  - What transfers: the training difficulties of RNNs. Backpropagation must
    run through every step, which is why Coconut stays at about 6 thoughts.
- **Breadth-first versus depth-first search.** Zhu et al. formalize the
  maze picture: a superposed frontier performs a BFS, while discrete
  sampling forces a DFS with backtracking.
- **Quantum superposition and measurement.** Zhu et al. borrow the terms:
  the thought is a superposition, and the answer token "measures" it.
  `[interpretation]` Where it breaks: there is no interference, and
  "measurement" is just a dot product.
- **Associative memory.** A thought that sums the embeddings of reached
  vertices is a superposition memory, so it inherits the dimension limit on
  cleanly separable items (see [associative memory](associative-memory.md)).
  The width bottleneck that Rizvi-Martel et al. measure fits this picture.
  `[interpretation]`
- **Depth recurrence.** Universal and looped transformers rerun layers within
  one token instead of feeding states across tokens (see
  [looped transformers](looped-transformers.md)).
- **Fast weights and Hebbian memory.** BDH-CQ writes demonstrations into a
  recurrent memory that the authors relate to fast weights and linear
  attention. In the underlying BDH architecture this memory is a Hebbian
  synaptic state. Here in-context learning is a memory write, the same
  operation as in [associative memory](associative-memory.md).
- **Cognitive science.** Coconut cites findings that the human language
  network stays largely inactive during many reasoning tasks.
  `[interpretation]`: a motivation, not evidence about transformers.

### 5. Measurement

- **Matched decode steps, not only matched tokens.** Compare a latent chain
  of `k` thoughts with a text chain of `k` tokens, a pause-token chain of
  `k` positions, and a self-consistency vote, all at the same forward
  passes. Coconut's own ablations show why the pause-token control matters.
- **Deletion and replacement tests** (Qiu et al.):
  - delete the chain;
  - replace its contents with noise, the dataset mean, or another problem's
    thoughts.

  If answers do not change, the chain is not doing the reasoning, however
  readable it looks.
- **An early-readout probe.** Is the answer decodable from the question's
  last hidden state, before any thought is written? If yes, the chain is a
  carrier.
- **A collapse probe.** Compare the hidden states for a soft token and for
  its top-1 token (cosine similarity, KL divergence).
- **Pass@k, not only pass@1.** It shows whether latent training preserves
  diversity.
- **A dose-response test.** Train with variable latent depth, then vary it at
  inference. If accuracy rises with more steps, the steps are doing work.
  BDH-CQ reports 21%, then 27%, then 29.5% at low, medium and high effort.
  This is weaker than a deletion test, but it is causal evidence of use.
- **What would support the strong claim:** a pretrained model of at least
  1B parameters where a latent chain beats a text chain at matched decode
  steps on a search-heavy task, and where deleting the chain hurts. None of
  the sources read here shows this.

### 6. Adoption

- **Open code and models:**
  - Coconut code from Meta (github.com/facebookresearch/coconut);
  - CODI code (github.com/zhenyi4/codi);
  - the Huginn-0125 recurrent-depth model: 3.5B parameters and 800B tokens
    (Geiping et al. 2025, arXiv:2502.05171);
  - an SGLang implementation of Soft Thinking.
- **Research volume is high in 2026.** An alphaXiv recency search returns
  many new methods (abstracts only, not read):
  - Soft Teacher Forcing from Google DeepMind (arXiv:2610.17189);
  - INTACT (arXiv:2610.19568);
  - latent reasoning with flow matching (arXiv:2610.06666);
  - several critiques.
- **No shipped production language model** in the sources read uses latent
  chains as its main reasoning mode. Frontier reasoning models still write
  text chains of thought. `[interpretation]`, based on these sources only.
- **A commercial latent reasoner outside language.** Pathway runs BDH-CQ as
  an ARC reasoning service, and an independent black-box audit reproduced
  its score. The exact architecture is proprietary.
- **Safety pushback.** Korbak et al. 2025 (arXiv:2507.11473) argue that
  readable chains of thought are a "new and fragile opportunity" for
  oversight. Xu et al. frame latent-reasoning limits as what keeps that
  opportunity alive.

### 7. Combination

- **Latent feedback in pretraining plus latent chains in reasoning.**
  `[speculation]` Rizvi-Martel et al. trace superposition collapse to
  next-token pretraining, and only from-scratch latent training escaped it.
  Pretraining with hidden-state feedback (arXiv:2611.20404) might produce
  models whose latents are not pre-collapsed.
- **Soft tokens as an RL exploration tool.** Butt et al.'s best setup trains
  soft and decodes hard, and Wu et al. need noise for soft tokens to help.
  Both point to soft tokens being useful mainly for exploration.
  `[interpretation]`
- **Per-step supervision.** SIM-CoT-style supervision of each slot is the
  one recipe in Qiu et al. that reliably makes models depend on the chain.
- **Adaptive halting.** The fixed-horizon result below suggests latent
  chains need a learned stopping rule, as looped models do.
- **Latent multi-agent communication.** Stream of Belief passes soft tokens
  between agents and sees them drift toward real word embeddings. That fits
  the collapse findings (see
  [multi-agent communication](multi-agent-communication.md)).
  `[interpretation]`

## L2 Mechanism

Four families feed something other than a sampled token into the next step.

1. **Hidden-state feedback** (Coconut, CODI). Between `<bot>` and `<eot>`,
   the last hidden state replaces the next input embedding:
   `E_t = [e(x_1) … e(x_i), h_i, h_{i+1} … h_{t-1}]`.
   - Coconut trains with a curriculum. Stage `k` replaces the first `k` text
     steps with `k·c` thoughts, with a loss only on the remaining text.
     Without the curriculum it does no better than no chain at all (14.4% on
     GSM8k).
   - CODI trains a teacher (text chain) and a student (latent chain) in one
     model. It aligns their hidden states at the token just before the
     answer with an L1 loss, in one stage and with no curriculum.
2. **Soft tokens** (Soft Thinking, training-free). The next input is the
   probability-weighted mix of embeddings, `ẽ = Σ_k p_k e_k`, usually over
   the top-k tokens.
   - Stochastic variants add Gumbel or Dirichlet noise.
   - The RL variant adds Gaussian noise to the mixed embedding, so that
     REINFORCE can explore.
3. **Pause and filler tokens.** Extra positions with no content give extra
   computation but carry no state between steps (Goyal et al. 2023,
   arXiv:2310.02226; Pfau et al. 2024, arXiv:2404.15758).
4. **Recurrence in depth or across tokens.**
   - Huginn loops a 4-layer block `r` times per token. At `r = 32`, GSM8k
     with a chain of thought rises from 0% (`r = 1`) to 34.8% strict match.
     Its non-recurrent twin is not matched on FLOPs.
   - Latent feedback passes each token's top-layer state into the next
     token's input during pretraining.

**Why superposition can work** (Zhu et al.'s construction): if vertex
embeddings are orthonormal, the thought
`t_c = (1/√|V_c|) Σ_{v ∈ V_c} u_v` encodes the set `V_c` of vertices reached
within `c` steps.
- One attention layer reads the edges whose source is in the set.
- One MLP thresholds away the noise.
- Normalization rescales.

This is exactly one BFS expansion per thought. It needs as many orthogonal
directions as there are vertices, which is the width cost.

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
- **Looped models** are now on their own card:
  [looped transformers](looped-transformers.md).

## BDH-CQ: in-context learning plus recurrent latent reasoning (Pathway, 2026)

Source: Engdahl, Kosowski, Chorowski, Stamirowska, Uznański, Jiang, Phadke,
Kinas & Zhong 2026, "BDH-CQ: In-Context Learning with Recurrent Latent
Reasoning", arXiv:2608.09888 (Pathway, Bielik AI, NYU). Read in full with
alphaXiv. It builds on Pathway's Dragon Hatchling (BDH) architecture
(Kosowski et al. 2025, arXiv:2509.26507, metadata verified).

**What is new: two separate states, one for learning and one for thinking.**

1. **Memory `S` learns the task from the context.** Each demonstration is
   written into a recurrent memory, `S_t = U(S_{t-1}, D_t)`, with fixed
   weights. There is no KV cache, and nothing is learned by gradient at test
   time.
2. **Workspace `H` does the reasoning.** After reading the demonstrations,
   the model encodes the query, `H_0 = E(x*, S_K)`. It then iterates
   `H_{r+1} = F(H_r, S_K)` for `R` steps and decodes only the answer,
   `ŷ = G(H_R)`. No intermediate step is written out as tokens.

Compared with the methods above:

- **Coconut and CODI** feed one hidden state back as the next token, inside a
  language model fine-tuned from a text chain. BDH-CQ iterates a separate,
  structured multi-vector workspace, which is recurrence in depth. It is
  trained from scratch for this purpose.
- **HRM and TRM** (recursive latent solvers for ARC) learn each evaluation
  task by optimization, with per-puzzle identity embeddings. BDH-CQ learns an
  unseen task from its demonstrations alone, in one forward computation.
  The paper cites ARC Prize costs of $1.48 per task for HRM and $1.76 for
  TRM.

**Results** `[empirical, self-reported]`:

- **ARC-AGI-1 public evaluation (400 tasks).** 29.5% pass@2 with 150M
  parameters, at about 0.85 H200 GPU-seconds, or $0.0007, per task.
  - No system on the ARC Prize leaderboard of August 2026 reaches this
    accuracy at this cost or less.
  - For comparison, GPT 5.6 Luna (Low) scores 34.2% at $0.040 per task, by
    the leaderboard's numbers.
  - An independent black-box audit by the Bielik AI and NYU co-authors
    reproduced the 29.5%.
- **Reasoning effort scales accuracy.** Low, medium and high latent effort
  give 21%, 27% and 29.5%. The paper reports the low setting as 22% cheaper
  than high.
- **The task is held in memory, not memorized.**
  - Fresh color permutations given only in the demonstrations are applied
    correctly on 96 of 96 held-out outputs.
  - Propagation and copying extrapolate across all tested lengths.
  - Ordering fails beyond 6 objects, and nesting fails at depth 5.
  - Adding one demonstration at the target depth fixes nesting (from 19/24
    to 24/24).
- **ConceptARC:** 95 of 160 tasks at pass@2, ranging from 9/10 (filled or
  not filled) to 2/10 (copy, order).

**Caveats:**

- **The update rules, dimensions and training recipe are proprietary**, so
  the results cannot be reproduced from the paper. The evaluated system also
  includes input transformations and candidate ranking, not only the model.
- **The headline is cost, not accuracy.** 29.5% is far below the best ARC-AGI-1
  systems. No comparison is made with a text chain of thought, or with a
  same-size model without latent steps, at matched compute.
- **It covers visual grids only.** Language and math are stated as future
  work. The paper's claim of Transformer-like scaling from 1B to 600B
  parameters is a one-line mention of early experiments, with no data.

**How it fits this card.** `[interpretation]` BDH-CQ is trained from scratch
for latent reasoning. That is the regime where Rizvi-Martel et al. found
latents are actually used, and the effort-scaling result agrees. So it
supports the reading that latent reasoning works when a model is built for
it, and fails mainly when it is retrofitted onto a pretrained language model.
Whether BDH-CQ's design carries over to language is open.

## L3 Math

Planned outline (fill with `/deepen latent-reasoning L3`):

- Merrill & Sabharwal's bounds:
  - why no-chain transformers sit in TC0;
  - why `t(n)` steps give `TIME(t(n)) ⊆ CoT(t(n)) ⊆ SPACE(t(n) + log n)`.
- Zhu et al.'s two-layer construction: the attention chooser, BFS
  expansion, MLP thresholding, and the final "measurement" readout.
- Why the discrete bound is `O(n²)` (DFS on a non-random-access Turing
  machine), and what a lower bound would need.
- How many superposed items fit in dimension `d` (the Johnson–Lindenstrauss
  view), linked to the width results.

## L4 Sources (reading order)

| # | Source | Why read it | Verified |
|---|---|---|---|
| 1 | Hao, Sukhbaatar, Su, Li, Hu, Weston & Tian 2024, "Training Large Language Models to Reason in a Continuous Latent Space" (Coconut), arXiv:2412.06769 | The origin of hidden-state feedback, with the ProsQA BFS story and the ablations that undercut it. | yes (full text) |
| 2 | Zhu, Hao, Hu, Jiao, Russell & Tian 2025, "Reasoning by Superposition", arXiv:2505.12514 (NeurIPS 2025) | The `[proven]` parallel-search construction for graph reachability. | yes (full text) |
| 3 | Merrill & Sabharwal 2023, "The Expressive Power of Transformers with Chain of Thought", arXiv:2310.07923 (ICLR 2024) | Why serial steps are the resource: TC0, L, regular languages, P. | yes (full text) |
| 4 | Rizvi-Martel, Rabusseau & Mosbach 2026, "The Illusion of Superposition?", arXiv:2604.06374 (COLM 2026) | The main negative result: collapse in pretrained and fine-tuned models, and the width bottleneck. | yes (full text) |
| 5 | Qiu et al. 2026, "Does Latent Chain-of-Thought Actually Reason?", arXiv:2610.21182 | Deletion and replacement tests, plus a taxonomy that reconciles the earlier reports. | yes (full text) |
| 6 | Wu et al. 2025, "LLMs are Single-threaded Reasoners", arXiv:2508.03440 | Soft Thinking behaves greedily at 32B; noise helps. | yes (full text) |
| 7 | Shen, Yan, Zhang, Hu, Du & He 2025, "CODI", arXiv:2502.21074 (EMNLP 2025) | The strongest distillation result: about 99% of the text chain at GPT-2 scale. | yes (full text) |
| 8 | Butt, Kwiatkowski, Labiad, Kempe & Ollivier 2025, "Soft Tokens, Hard Truths", arXiv:2509.19170 | Scalable RL for continuous chains; train soft, decode hard. | yes (full text) |
| 9 | Xu, Jettkant & Ruis 2026, "The Depth Ceiling", arXiv:2604.06427 | Limits of latent planning, and what they mean for monitoring chains of thought. | yes (full text) |
| 10 | Geiping et al. 2025, "Scaling up Test-Time Compute with Latent Reasoning: A Recurrent Depth Approach", arXiv:2502.05171 (NeurIPS 2025) | Recurrence in depth at 3.5B scale. | yes (full text) |
| 11 | Huang, Dwivedi, Ma, Moreno & Liu 2026, latent feedback, arXiv:2611.20404 | Hidden-state feedback in pretraining at matched compute. | yes (spot-checked) |
| 12 | Zhang et al. 2025, "Soft Thinking", arXiv:2505.15778 (NeurIPS 2025) | The training-free soft-token method that papers 4 and 6 critique. | yes (metadata) |
| 13 | Deng, Choi & Shieber 2024, "From Explicit CoT to Implicit CoT: Learning to Internalize CoT Step by Step", arXiv:2405.14838 | iCoT, the curriculum that Coconut builds on and that matches it on ProsQA. | yes (metadata) |
| 14 | Goyal et al. 2023, "Think before you speak: Training Language Models With Pause Tokens", arXiv:2310.02226 (ICLR 2024) | The pause-token control. | yes (metadata) |
| 15 | Pfau, Merrill & Bowman 2024, "Let's Think Dot by Dot", arXiv:2404.15758 | Filler tokens and hidden computation. | yes (metadata) |
| 16 | Korbak et al. 2025, "Chain of Thought Monitorability: A New and Fragile Opportunity for AI Safety", arXiv:2507.11473 | Why readable chains matter for oversight. | yes (metadata) |
| 17 | Zhu et al. 2025, "A Survey on Latent Reasoning", arXiv:2507.06203 | A broad map of the field; good for orientation. | yes (metadata) |
| 18 | Chen et al. 2026, "Rethinking Fixed-Horizon Latent Reasoning", arXiv:2611.24001 | Overlong latent chains hurt; stop adaptively. | abstract only |
| 19 | Engdahl, Kosowski, Chorowski et al. 2026, "BDH-CQ: In-Context Learning with Recurrent Latent Reasoning", arXiv:2608.09888 | Separate memory and workspace; the ARC cost frontier; dose-response from latent effort. | yes (full text) |
| 20 | Kosowski, Uznański, Chorowski, Stamirowska & Bartoszkiewicz 2025, "The Dragon Hatchling", arXiv:2509.26507 | The BDH architecture: sparse positive activations and Hebbian synaptic state. | yes (abstract and metadata) |

## Open questions

- [ ] On a search-heavy task, does a latent chain in a pretrained model of at
      least 1B parameters beat a text chain at matched decode steps, and does
      deleting it hurt? (2026: no source shows both. Coconut's gains on
      ProsQA match iCoT and pause-token controls.)
- [ ] Does hidden-state feedback that helps pretraining (arXiv:2611.20404)
      also give Coconut-style reasoning gains without a separate latent
      training stage, and does it avoid superposition collapse?
- [ ] Is there a lower bound that strictly separates discrete from continuous
      chains of thought on graph reachability (more than `D` discrete steps
      needed)?
- [ ] Does superposition capacity scale with width like associative-memory
      capacity, about `d` separable items per thought?
- [ ] Does giving a model latent slots raise the latent planning depth
      ceiling (3 to 7 steps) seen within one forward pass?
- [ ] Can probes read latent chains well enough to keep chain-of-thought
      monitoring viable if latent reasoning is adopted?
- [ ] Does BDH-CQ-style in-context latent reasoning (separate memory and
      workspace, trained from scratch) carry over to language or math tasks?
      At matched compute, does it beat a same-size model that writes its
      reasoning out?

## Log

- 2026-11-19: stub created from the multi-agent-communication card.
- 2026-11-20: added latent feedback, the fixed-horizon result and looped
  models from the [2026-W47 radar update](../radar/2026-W47.md).
  - Spot-checked the latent-feedback numbers against the paper with alphaXiv.
  - The other three papers are from abstracts only.
- 2026-11-20: `/investigate`: filled L1, the seven questions, L2 and L4 (18
  sources), plus an L3 outline and four new open questions. Status changed
  from stub to draft.
  - Read the full text of Coconut, Reasoning by Superposition, Merrill &
    Sabharwal, Illusion of Superposition, Does Latent CoT Actually Reason,
    Single-threaded Reasoners, CODI, Soft Tokens Hard Truths, Depth Ceiling
    and Huginn with alphaXiv.
  - Checked metadata for the other sources with Semantic Scholar.
  - Moved the looped-model papers to a new
    [looped transformers](looped-transformers.md) stub.
  - Corrected the seed note that Coconut "beats chain of thought on
    planning-heavy logic tasks". It does on ProsQA, but iCoT and pause-token
    controls match it, so the continuous thoughts are not what wins.
- 2026-11-22: added Pathway's BDH-CQ (arXiv:2608.09888, read in full).
  - New section, plus notes in Trade-off, Lineage, Measurement and Adoption.
  - L4 sources 19–20 and one open question.
