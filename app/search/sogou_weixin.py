from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

from app.search.providers import SearchProviderError, SearchResult
from app.wechat_sync import USER_AGENT


SOGOU_WEIXIN_SEARCH_URL = "https://weixin.sogou.com/weixin"


def search_sogou_weixin(query: str, *, limit: int = 10) -> list[SearchResult]:
    normalized_query = str(query or "").strip()
    if not normalized_query:
        raise SearchProviderError("搜索关键词不能为空")
    normalized_limit = 20 if int(limit or 10) == 20 else 10
    try:
        response = requests.get(
            SOGOU_WEIXIN_SEARCH_URL,
            params={"type": "2", "query": normalized_query, "ie": "utf8"},
            headers={
                "User-Agent": USER_AGENT,
                "Referer": "https://weixin.sogou.com/",
            },
            timeout=12,
        )
        response.raise_for_status()
    except Exception as error:
        raise SearchProviderError(f"搜狗微信搜索失败：{error}") from error

    return parse_sogou_weixin_results(response.text, limit=normalized_limit)


def parse_sogou_weixin_results(html: str, *, limit: int = 10) -> list[SearchResult]:
    soup = BeautifulSoup(html or "", "html.parser")
    results: list[SearchResult] = []
    seen: set[str] = set()
    for item in soup.select("ul.news-list > li, .news-list li"):
        link = item.select_one("h3 a[href]") or item.select_one("a[href]")
        if link is None:
            continue
        url = _normalize_result_url(str(link.get("href") or ""))
        if not url or "mp.weixin.qq.com" not in url or url in seen:
            continue
        seen.add(url)
        title = " ".join(link.get_text("", strip=False).split())
        snippet_el = item.select_one(".txt-info") or item.select_one("p")
        source_el = item.select_one(".account") or item.select_one(".s-p a")
        published_el = item.select_one(".s2") or item.select_one("[t]")
        results.append(
            {
                "title": title,
                "url": url,
                "source_name": source_el.get_text(" ", strip=True) if source_el else "",
                "published_at": published_el.get_text(" ", strip=True) if published_el else "",
                "snippet": snippet_el.get_text(" ", strip=True) if snippet_el else "",
                "provider": "sogou_weixin",
                "already_ingested": False,
                "score": None,
            }
        )
        if len(results) >= max(int(limit or 10), 1):
            break
    return results


def _normalize_result_url(raw_url: str) -> str:
    url = unquote(str(raw_url or "").strip())
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.netloc.endswith("sogou.com") and parsed.path.endswith("/link"):
        query = parse_qs(parsed.query)
        candidate = (query.get("url") or [""])[0]
        if candidate:
            url = unquote(candidate)
    if url.startswith("//"):
        url = f"https:{url}"
    return url
