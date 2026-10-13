"""AbuseIPDB reputation lookup for the sending IP."""

from __future__ import annotations

import requests

_URL = "https://api.abuseipdb.com/api/v2/check"


def lookup_ip(ip: str, api_key: str, cache) -> dict | None:
    key = f"abuse:{ip}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        r = requests.get(
            _URL,
            headers={"Key": api_key, "Accept": "application/json"},
            params={"ipAddress": ip, "maxAgeInDays": 90},
            timeout=10,
        )
        if not r.ok:
            return None
        data = r.json().get("data", {})
        result = {
            "score": int(data.get("abuseConfidenceScore", 0)),
            "country": data.get("countryCode", ""),
            "isp": data.get("isp", ""),
        }
    except Exception:
        return None
    cache.set(key, result)
    return result
