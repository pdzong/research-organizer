"""Objective inputs for /curate: size against budget, grounding signals, duplicates.

Usage (from the exploration folder):
  py curation/measure.py               all cards, summary table
  py curation/measure.py <slug> ...    detailed report for these cards
  py curation/measure.py --json        everything as JSON

It reads the cards with the viewer's parser and never edits anything.
The budgets below are the ones in curation-policy.md; change both together.
Standard library only.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VAULT / "viewer"))
from build import parse_card, cited_ids  # noqa: E402

BUDGET = {
    "l0_words": 60,
    "core_min": 3,
    "core_max": 6,
    "l1_words": 300,
    "question_words": 350,
    "question_bullets": 8,
    "l2_words": 900,
    "reading_words": 3000,  # everything a reader sees at depth L2
    "open_questions": 8,
}

WEAK = {
    "unverified": re.compile(r"\(unverified\)", re.I),
    "abstract_only": re.compile(r"abstract only|from (?:the )?abstract", re.I),
    "not_read": re.compile(r"not read|title (?:only|from)", re.I),
    "self_reported": re.compile(r"self-reported", re.I),
    "speculation": re.compile(r"\[speculation\]"),
}
LABEL = re.compile(r"\[(proven|empirical|interpretation|speculation)[^\]]*\]")


def words(md: str) -> int:
    return len(re.findall(r"\w+", md))


def bullets(md: str) -> list[str]:
    """Top-level list items with their continuation lines."""
    items: list[list[str]] = []
    for line in md.splitlines():
        if re.match(r"^[-*] ", line):
            items.append([line[2:]])
        elif items and (line.startswith(" ") and line.strip()):
            items[-1].append(line.strip())
    return [" ".join(i) for i in items]


def shingles(text: str, k: int = 4) -> set[tuple[str, ...]]:
    w = re.findall(r"[a-z0-9]+", text.lower())
    return {tuple(w[i:i + k]) for i in range(max(0, len(w) - k + 1))}


def near_duplicates(units: list[tuple[str, str]], threshold: float = 0.45) -> list[dict]:
    """Pairs of units (where, text) that share many 4-word shingles."""
    sh = [(where, text, shingles(text)) for where, text in units if words(text) >= 12]
    out = []
    for i in range(len(sh)):
        for j in range(i + 1, len(sh)):
            a, b = sh[i][2], sh[j][2]
            if not a or not b:
                continue
            score = len(a & b) / min(len(a), len(b))
            if score >= threshold:
                out.append({"a": sh[i][0], "b": sh[j][0], "overlap": round(score, 2),
                            "text_a": sh[i][1][:140], "text_b": sh[j][1][:140]})
    return out


def measure(card: dict) -> dict:
    sec = {s["kind"]: s for s in card["sections"]}
    extras = [s for s in card["sections"] if s["kind"] == "extra"]
    l0 = words(sec["l0"]["md"]) if "l0" in sec else 0
    l1 = words(sec["l1"]["md"]) if "l1" in sec else 0
    l2 = words(sec["l2"]["md"]) if "l2" in sec else 0
    qs = {n: {"words": words(md), "bullets": len(bullets(md))} for n, md in card["questions"].items()}
    extra_words = sum(words(s["md"]) for s in extras)
    reading = l0 + l1 + l2 + extra_words + sum(q["words"] for q in qs.values())

    over = []
    if l0 > BUDGET["l0_words"]:
        over.append(f"L0 {l0}/{BUDGET['l0_words']} words")
    if card["core"] and not BUDGET["core_min"] <= len(card["core"]) <= BUDGET["core_max"]:
        over.append(f"{len(card['core'])} core ideas (want {BUDGET['core_min']}-{BUDGET['core_max']})")
    if l1 > BUDGET["l1_words"]:
        over.append(f"L1 {l1}/{BUDGET['l1_words']} words")
    for n, q in qs.items():
        if q["words"] > BUDGET["question_words"] or q["bullets"] > BUDGET["question_bullets"]:
            over.append(f"Q{n} {q['words']} words, {q['bullets']} bullets")
    if l2 > BUDGET["l2_words"]:
        over.append(f"L2 {l2}/{BUDGET['l2_words']} words")
    for s in extras:
        over.append(f"extra section at reading depth: '{s['heading']}' ({words(s['md'])} words)")
    if reading > BUDGET["reading_words"]:
        over.append(f"reading depth {reading}/{BUDGET['reading_words']} words")
    n_open = sum(1 for o in card["open"] if not o["done"])
    if n_open > BUDGET["open_questions"]:
        over.append(f"{n_open}/{BUDGET['open_questions']} open questions")

    # Grounding: every unit at reading depth, scanned for weak-evidence markers.
    units: list[tuple[str, str]] = []
    for s in card["sections"]:
        if s["kind"] in ("l0", "l1", "l2", "extra"):
            units += [(f"{s['heading']}", b) for b in bullets(s["md"]) or [s["md"]]]
    for n, md in card["questions"].items():
        units += [(f"Q{n}", b) for b in bullets(md) or [md]]
    weak = []
    for where, text in units:
        hits = [k for k, rx in WEAK.items() if rx.search(text)]
        if hits:
            weak.append({"where": where, "signals": hits, "text": text[:160]})
    unlabeled_boundary = [b[:160] for b in bullets(card["questions"].get("3", "")) if not LABEL.search(b)]
    sources = card.get("sources", [])
    unverified_rows = [r["id"] for r in sources if not re.match(r"yes", r["verified"], re.I)]
    in_table = {r["id"] for r in sources}
    cited_not_listed = [i for i in card["cites"] if i not in in_table] if sources else []

    return {
        "slug": card["slug"],
        "status": card["status"],
        "words": card["words"],
        "reading_words": reading,
        "l0": l0, "l1": l1, "l2": l2, "questions": qs,
        "extras": [{"heading": s["heading"], "words": words(s["md"])} for s in extras],
        "core_ideas": len(card["core"]),
        "open": n_open,
        "shelf": len(card["shelf"]),
        "over_budget": over,
        "weak": weak,
        "unlabeled_boundary": unlabeled_boundary,
        "l4_not_verified": unverified_rows,
        "cited_not_in_l4": cited_not_listed,
        "duplicates": near_duplicates(units),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    cards = [parse_card(p) for p in sorted((VAULT / "cards").glob("*.md"))]
    report = [measure(c) for c in cards if not args or c["slug"] in args]

    # Papers cited by more than one card: candidates for "lives in one card, linked from others".
    shared: dict[str, list[str]] = {}
    for c in cards:
        for pid in c["cites"]:
            shared.setdefault(pid, []).append(c["slug"])
    shared = {k: v for k, v in shared.items() if len(v) > 1}

    if "--json" in sys.argv:
        print(json.dumps({"budget": BUDGET, "cards": report, "shared_papers": shared}, indent=1))
        return
    if not args:
        print(f"{'card':28} {'status':6} {'read':>5} {'over':>4} {'weak':>4} {'dup':>3} {'shelf':>5}")
        for r in report:
            print(f"{r['slug']:28} {r['status']:6} {r['reading_words']:>5} {len(r['over_budget']):>4} "
                  f"{len(r['weak']):>4} {len(r['duplicates']):>3} {r['shelf']:>5}")
        print(f"\n{len(shared)} papers are cited by more than one card.")
        return
    for r in report:
        print(f"# {r['slug']} ({r['status']}): {r['reading_words']} words at reading depth, {r['words']} in total")
        print(f"core ideas: {r['core_ideas'] or 'none yet'} · open questions: {r['open']} · shelf: {r['shelf']}")
        print("\n## Over budget"); print("\n".join(f"- {x}" for x in r["over_budget"]) or "- none")
        print("\n## Weak grounding at reading depth")
        print("\n".join(f"- {w['where']} [{', '.join(w['signals'])}]: {w['text']}" for w in r["weak"]) or "- none")
        print("\n## Boundary bullets (Q3) without an evidence label")
        print("\n".join(f"- {b}" for b in r["unlabeled_boundary"]) or "- none")
        print("\n## L4 rows not verified:", ", ".join(r["l4_not_verified"]) or "none")
        print("## Cited but missing from L4:", ", ".join(r["cited_not_in_l4"]) or "none")
        print("\n## Near-duplicates")
        print("\n".join(f"- {d['a']} ~ {d['b']} ({d['overlap']}): {d['text_a']} | {d['text_b']}"
                        for d in r["duplicates"]) or "- none")
        here = {k: v for k, v in shared.items() if r["slug"] in v}
        print(f"\n## Papers shared with other cards: {len(here)}")
        print()


if __name__ == "__main__":
    main()
