"""Paper discovery sources.

To add a new source: implement a provider class with `id`, `label`,
`fields()` and `async discover(query, field, days, limit, sort)` returning
`list[SourcePaper]` (see arxiv.py / openalex.py), then register an instance
in PROVIDERS below.
"""
from .arxiv import ArxivProvider
from .models import SourceField, SourceInfo, SourcePaper
from .openalex import OpenAlexProvider

_provider_list = [
    ArxivProvider(),
    OpenAlexProvider(),
]

PROVIDERS = {provider.id: provider for provider in _provider_list}


def list_sources() -> list[SourceInfo]:
    return [
        SourceInfo(id=p.id, label=p.label, fields=p.fields())
        for p in PROVIDERS.values()
    ]


def get_provider(source_id: str):
    return PROVIDERS.get(source_id)


__all__ = [
    "PROVIDERS",
    "SourceField",
    "SourceInfo",
    "SourcePaper",
    "get_provider",
    "list_sources",
]
