"""SPF record checks (A2)."""

from __future__ import annotations

import re

from ..models import Finding, Severity
from . import resolver


def _spf_records(domain: str) -> list[str]:
    return [t for t in resolver.txt(domain) if t.lower().startswith("v=spf1")]


def _count_lookups(record: str, domain: str, seen: set[str] | None = None, depth: int = 0) -> int:
    """Approximate the RFC 7208 10-lookup limit (include/a/mx/ptr/exists/redirect)."""
    if seen is None:
        seen = set()
    if depth > 10:
        return 11
    count = 0
    for token in record.split():
        tl = token.lower()
        if tl.startswith(("include:", "a:", "mx:", "ptr", "exists:", "redirect=")) or tl in ("a", "mx"):
            count += 1
            target = token.split(":", 1)[-1].split("=", 1)[-1] if (":" in token or "=" in token) else domain
            if tl.startswith(("include:", "redirect=")) and target not in seen:
                seen.add(target)
                for rec in _spf_records(target):
                    count += _count_lookups(rec, target, seen, depth + 1)
    return count


def check(domain: str, records: dict) -> list[Finding]:
    findings: list[Finding] = []
    spf = _spf_records(domain)
    records["spf"] = spf

    if not spf:
        findings.append(
            Finding(
                "A2", "No SPF record", Severity.HIGH, detail=f"No v=spf1 TXT record for {domain}.",
                recommendation='Publish an SPF record, e.g. "v=spf1 include:_spf.google.com -all".',
            )
        )
        return findings

    if len(spf) > 1:
        findings.append(
            Finding(
                "A2", "Multiple SPF records", Severity.HIGH,
                detail=f"{len(spf)} SPF records found; RFC 7208 allows exactly one.",
                recommendation="Merge into a single SPF TXT record.",
            )
        )

    record = spf[0]
    all_m = re.search(r"([~\-+?])all\b", record.lower())
    mech = all_m.group(1) if all_m else None
    if mech == "+":
        findings.append(
            Finding(
                "A2", "SPF uses +all (passes everyone)", Severity.HIGH, detail=record,
                recommendation='Change "+all" to "-all" (hard fail) or "~all" (soft fail).',
            )
        )
    elif mech == "?":
        findings.append(
            Finding(
                "A2", "SPF uses ?all (neutral)", Severity.MEDIUM, detail=record,
                recommendation='Use "-all" to explicitly reject unauthorised senders.',
            )
        )
    elif mech is None:
        findings.append(
            Finding(
                "A2", "SPF has no 'all' mechanism", Severity.MEDIUM, detail=record,
                recommendation='Terminate the record with "-all" or "~all".',
            )
        )

    lookups = _count_lookups(record, domain)
    records["spf_lookups"] = lookups
    if lookups > 10:
        findings.append(
            Finding(
                "A2", f"SPF exceeds 10 DNS lookups ({lookups})", Severity.MEDIUM, detail=record,
                recommendation="Flatten includes or remove unused mechanisms to stay <=10 lookups.",
            )
        )
    return findings
