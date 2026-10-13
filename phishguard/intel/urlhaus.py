"""URLhaus (abuse.ch) lookups for malware-distribution URLs."""

from __future__ import annotations

import requests

_URL = "https://urlhaus-api.abuse.ch/v1/url/"


def lookup_url(url: str, api_key: str, cache) -> dict | None:
    key = f"urlhaus:{url}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    headers = {"Auth-Key": api_key} if api_key else {}
    try:
        r = requests.post(_URL, data={"url": url}, headers=headers, timeout=10)
        if not r.ok:
            return None
        data = r.json()
        result = {
            "listed": data.get("query_status") == "ok",
            "threat": data.get("threat", ""),
            "status": data.get("url_status", ""),
        }
    except Exception:
        return None
    cache.set(key, result)
    return result
