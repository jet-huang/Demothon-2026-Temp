from __future__ import annotations

import os
from typing import Any

import httpx
from loguru import logger

PIXABAY_ENDPOINT = "https://pixabay.com/api/"
DEFAULT_TIMEOUT_SECONDS = 5.0


def _resolve_api_key(tool_config: dict[str, Any] | None) -> str | None:
    if tool_config and tool_config.get("api_key"):
        return str(tool_config["api_key"])
    return os.environ.get("PIXABAY_API_KEY")


def _shape_hit(hit: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": hit.get("id"),
        "tags": hit.get("tags"),
        "page_url": hit.get("pageURL"),
        "preview_url": hit.get("previewURL"),
        "web_url": hit.get("webformatURL"),
        "large_url": hit.get("largeImageURL"),
        "user": hit.get("user"),
        "width": hit.get("imageWidth"),
        "height": hit.get("imageHeight"),
    }


def search_images(
    query: str,
    per_page: int = 3,
    image_type: str = "photo",
    safesearch: bool = True,
    orientation: str | None = None,
    category: str | None = None,
    tool_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    api_key = _resolve_api_key(tool_config)
    if not api_key:
        return {
            "ok": False,
            "query": query,
            "count": 0,
            "results": [],
            "error": "PIXABAY_API_KEY not set",
        }

    per_page = max(3, min(int(per_page), 200))
    params: dict[str, Any] = {
        "key": api_key,
        "q": query,
        "per_page": per_page,
        "image_type": image_type,
        "safesearch": "true" if safesearch else "false",
    }
    if orientation:
        params["orientation"] = orientation
    if category:
        params["category"] = category

    last_error: str | None = None
    for attempt in (1, 2):
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
                resp = client.get(PIXABAY_ENDPOINT, params=params)
            if resp.status_code >= 500:
                last_error = f"HTTP {resp.status_code}"
                logger.warning("pixabay 5xx (attempt {}): {}", attempt, resp.status_code)
                continue
            resp.raise_for_status()
            payload = resp.json()
            hits = payload.get("hits", []) or []
            results = [_shape_hit(h) for h in hits]
            return {
                "ok": True,
                "query": query,
                "count": len(results),
                "total_hits": payload.get("totalHits", 0),
                "results": results,
            }
        except httpx.HTTPError as exc:
            last_error = str(exc)
            logger.warning("pixabay error (attempt {}): {}", attempt, exc)
            continue

    return {
        "ok": False,
        "query": query,
        "count": 0,
        "results": [],
        "error": last_error or "unknown error",
    }
