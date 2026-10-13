"""Zone transfer (AXFR) check (A7).

ETHICS: only run against domains you own, are authorised to test, or that exist
for learning (e.g. zonetransfer.me). AXFR is a read-only query but an open zone
transfer is a real misconfiguration worth reporting.
"""

from __future__ import annotations

from ..models import Finding, Severity
from . import resolver

try:
    import dns.query
    import dns.zone
    HAVE_DNS = True
except ImportError:  # pragma: no cover
    HAVE_DNS = False


def check(domain: str, records: dict, enabled: bool = True) -> list[Finding]:
    if not enabled or not HAVE_DNS:
        records["zone_transfer"] = {"tested": False}
        return []

    findings: list[Finding] = []
    open_ns: list[str] = []
    for ns in resolver.nameservers(domain):
        try:
            xfr = dns.query.xfr(ns, domain, timeout=5, lifetime=8)
            zone = dns.zone.from_xfr(xfr)
            if zone and zone.nodes:
                open_ns.append(ns)
        except Exception:
            continue

    records["zone_transfer"] = {"tested": True, "open_on": open_ns}
    if open_ns:
        findings.append(
            Finding(
                "A7", "Zone transfer (AXFR) allowed", Severity.HIGH,
                detail=f"Name servers leaking the full zone: {', '.join(open_ns)}.",
                recommendation="Restrict AXFR to authorised secondary servers only.",
            )
        )
    return findings
