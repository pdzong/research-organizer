"""Build the vault reader from the Markdown cards.

The cards stay the single source of truth. This script only parses their
fixed structure (header fields, depth levels, the seven questions, open
questions, log) into JSON, and writes:

  viewer/site/vault-data.js   window.VAULT = {...}
  viewer/site/index.html      the page, for publishing as an artifact
  viewer/site/vault.html      the same page with a full HTML skeleton, for
                              opening locally in a browser

Usage (from the exploration folder):  py viewer/build.py
Standard library only.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
VIEWER = VAULT / "viewer"
SITE = VIEWER / "site"

CARD_LINK = re.compile(r"\]\((?:\.\./cards/|\./)?([a-z0-9-]+)\.md\)")
FENCE = re.compile(r"^\s*(```|~~~)")
QUESTION_H3 = re.compile(r"^###\s+(\d)\.\s+(.+?)\s*$")
OQ_ITEM = re.compile(r"^- \[( |x|X)\]\s?(.*)$")
LOG_ITEM = re.compile(r"^- (\d{4}-\d{2}-\d{2}):\s?(.*)$")
VIZ_FENCE = re.compile(r"^\s*```(mermaid|frontier|boundary|embed)\b", re.M)

H2_KIND = [
    (re.compile(r"^L0\b"), "l0"),
    (re.compile(r"^L1\b"), "l1"),
    (re.compile(r"^The seven questions", re.I), "seven"),
    (re.compile(r"^L2\b"), "l2"),
    (re.compile(r"^L3\b"), "l3"),
    (re.compile(r"^L4\b"), "l4"),
    (re.compile(r"^Open questions", re.I), "open"),
    (re.compile(r"^Log\b", re.I), "log"),
]


def h2_kind(heading: str) -> str:
    for pattern, kind in H2_KIND:
        if pattern.search(heading):
            return kind
    return "extra"


def split_h2(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Split body lines into (h2 heading, lines) blocks, ignoring fenced code."""
    blocks: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] | None = None
    in_fence = False
    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
        if not in_fence and line.startswith("## "):
            current = (line[3:].strip(), [])
            blocks.append(current)
        elif current is not None:
            current[1].append(line)
    return blocks


def is_empty(md: str) -> bool:
    """True for template leftovers such as 'Analogy:' with nothing after it."""
    text = re.sub(r"(?m)^\s*(Analogy|Where the analogy breaks):\s*$", "", md)
    return not text.strip()


def parse_items(lines: list[str], item_re: re.Pattern) -> list[tuple[re.Match, str]]:
    """Group a Markdown list into items: the first line plus indented continuation."""
    items: list[tuple[re.Match, list[str]]] = []
    for line in lines:
        m = item_re.match(line)
        if m:
            items.append((m, [m.group(2)]))
        elif items and (line.startswith(" ") or not line.strip()):
            items[-1][1].append(line)
        elif items and line.strip():
            items.append((None, [line]))  # stray text, kept as its own item
    out = []
    for m, body in items:
        if m is None:
            continue
        rest = body[1:]
        indent = min((len(l) - len(l.lstrip()) for l in rest if l.strip()), default=0)
        if m.re is OQ_ITEM:
            # Continuation lines of a checkbox item are wrapped prose.
            text = " ".join([body[0]] + [l.strip() for l in rest if l.strip()])
        else:
            # Log items may hold nested bullets: keep them as Markdown.
            nested = [l[min(indent, 2):] if l.strip() else "" for l in rest]
            text = "\n".join([body[0]] + nested).rstrip()
        out.append((m, text))
    return out


def parse_card(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = next((l[2:].strip() for l in lines if l.startswith("# ")), path.stem)

    header_end = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
    header = "\n".join(lines[:header_end])
    status = (re.search(r"^Status:\s*(\w+)", header, re.M) or [None, "stub"])[1].lower()
    updated = (re.search(r"^Last updated:\s*(\S+)", header, re.M) or [None, ""])[1]
    rel_match = re.search(r"^Related:(.*?)(?:\n\s*\n|\Z)", header, re.M | re.S)
    related = CARD_LINK.findall(rel_match.group(1)) if rel_match else []

    card = {
        "slug": path.stem,
        "title": title,
        "status": status,
        "updated": updated,
        "related": related,
        "sections": [],
        "questions": {},
        "open": [],
        "log": [],
        "viz": sorted(set(VIZ_FENCE.findall(text))),
        "links": sorted(set(CARD_LINK.findall(text)) - {path.stem}),
        "words": len(re.findall(r"\w+", text)),
    }

    for heading, body in split_h2(lines[header_end:]):
        kind = h2_kind(heading)
        md = "\n".join(body).strip("\n")
        if kind == "seven":
            current = None
            buf: list[str] = []
            for line in body + ["### 0. end"]:
                m = QUESTION_H3.match(line)
                if m:
                    if current is not None and not is_empty("\n".join(buf)):
                        card["questions"][current] = "\n".join(buf).strip("\n")
                    current, buf = m.group(1), []
                else:
                    buf.append(line)
        elif kind == "open":
            for m, item in parse_items(body, OQ_ITEM):
                card["open"].append({"done": m.group(1).lower() == "x", "md": item})
        elif kind == "log":
            for m, item in parse_items(body, LOG_ITEM):
                card["log"].append({"date": m.group(1), "md": item.strip()})
        elif not is_empty(md):
            planned = bool(re.search(r"Planned outline|\(fill with", md))
            card["sections"].append({"kind": kind, "heading": heading, "md": md, "planned": planned})
    return card


def parse_index() -> tuple[dict, list]:
    path = VAULT / "INDEX.md"
    if not path.exists():
        return {}, []
    text = path.read_text(encoding="utf-8")
    one_lines = {}
    for m in re.finditer(r"^\|\s*\[[^\]]+\]\(cards/([a-z0-9-]+)\.md\)\s*\|[^|]*\|\s*(.+?)\s*\|\s*$", text, re.M):
        one_lines[m.group(1)] = m.group(2)
    radar_notes = []
    radar_block = text.split("## Radar reports", 1)[1] if "## Radar reports" in text else ""
    for m in re.finditer(r"^- \[([^\]]+)\]\(radar/([^)]+)\.md\):\s*(.*?)(?=^- |\Z)", radar_block, re.M | re.S):
        radar_notes.append({"id": m.group(2), "md": " ".join(m.group(3).split())})
    return one_lines, radar_notes


def parse_radar(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), path.stem)
    return {"id": path.stem, "title": title, "md": text}


def git_meta() -> dict:
    def run(*args: str) -> str:
        try:
            return subprocess.run(["git", *args], cwd=VAULT, capture_output=True,
                                  text=True, encoding="utf-8", timeout=10).stdout.strip()
        except Exception:
            return ""
    return {"commit": run("rev-parse", "--short", "HEAD"),
            "commitDate": run("log", "-1", "--format=%cs")}


def main() -> None:
    one_lines, radar_notes = parse_index()
    cards = [parse_card(p) for p in sorted((VAULT / "cards").glob("*.md"))]
    for card in cards:
        card["oneLine"] = one_lines.get(card["slug"], "")
    radars = [parse_radar(p) for p in sorted((VAULT / "radar").glob("*.md"), reverse=True)]
    notes = {n["id"]: n["md"] for n in radar_notes}
    for r in radars:
        r["note"] = notes.get(r["id"], "")

    data = {
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        **git_meta(),
        "cards": cards,
        "radars": radars,
    }

    SITE.mkdir(exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    (SITE / "vault-data.js").write_text(f"window.VAULT = {payload};\n", encoding="utf-8")

    page = (VIEWER / "template.html").read_text(encoding="utf-8")
    (SITE / "index.html").write_text(page, encoding="utf-8")
    local = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
             "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
             "</head>\n<body>\n" + page + "\n</body>\n</html>\n")
    (SITE / "vault.html").write_text(local, encoding="utf-8")

    n_open = sum(1 for c in cards for q in c["open"] if not q["done"])
    print(f"Built {len(cards)} cards, {n_open} open questions, {len(radars)} radar reports "
          f"-> {SITE.relative_to(VAULT)}")


if __name__ == "__main__":
    main()
