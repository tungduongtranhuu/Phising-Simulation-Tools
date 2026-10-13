"""Threat-intelligence enrichment.

``build_enricher()`` returns a callable ``enrich(iocs) -> list[Finding]`` that
PhishGuard's email analyser calls. Enrichment is best-effort: a missing API key
or a failing API never stops the analysis.
"""

from __future__ import annotations

import os

from ..models import Finding, IOCs, Severity
from . import abuseipdb, urlhaus, virustotal
from .cache import Cache

try:
    import requests  # noqa: F401  (presence check)
    HAVE_REQUESTS = True
except ImportError:  # pragma: no cover
    HAVE_REQUESTS = False


def build_enricher(offline: bool = False):
    """Return an enrich callable, or None when enrichment is unavailable."""
    if offline or not HAVE_REQUESTS:
        return None

    vt_key = os.getenv("VT_API_KEY", "").strip()
    abuse_key = os.getenv("ABUSEIPDB_API_KEY", "").strip()
    urlhaus_key = os.getenv("URLHAUS_KEY", "").strip()

    if not any((vt_key, abuse_key, urlhaus_key)):
        return None

    cache = Cache()

    def enrich(iocs: IOCs) -> list[Finding]:
        findings: list[Finding] = []

        if vt_key:
            for h in iocs.hashes:
                res = virustotal.lookup_hash(h, vt_key, cache)
                if res and res.get("found") and res.get("malicious", 0) >= 3:
                    findings.append(
                        Finding(
                            "VT", f"VirusTotal: {res['malicious']} engines flag attachment",
                            Severity.CRITICAL, detail=f"sha256={h}",
                            recommendation="Known-malicious file; block the hash org-wide.",
                        )
                    )

        if abuse_key:
            for ip in iocs.ips:
                res = abuseipdb.lookup_ip(ip, abuse_key, cache)
                if res and res.get("score", 0) > 50:
                    findings.append(
                        Finding(
                            "ABUSE", f"AbuseIPDB score {res['score']} for sender IP",
                            Severity.HIGH,
                            detail=f"{ip} ({res.get('country')}, {res.get('isp')})",
                            recommendation="Sending IP has a bad reputation; block at the gateway.",
                        )
                    )

        if urlhaus_key or True:  # URLhaus works without a key for lookups
            for url in iocs.urls[:10]:
                res = urlhaus.lookup_url(url, urlhaus_key, cache)
                if res and res.get("listed"):
                    findings.append(
                        Finding(
                            "VT", f"URLhaus lists URL as {res.get('threat') or 'malicious'}",
                            Severity.CRITICAL, detail=url,
                            recommendation="Known malware URL; block the domain.",
                        )
                    )

        return findings

    return enrich
