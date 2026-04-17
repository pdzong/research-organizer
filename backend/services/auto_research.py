"""
Auto-research service.

Scrapes the HuggingFace Daily Papers feed (https://huggingface.co/papers) for
new arXiv ids and runs the full pipeline on each one:

    add → parse → metadata → analyze → for every detected `ApplicationIdea` in
    the analysis, save an `application` entry (with cached related papers).

Supports:

* `limit` — process at most N papers in a single batch.
* `continuous` — when True the runner keeps looping, sleeping for
  ``interval_seconds`` between batches.
* Cooperative cancellation via ``stop()``.

Designed to be friendly to the rest of the codebase: no new dependencies, all
side effects flow through the existing services / cache layer.
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import httpx

from . import cache_service
from .huggingface import add_paper, load_papers
from .openai_service import summarize_paper, extract_paper_sections
from .pdf_parser import download_and_parse_paper
from .semantic_scholar import get_paper_metadata


HF_PAPERS_URL = "https://huggingface.co/papers"
ARXIV_ID_RE = re.compile(r"/papers/(\d{4}\.\d{4,5})")


# ─── Source adapters ────────────────────────────────────────────────────────


async def fetch_huggingface_arxiv_ids(limit: int = 20) -> List[str]:
    """Scrape the HuggingFace papers index page for arXiv ids."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(HF_PAPERS_URL)
        response.raise_for_status()
        html = response.text

    seen: List[str] = []
    for match in ARXIV_ID_RE.finditer(html):
        arxiv_id = match.group(1)
        if arxiv_id not in seen:
            seen.append(arxiv_id)
        if len(seen) >= limit:
            break
    return seen


SOURCES: Dict[str, str] = {
    "huggingface": "HuggingFace Daily Papers",
}


# ─── Runner state ────────────────────────────────────────────────────────────


@dataclass
class AutoResearchStatus:
    state: str = "idle"  # idle | running | stopping | stopped | error
    source: str = "huggingface"
    limit: int = 5
    continuous: bool = False
    interval_seconds: int = 300

    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    current_arxiv_id: Optional[str] = None
    current_step: Optional[str] = None  # discover | parse | analyze | save | sleep

    processed_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    application_count: int = 0

    log: List[Dict[str, str]] = field(default_factory=list)
    last_error: Optional[str] = None

    def snapshot(self) -> Dict:
        return {
            "state": self.state,
            "source": self.source,
            "limit": self.limit,
            "continuous": self.continuous,
            "interval_seconds": self.interval_seconds,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "current_arxiv_id": self.current_arxiv_id,
            "current_step": self.current_step,
            "processed_count": self.processed_count,
            "skipped_count": self.skipped_count,
            "error_count": self.error_count,
            "application_count": self.application_count,
            "log": self.log[-50:],
            "last_error": self.last_error,
        }

    def push_log(self, level: str, message: str) -> None:
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
        }
        self.log.append(entry)
        # Keep memory bounded
        if len(self.log) > 500:
            self.log = self.log[-500:]
        print(f"[auto-research] {level.upper()}: {message}")


class AutoResearchRunner:
    """Singleton-ish background runner. One instance, one task at a time."""

    def __init__(self) -> None:
        self.status = AutoResearchStatus()
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    # ── lifecycle ─────────────────────────────────────────────────────────

    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(
        self,
        source: str = "huggingface",
        limit: int = 5,
        continuous: bool = False,
        interval_seconds: int = 300,
    ) -> Dict:
        if self.is_running():
            return {"success": False, "error": "auto-research is already running"}
        if source not in SOURCES:
            return {
                "success": False,
                "error": f"unknown source '{source}'. Known: {list(SOURCES)}",
            }

        # Reset status
        self.status = AutoResearchStatus(
            state="running",
            source=source,
            limit=limit,
            continuous=continuous,
            interval_seconds=interval_seconds,
            started_at=datetime.utcnow().isoformat(),
        )
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run())
        return {"success": True, "status": self.status.snapshot()}

    async def stop(self) -> Dict:
        if not self.is_running():
            return {"success": True, "status": self.status.snapshot()}
        self.status.state = "stopping"
        self.status.push_log("info", "stop requested")
        self._stop_event.set()
        return {"success": True, "status": self.status.snapshot()}

    def get_status(self) -> Dict:
        return self.status.snapshot()

    # ── main loop ─────────────────────────────────────────────────────────

    async def _run(self) -> None:
        try:
            while True:
                ids = await self._discover()
                for arxiv_id in ids:
                    if self._stop_event.is_set():
                        break
                    try:
                        await self._process_paper(arxiv_id)
                    except Exception as e:
                        self.status.error_count += 1
                        self.status.last_error = str(e)
                        self.status.push_log(
                            "error", f"{arxiv_id}: pipeline failed: {e}"
                        )

                if self._stop_event.is_set() or not self.status.continuous:
                    break

                self.status.current_step = "sleep"
                self.status.current_arxiv_id = None
                self.status.push_log(
                    "info",
                    f"sleeping {self.status.interval_seconds}s before next batch",
                )
                # Wake early if stop is requested
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.status.interval_seconds,
                    )
                    break
                except asyncio.TimeoutError:
                    pass

            self.status.state = "stopped" if self._stop_event.is_set() else "idle"
        except Exception as e:
            self.status.state = "error"
            self.status.last_error = str(e)
            self.status.push_log("error", f"runner crashed: {e}")
        finally:
            self.status.finished_at = datetime.utcnow().isoformat()
            self.status.current_step = None
            self.status.current_arxiv_id = None

    # ── pipeline steps ────────────────────────────────────────────────────

    async def _discover(self) -> List[str]:
        self.status.current_step = "discover"
        self.status.push_log(
            "info",
            f"discovering papers from {self.status.source} (limit={self.status.limit})",
        )

        if self.status.source == "huggingface":
            ids = await fetch_huggingface_arxiv_ids(limit=self.status.limit)
        else:
            ids = []

        self.status.push_log("info", f"discovered {len(ids)} candidate papers")
        return ids

    async def _process_paper(self, arxiv_id: str) -> None:
        self.status.current_arxiv_id = arxiv_id
        self.status.push_log("info", f"{arxiv_id}: starting pipeline")

        # Skip if we already have a full analysis cached
        analysis = cache_service.load_analysis(arxiv_id)
        if analysis and analysis.get("data"):
            self.status.skipped_count += 1
            self.status.push_log(
                "info", f"{arxiv_id}: already analyzed, deriving applications only"
            )
            await self._save_applications_from_analysis(arxiv_id, analysis["data"])
            return

        # 1. Make sure it's in the local papers list
        self.status.current_step = "register"
        existing_ids = {p.get("arxiv_id") for p in load_papers()}
        if arxiv_id not in existing_ids:
            try:
                await add_paper(f"https://arxiv.org/abs/{arxiv_id}")
            except Exception as e:
                self.status.push_log(
                    "warn",
                    f"{arxiv_id}: add_paper failed (continuing anyway): {e}",
                )

        # 2. Metadata (best-effort)
        self.status.current_step = "metadata"
        if not cache_service.load_metadata(arxiv_id):
            try:
                meta = await get_paper_metadata(arxiv_id)
                if meta.get("success"):
                    cache_service.save_metadata(arxiv_id, meta)
            except Exception as e:
                self.status.push_log(
                    "warn", f"{arxiv_id}: metadata failed: {e}"
                )

        # 3. Parse PDF
        self.status.current_step = "parse"
        markdown = cache_service.load_markdown(arxiv_id)
        if not markdown:
            parse_result = await download_and_parse_paper(
                f"https://arxiv.org/abs/{arxiv_id}"
            )
            if not parse_result.get("success") or not parse_result.get("markdown"):
                raise RuntimeError(
                    f"parse failed: {parse_result.get('error')}"
                )
            markdown = parse_result["markdown"]
            cache_service.save_markdown(arxiv_id, markdown)

        # 4. Extract structured sections (best-effort)
        sections_dict = cache_service.load_sections(arxiv_id)
        if not sections_dict:
            try:
                sections = await extract_paper_sections(markdown)
                cache_service.save_sections(arxiv_id, sections.model_dump())
                sections_dict = sections.model_dump()
            except Exception as e:
                self.status.push_log(
                    "warn", f"{arxiv_id}: section extraction failed: {e}"
                )

        # 5. Analyze
        self.status.current_step = "analyze"
        if sections_dict:
            from .models import PaperSections  # local import to avoid cycle

            clean_md = PaperSections(**sections_dict).to_clean_markdown()
        else:
            clean_md = markdown
        result = await summarize_paper(clean_md)
        if not result.get("success"):
            raise RuntimeError(f"analysis failed: {result.get('error')}")
        cache_service.save_analysis(arxiv_id, result)

        # 6. Derive applications from the analysis
        await self._save_applications_from_analysis(arxiv_id, result["data"])

        self.status.processed_count += 1
        self.status.push_log("info", f"{arxiv_id}: pipeline complete")

    async def _save_applications_from_analysis(
        self, arxiv_id: str, analysis_data: Dict
    ) -> None:
        self.status.current_step = "save"
        title = analysis_data.get("paper_title") or arxiv_id
        applications = (
            (analysis_data.get("summary") or {}).get("applications") or []
        )
        if not applications:
            self.status.push_log(
                "info", f"{arxiv_id}: analysis produced no application ideas"
            )
            return

        meta = cache_service.load_metadata(arxiv_id) or {}
        author_objs = meta.get("authors") or []
        authors = [a.get("name") for a in author_objs if a.get("name")] or [
            "Unknown"
        ]

        for app in applications:
            # Defensive: handle both old string format and structured.
            if isinstance(app, str):
                domain, utility = app[:60], app
            else:
                domain = app.get("domain") or ""
                utility = app.get("specific_utility") or ""
            if not domain:
                continue

            cache_service.save_application(
                application={"domain": domain, "specific_utility": utility},
                current_paper={
                    "title": title,
                    "authors": authors,
                    "arxiv_id": arxiv_id,
                },
                related_papers=[],  # auto-research keeps this fast; planner can enrich later
            )
            self.status.application_count += 1
            self.status.push_log(
                "info",
                f"{arxiv_id}: saved application '{domain}'",
            )


# Module-level singleton — FastAPI imports this directly.
runner = AutoResearchRunner()
