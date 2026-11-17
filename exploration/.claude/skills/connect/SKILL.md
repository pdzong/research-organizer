---
name: connect
description: Look for real, evidence-backed connections between two concepts or cards in the exploration vault (shared mechanisms, shared boundaries, transferable results, combination ideas). Use when the user asks how two ideas relate or could work together.
argument-hint: <card or concept A> <card or concept B>
---

# Connect

Targets: $ARGUMENTS

1. Read both cards (or run a quick `/investigate` for a concept without a card
   and create a stub).
2. Look for connections at four strengths, strongest first:
   - **Formal equivalence**: one is provably a special case or a dual of the
     other. Needs a source.
   - **Shared boundary**: both are limited by the same theorem or resource.
   - **Transferable result**: a technique or theorem from one has been, or
     plausibly could be, applied to the other.
   - **Analogy only**: useful for intuition, not evidence. Say where it breaks.
3. Search for papers that already make the connection (alphaXiv
   `discover_papers` with both concepts in the question; Asta for papers
   citing both origin papers). If a connection is already published, cite it
   and do not present it as new.
4. Propose at most three combination ideas, each labeled `[speculation]`, with:
   what would be built or tested, what result would show it works, the
   cheapest experiment that could test it, and the closest existing work.
5. Write a `## Connections` section in both cards linking to each other, and
   add any new open questions to the cards and `INDEX.md`.
6. Report to the user in a few sentences, then commit and push files under
   `exploration/`.
