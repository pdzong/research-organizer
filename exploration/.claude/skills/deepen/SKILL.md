---
name: deepen
description: Take one concept card in the exploration vault one depth level further (intuition, mechanism, math, proofs), or explain one section of it more deeply. Use when the user wants to go deeper on a card or does not understand part of it.
argument-hint: <card slug> [L1|L2|L3|L4|section name]
---

# Deepen

Target: $ARGUMENTS

1. Read the card in `cards/`. If no level or section is given, pick the first
   level that is missing or marked as planned.
2. Work out what the reader needs first. List the prerequisite concepts for
   this level in one line each. If a prerequisite is substantial, link or
   create a stub card for it instead of explaining it inline.
3. Write the level:
   - **L1**: a sharper analogy, a second analogy from a different field if it
     helps, and where each one breaks.
   - **L2**: the mechanism with minimal notation; define every symbol once.
   - **L3**: the equations and the argument behind each boundary claim. For
     a theorem, state it precisely, give the proof idea in plain language,
     then the key step in symbols. Say which assumptions it relies on.
   - **L4**: a reading order with what to look for in each source and which
     sections can be skipped.
4. Use a small worked example (numbers, a tiny matrix, a toy sequence)
   whenever it makes an idea concrete.
5. Verify any new citation with a tool, following `CLAUDE.md`.
6. Ask the user one or two check-your-understanding questions at the end, and
   offer the next level.
7. Update the card's `Log` and `Last updated`, then commit and push files
   under `exploration/`.
