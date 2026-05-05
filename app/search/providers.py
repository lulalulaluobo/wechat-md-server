from __future__ import annotations

from typing import TypedDict


class SearchResult(TypedDict, total=False):
    title: str
    url: str
    source_name: str
    published_at: str
    snippet: str
    provider: str
    already_ingested: bool
    score: float | None


class SearchProviderError(RuntimeError):
    pass


SUPPORTED_WECHAT_PROVIDERS = {"sogou_weixin"}
UNSUPPORTED_WECHAT_PROVIDERS = {"local_cache", "web_search"}


def search_wechat_provider(query: str, *, provider: str = "sogou_weixin", limit: int = 10) -> list[SearchResult]:
    normalized_provider = str(provider or "sogou_weixin").strip() or "sogou_weixin"
    if normalized_provider in UNSUPPORTED_WECHAT_PROVIDERS:
        raise SearchProviderError(f"{normalized_provider} 暂未支持")
    if normalized_provider not in SUPPORTED_WECHAT_PROVIDERS:
        raise SearchProviderError("provider 仅支持 sogou_weixin、local_cache 或 web_search")
    from app.search.sogou_weixin import search_sogou_weixin

    return search_sogou_weixin(query, limit=limit)
