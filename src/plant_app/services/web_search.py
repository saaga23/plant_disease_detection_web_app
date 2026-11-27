"""Web search service (SerpAPI-backed, optional).

The legacy app shipped a placeholder SerpAPI key in source. Now the key comes
from the SERPAPI_API_KEY environment variable; when absent, the UI shows a
configuration message instead of attempting a doomed request.
"""
from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

SEARCH_URL = "https://serpapi.com/search"
REQUEST_TIMEOUT_S = 15


def web_search(query: str, api_key: str | None, num: int = 5) -> tuple[list[dict] | None, str]:
    """Return (results, note). results is None when unavailable."""
    if not api_key:
        return None, (
            "Web search is not configured. Set the SERPAPI_API_KEY environment "
            "variable (see .env.example) to enable this page."
        )
    if not query.strip():
        return None, "Enter a search query."
    try:
        resp = requests.get(
            SEARCH_URL,
            params={"q": query.strip(), "api_key": api_key, "num": num},
            timeout=REQUEST_TIMEOUT_S,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Web search failed: %s", exc)
        return None, "The search service could not be reached. Try again later."
    results = [
        {"title": r.get("title", ""), "link": r.get("link", ""), "snippet": r.get("snippet", "")}
        for r in (data.get("organic_results") or [])[:num]
    ]
    if not results:
        return results, "No results returned for that query."
    return results, "Results via SerpAPI. Always verify agricultural advice against official extension services."
