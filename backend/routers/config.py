"""
Runtime configuration endpoints.

Currently exposes the per-role LLM provider/model configuration used by the
rest of the backend. The UI pulls this to render the Settings modal and
PUTs updates back.
"""

from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services import llm_config
from services import llm_clients


router = APIRouter()


class RoleConfig(BaseModel):
    provider: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)


class LlmConfigPayload(BaseModel):
    roles: Dict[str, RoleConfig] = Field(default_factory=dict)


@router.get("/config/llm")
async def get_llm_config(
    live_models: bool = Query(
        True,
        description="Fetch each provider's current model catalog. Falls back to the static list on error.",
    ),
):
    live_catalog = None
    if live_models:
        health_keys = llm_config.provider_health()
        to_fetch = [pid for pid, info in health_keys.items() if info.get("key_present")]
        if to_fetch:
            live_catalog = await llm_clients.list_all_provider_models(providers=to_fetch)
    return {
        "success": True,
        "roles": llm_config.get_full_config(),
        "defaults": llm_config.DEFAULTS,
        "role_descriptions": llm_config.describe_roles(),
        "providers": llm_config.provider_health(live_catalog=live_catalog),
    }


@router.put("/config/llm")
async def put_llm_config(payload: LlmConfigPayload):
    try:
        updates = {
            role: cfg.model_dump(exclude_none=True)
            for role, cfg in payload.roles.items()
        }
        effective = llm_config.update_config(updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "roles": effective}


@router.post("/config/llm/reset")
async def reset_llm_config():
    effective = llm_config.reset_config()
    return {"success": True, "roles": effective}
