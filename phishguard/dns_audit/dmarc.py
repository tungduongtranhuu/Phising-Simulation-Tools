"""DMARC record checks (A3)."""

from __future__ import annotations

from ..models import Finding, Severity
from . import resolver

SAMPLE = "v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain}; pct=100"


def parse(record: str) -> dict[str, str]:
    tags: dict[str, str] = {}
    for part in record.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            tags[k.strip().lower()] = v.strip()
    return tags


def check(domain: str, records: dict) -> list[Finding]:
    findings: list[Finding] = []
    dmarc = [t for t in resolver.txt(f"_dmarc.{domain}") if t.lower().startswith("v=dmarc1")]
    records["dmarc"] = dmarc

    if not dmarc:
        findings.append(
            Finding(
                "A3", "No DMARC record", Severity.HIGH,
                detail=f"No DMARC TXT record at _dmarc.{domain}.",
                recommendation=f'Publish: "{SAMPLE.format(domain=domain)}".',
            )
        )
        return findings

    tags = parse(dmarc[0])
    records["dmarc_tags"] = tags
    policy = tags.get("p", "none").lower()

    if policy == "none":
        findings.append(
            Finding(
                "A3", "DMARC policy is p=none (monitor only)", Severity.HIGH, detail=dmarc[0],
                recommendation="Move to p=quarantine, then p=reject once reports look clean.",
            )
        )

    if "rua" not in tags:
        findings.append(
            Finding(
                "A3", "DMARC has no aggregate reporting (rua)", Severity.MEDIUM, detail=dmarc[0],
                recommendation="Add rua=mailto:dmarc@yourdomain to receive aggregate reports.",
            )
        )

    pct = tags.get("pct")
    if pct and pct.isdigit() and int(pct) < 100:
        findings.append(
            Finding(
                "A3", f"DMARC pct={pct} (<100%)", Severity.LOW, detail=dmarc[0],
                recommendation="Set pct=100 so the policy applies to all mail.",
            )
        )
    return findings
