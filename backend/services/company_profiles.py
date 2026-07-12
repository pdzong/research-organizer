"""
Company research profiles (P2-001).

A CompanyProfile captures what a company builds, which technologies it
depends on, and which research topics it needs to watch. Profiles drive
company-targeted discovery (OpenAlex searches from watch topics) and
strategic-fit scoring of individual papers.

Storage: ``backend/data/company_profiles.json``
Shape: ``{"active_profile_id": str | null, "profiles": [ {...}, ... ]}``
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

PROFILES_FILE = Path(__file__).parent.parent / "data" / "company_profiles.json"


class CompanyProfile(BaseModel):
    """Everything the research pipeline needs to know about one company."""

    id: str
    name: str
    industry: Optional[str] = None
    description: Optional[str] = Field(
        None, description="What the company builds / sells, its market and moat."
    )
    tech_stack: List[str] = Field(
        default_factory=list, description="Key technologies the company relies on."
    )
    strategic_questions: List[str] = Field(
        default_factory=list,
        description="Open questions the company wants research to answer.",
    )
    watch_topics: List[str] = Field(
        default_factory=list,
        description="Search topics used for automated discovery (OpenAlex queries).",
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Strategic assumptions; papers challenging these are surprise-risk (P3).",
    )
    created_at: str = ""
    updated_at: str = ""


class CompanyProfileInput(BaseModel):
    """User-supplied fields for create/update (id and timestamps are managed)."""

    name: str
    industry: Optional[str] = None
    description: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    strategic_questions: List[str] = Field(default_factory=list)
    watch_topics: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or uuid.uuid4().hex[:8]


def _load_store() -> Dict[str, Any]:
    if not PROFILES_FILE.exists():
        return {"active_profile_id": None, "profiles": []}
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("active_profile_id", None)
        data.setdefault("profiles", [])
        return data
    except Exception as e:  # pragma: no cover
        print(f"⚠️ company_profiles: failed to read {PROFILES_FILE}: {e}")
        return {"active_profile_id": None, "profiles": []}


def _save_store(store: Dict[str, Any]) -> None:
    PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)


def list_profiles() -> List[CompanyProfile]:
    return [CompanyProfile(**p) for p in _load_store()["profiles"]]


def get_profile(profile_id: str) -> Optional[CompanyProfile]:
    for p in _load_store()["profiles"]:
        if p.get("id") == profile_id:
            return CompanyProfile(**p)
    return None


def get_active_profile() -> Optional[CompanyProfile]:
    store = _load_store()
    active_id = store.get("active_profile_id")
    if not active_id:
        return None
    for p in store["profiles"]:
        if p.get("id") == active_id:
            return CompanyProfile(**p)
    return None


def create_profile(data: CompanyProfileInput) -> CompanyProfile:
    store = _load_store()
    base_slug = _slugify(data.name)
    existing_ids = {p.get("id") for p in store["profiles"]}
    profile_id = base_slug
    suffix = 2
    while profile_id in existing_ids:
        profile_id = f"{base_slug}-{suffix}"
        suffix += 1

    now = datetime.now().isoformat()
    profile = CompanyProfile(
        id=profile_id, created_at=now, updated_at=now, **data.model_dump()
    )
    store["profiles"].append(profile.model_dump())
    # First profile becomes active automatically.
    if not store.get("active_profile_id"):
        store["active_profile_id"] = profile.id
    _save_store(store)
    return profile


def update_profile(profile_id: str, data: CompanyProfileInput) -> Optional[CompanyProfile]:
    store = _load_store()
    for i, p in enumerate(store["profiles"]):
        if p.get("id") == profile_id:
            updated = CompanyProfile(
                id=profile_id,
                created_at=p.get("created_at", ""),
                updated_at=datetime.now().isoformat(),
                **data.model_dump(),
            )
            store["profiles"][i] = updated.model_dump()
            _save_store(store)
            return updated
    return None


def delete_profile(profile_id: str) -> bool:
    store = _load_store()
    before = len(store["profiles"])
    store["profiles"] = [p for p in store["profiles"] if p.get("id") != profile_id]
    if len(store["profiles"]) == before:
        return False
    if store.get("active_profile_id") == profile_id:
        store["active_profile_id"] = (
            store["profiles"][0]["id"] if store["profiles"] else None
        )
    _save_store(store)
    return True


def set_active_profile(profile_id: str) -> bool:
    store = _load_store()
    if not any(p.get("id") == profile_id for p in store["profiles"]):
        return False
    store["active_profile_id"] = profile_id
    _save_store(store)
    return True


def get_active_profile_id() -> Optional[str]:
    return _load_store().get("active_profile_id")
