"""DNSSEC presence check (A5)."""

from __future__ import annotations

from ..models import Finding, Severity
from . import resolver


def check(domain: str, records: dict) -> list[Finding]:
    dnskey = resolver.query(domain, "DNSKEY")
    ds = resolver.query(domain, "DS")
    enabled = bool(dnskey) and bool(ds)
    records["dnssec"] = {"dnskey": bool(dnskey), "ds": bool(ds)}

    if enabled:
        return []
    return [
        Finding(
            "A5", "DNSSEC not enabled", Severity.MEDIUM,
            detail=f"DNSKEY={'yes' if dnskey else 'no'}, DS at parent={'yes' if ds else 'no'}.",
            recommendation="Enable DNSSEC at your DNS provider and publish a DS record at the registrar.",
        )
    ]
