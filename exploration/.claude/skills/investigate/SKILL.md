---
name: investigate
description: Create or update a concept card in the exploration vault for a research question or concept (AI, math, physics, biology). Use when the user asks to investigate, explain, understand or map an idea, paper or trend.
argument-hint: <question, concept, paper URL, or existing card slug>
---

# Investigate

Target: $ARGUMENTS

Follow the method and evidence rules in `CLAUDE.md`.

1. **Find or create the card.** Look in `cards/` for an existing card on this
   topic. If none exists, copy `templates/concept-card.md` to
   `cards/<slug>.md` and phrase the title as a question. If the target is a
   paper, the card is about the question the paper answers, not the paper
   itself.
2. **Gather sources.** Use the connected tools in the order given in
   `CLAUDE.md` (alphaXiv, then Semantic Scholar through Asta, Hugging Face,
   arXiv). Aim for: the origin paper of the idea, the strongest recent
   result, any known boundary (theorem or consistent empirical limit), and one
   good explainer (blog or survey). Ask before running an Undermind deep
   search.
3. **Verify existing citations.** For every source in the card marked
   `Verified: no` or `(unverified)`, confirm title, authors, year and arXiv id
   with a tool, and that the paper actually supports the claim it is cited
   for. Fix or remove anything that does not check out, and say what you
   changed.
4. **Write the card.** Fill L0, L1 (with "where the analogy breaks"), all
   seven questions, and L2. Label every boundary claim. Fill L3 and L4 only if
   the user asked or a boundary depends on them; otherwise leave the planned
   outline.
5. **Open questions.** Add questions a future paper or experiment could
   answer. These drive `/radar`.
6. **Links.** Link related cards. Create stub cards (`Status: stub`) for
   important linked concepts that do not exist yet.
7. **Update `INDEX.md`** (card row and open questions) and the card's `Log`.
8. **Report to the user** in a few sentences: the L0 headline, the single most
   important boundary or trade-off, what you verified or corrected, and which
   section is worth going deeper on.
9. **Commit and push** only files under `exploration/`, as described in
   `CLAUDE.md`.
