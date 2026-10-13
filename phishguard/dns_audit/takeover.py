"""Subdomain discovery (crt.sh) + dangling-CNAME takeover check (A11).

Fingerprints are inspired by the community project 'can-i-take-over-xyz'.
Only run subdomain enumeration against domains you are authorised to test.
"""

from __future__ import annotations

import json

from ..models import Finding, Severity
from . import resolver

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]

# CNAME target substring -> service name (dangling = likely takeover).
TAKEOVER_FINGERPRINTS = {
    "github.io": "GitHub Pages",
    "herokuapp.com": "Heroku",
    "herokudns.com": "Heroku",
    "s3.amazonaws.com": "AWS S3",
    "cloudfront.net": "AWS CloudFront",
    "azurewebsites.net": "Azure App Service",
    "cloudapp.net": "Azure",
    "trafficmanager.net": "Azure Traffic Manager",
    "ghost.io": "Ghost",
    "fastly.net": "Fastly",
    "zendesk.com": "Zendesk",
    "surge.sh": "Surge.sh",
    "bitbucket.io": "Bitbucket",
    "readthedocs.io": "Read the Docs",
    "wordpress.com": "WordPress",
    "pantheonsite.io": "Pantheon",
    "helpscoutdocs.com": "Help Scout",
}


def _crtsh_subdomains(domain: str, limit: int = 50) -> list[str]:
    if requests is None:
        return []
    try:
        r = requests.get(
            "https://crt.sh/", params={"q": f"%.{domain}", "output": "json"}, timeout=10,
        )
        if not r.ok:
            return []
        data = json.loads(r.text)
    except Exception:
        return []
    subs: set[str] = set()
    for entry in data:
        for name in str(entry.get("name_value", "")).splitlines():
            name = name.strip().lower().lstrip("*.")
            if name.endswith(domain) and name != domain:
                subs.add(name)
    return sorted(subs)[:limit]


def check(domain: str, records: dict, enabled: bool = True) -> list[Finding]:
    if not enabled or requests is None:
        records["subdomains"] = {"tested": False}
        return []

    findings: list[Finding] = []
    subs = _crtsh_subdomains(domain)
    dangling: list[dict] = []

    for sub in subs:
        cnames = resolver.query(sub, "CNAME")
        if not cnames:
            continue
        target = cnames[0].rstrip(".").lower()
        service = next((svc for fp, svc in TAKEOVER_FINGERPRINTS.items() if fp in target), None)
        if not service:
            continue
        # Dangling if the CNAME target no longer resolves to an address.
        resolves = bool(resolver.query(target, "A") or resolver.query(target, "AAAA"))
        if not resolves:
            dangling.append({"subdomain": sub, "cname": target, "service": service})

    records["subdomains"] = {
        "tested": True, "count": len(subs), "dangling": dangling,
    }

    for d in dangling:
        findings.append(
            Finding(
                "A11", f"Possible subdomain takeover: {d['subdomain']}", Severity.HIGH,
                detail=f"CNAME -> {d['cname']} ({d['service']}) does not resolve (dangling).",
                recommendation=f"Remove the dangling CNAME or reclaim the {d['service']} resource.",
            )
        )
    return findings
