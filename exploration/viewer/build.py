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
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
VIEWER = VAULT / "viewer"
SITE = VIEWER / "site"
PAPERS_CACHE = VIEWER / "papers.json"  # committed, so builds work offline

# "arXiv:2412.06769" (any era), or a bare post-2015 id such as 2611.17610.
ARXIV_ID = re.compile(r"arXiv:\s?(\d{4}\.\d{4,5})|\b(\d{2}(?:0[1-9]|1[0-2])\.\d{5})\b")

CARD_LINK = re.compile(r"\]\((?:\.\./cards/|\./)?([a-z0-9-]+)\.md\)")
FENCE = re.compile(r"^\s*(```|~~~)")
QUESTION_H3 = re.compile(r"^###\s+(\d)\.\s+(.+?)\s*$")
OQ_ITEM = re.compile(r"^- \[( |x|X)\]\s?(.*)$")
LOG_ITEM = re.compile(r"^- (\d{4}-\d{2}-\d{2}):\s?(.*)$")
CORE_ITEM = re.compile(r"^\d+\.\s+(.+(?:\n {3,}.+)*)", re.M)
VIZ_FENCE = re.compile(r"^\s*```(mermaid|frontier|boundary|embed)\b", re.M)

H2_KIND = [
    (re.compile(r"^L0\b"), "l0"),
    (re.compile(r"^Core ideas", re.I), "core"),
    (re.compile(r"^Superseded", re.I), "superseded"),
    (re.compile(r"^Archive", re.I), "archive"),
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
        "core": [],
        "shelf": [],  # superseded and archived entries, shown collapsed
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
        elif kind == "core":
            card["core"] = [" ".join(m.group(1).split()) for m in CORE_ITEM.finditer(md)]
        elif kind in ("superseded", "archive"):
            card["shelf"] += [dict(e, kind=kind) for e in parse_shelf(body)]
        elif kind == "log":
            for m, item in parse_items(body, LOG_ITEM):
                card["log"].append({"date": m.group(1), "md": item.strip()})
        elif not is_empty(md):
            planned = bool(re.search(r"Planned outline|\(fill with", md))
            card["sections"].append({"kind": kind, "heading": heading, "md": md, "planned": planned})
            if kind == "l4":
                card["sources"] = parse_sources(body)
    card["cites"] = cited_ids(text)
    return card


def parse_shelf(lines: list[str]) -> list[dict]:
    """H3 entries of a Superseded or Archive section; text before the first H3 is the intro."""
    out: list[dict] = []
    for line in lines:
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            title = m.group(1)
            date = re.search(r"\((?:superseded|archived)\s+(\d{4}-\d{2}-\d{2})[^)]*\)\s*$", title)
            if title.startswith("<"):  # template placeholder
                out.append({"title": "", "date": "", "md": [], "skip": True}); continue
            out.append({"title": title[:date.start()].strip() if date else title,
                        "date": date.group(1) if date else "", "md": []})
        elif out:
            out[-1]["md"].append(line)
    return [dict(e, md="\n".join(e["md"]).strip("\n")) for e in out if not e.get("skip")]


def cited_ids(text: str) -> list[str]:
    """arXiv ids in order of first appearance."""
    seen: dict[str, None] = {}
    for m in ARXIV_ID.finditer(text):
        seen.setdefault(m.group(1) or m.group(2), None)
    return list(seen)


def parse_sources(lines: list[str]) -> list[dict]:
    """Rows of the L4 table: which ids a row cites, why to read it, verification."""
    out = []
    for line in lines:
        if not line.startswith("|") or set(line) <= set("|- "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        ids = cited_ids(line)
        if not ids or len(cells) < 3:
            continue
        for pid in ids:
            out.append({"id": pid, "why": cells[2] if len(cells) > 3 else "",
                        "verified": cells[-1]})
    return out


def load_cache() -> dict:
    try:
        return json.loads(PAPERS_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def fetch_arxiv(ids: list[str], cache: dict) -> None:
    """Fill the cache from the arXiv API (titles, authors, year, abstract)."""
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for i in range(0, len(ids), 40):
        batch = ids[i:i + 40]
        url = ("https://export.arxiv.org/api/query?max_results=50&id_list="
               + urllib.parse.quote(",".join(batch), safe=","))
        req = urllib.request.Request(url, headers={"User-Agent": "exploration-vault-viewer/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                root = ET.fromstring(resp.read())
        except Exception as err:  # network is optional
            print(f"arXiv lookup skipped ({err}); cached titles only.")
            return
        found = set()
        for entry in root.findall("a:entry", ns):
            raw_id = (entry.findtext("a:id", "", ns) or "").rsplit("/", 1)[-1]
            pid = re.sub(r"v\d+$", "", raw_id)
            title = " ".join((entry.findtext("a:title", "", ns) or "").split())
            if pid not in batch or not title or title == "Error":
                continue
            summary = " ".join((entry.findtext("a:summary", "", ns) or "").split())
            if len(summary) > 480:
                cut = summary[:480]
                summary = cut[: cut.rfind(". ") + 1] if ". " in cut else cut.rsplit(" ", 1)[0] + "…"
            prim = entry.find("x:primary_category", ns)
            cache[pid] = {
                "found": True,
                "title": title,
                "authors": [a.findtext("a:name", "", ns) for a in entry.findall("a:author", ns)],
                "year": (entry.findtext("a:published", "", ns) or "")[:4],
                "category": prim.get("term") if prim is not None else "",
                "summary": summary,
                "checked": today,
            }
            found.add(pid)
        for pid in batch:
            if pid not in found:
                cache[pid] = {"found": False, "checked": today}
        if i + 40 < len(ids):
            time.sleep(3)  # arXiv asks for a pause between API calls


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
    return {"id": path.stem, "title": title, "md": text, "cites": cited_ids(text)}


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

    all_ids = list(dict.fromkeys([i for c in cards for i in c["cites"]] +
                                 [i for r in radars for i in r["cites"]]))
    cache = load_cache()
    missing = [i for i in all_ids if i not in cache]
    if missing and "--offline" not in sys.argv:
        print(f"Looking up {len(missing)} new arXiv ids...")
        fetch_arxiv(missing, cache)
        PAPERS_CACHE.write_text(json.dumps(dict(sorted(cache.items())), ensure_ascii=False, indent=1),
                                encoding="utf-8")
    papers = {}
    for pid in all_ids:
        entry = dict(cache.get(pid, {"found": None}))
        entry["cards"] = [c["slug"] for c in cards if pid in c["cites"]]
        entry["radars"] = [r["id"] for r in radars if pid in r["cites"]]
        entry["checks"] = {c["slug"]: s["verified"] for c in cards
                           for s in c.get("sources", []) if s["id"] == pid}
        papers[pid] = entry

    data = {
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        **git_meta(),
        "cards": cards,
        "radars": radars,
        "papers": papers,
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
