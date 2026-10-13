"""VirusTotal lookups. We only submit HASHES (never upload files)."""

from __future__ import annotations

import requests

_BASE = "https://www.virustotal.com/api/v3"


def lookup_hash(sha256: str, api_key: str, cache) -> dict | None:
    key = f"vt:hash:{sha256}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        r = requests.get(
            f"{_BASE}/files/{sha256}",
            headers={"x-apikey": api_key}, timeout=10,
        )
        if r.status_code == 404:
            result = {"found": False}
        elif r.ok:
            stats = r.json()["data"]["attributes"]["last_analysis_stats"]
            result = {
                "found": True,
                "malicious": int(stats.get("malicious", 0)),
                "suspicious": int(stats.get("suspicious", 0)),
            }
        else:
            return None
    except Exception:
        return None
    cache.set(key, result)
    return result
