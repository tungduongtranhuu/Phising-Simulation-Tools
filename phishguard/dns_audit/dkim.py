"""DKIM selector discovery (A4).

We cannot enumerate every selector, so we probe a list of common ones. If an
email is being analysed, its real selector (from the DKIM-Signature ``s=`` tag)
can be passed in to check precisely.
"""

from __future__ import annotations

import base64

from ..models import Finding, Severity
from . import resolver

COMMON_SELECTORS = [
    "default", "google", "selector1", "selector2", "k1", "k2",
    "mail", "dkim", "s1", "s2", "smtp", "mandrill", "mailjet",
]


def _rsa_bits(record: str) -> int | None:
    """Rough public-key size estimate from the p= base64 blob."""
    for part in record.split(";"):
        part = part.strip()
        if part.lower().startswith("p="):
            b64 = part[2:].strip()
            if not b64:
                return 0
            try:
                der = base64.b64decode(b64 + "===")
                # ~ DER overhead; 8 bits per byte.
                return (len(der) - 38) * 8
            except Exception:
                return None
    return None


def check(domain: str, records: dict, extra_selectors: list[str] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    selectors = list(dict.fromkeys((extra_selectors or []) + COMMON_SELECTORS))
    found: dict[str, str] = {}
    for sel in selectors:
        answers = resolver.txt(f"{sel}._domainkey.{domain}")
        rec = next((a for a in answers if "k=" in a.lower() or "p=" in a.lower()), None)
        if rec:
            found[sel] = rec

    records["dkim_selectors"] = list(found.keys())

    if not found:
        findings.append(
            Finding(
                "A4", "No DKIM record for common selectors", Severity.MEDIUM,
                detail=f"Tried: {', '.join(selectors)}.",
                recommendation="Publish DKIM keys and sign outbound mail (>=1024-bit, prefer 2048).",
            )
        )
        return findings

    for sel, rec in found.items():
        bits = _rsa_bits(rec)
        if bits == 0:
            findings.append(
                Finding(
                    "A4", f"DKIM selector '{sel}' has an empty key (revoked)", Severity.MEDIUM,
                    detail=rec, recommendation="Remove revoked selectors or republish a valid key.",
                )
            )
        elif bits is not None and 0 < bits < 1024:
            findings.append(
                Finding(
                    "A4", f"DKIM selector '{sel}' key < 1024 bits (~{bits})", Severity.MEDIUM,
                    detail=rec, recommendation="Rotate to a 2048-bit RSA key.",
                )
            )
    return findings
