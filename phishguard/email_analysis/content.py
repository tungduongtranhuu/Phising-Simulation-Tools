"""Content/keyword analysis (B24-B26)."""

from __future__ import annotations

from ..config import keywords as keywords_cfg
from ..models import Finding, Severity


def analyse(subject: str, text: str, html: str) -> list[Finding]:
    cfg = keywords_cfg()
    blob = " ".join(x for x in (subject, text, html) if x).lower()
    findings: list[Finding] = []

    groups = (
        ("B24", "Pressure / urgency language", "pressure", Severity.LOW),
        ("B25", "Financial lure", "financial", Severity.LOW),
        ("B26", "Generic greeting", "generic_greeting", Severity.INFO),
    )
    for fid, title, key, sev in groups:
        hits = [kw for kw in cfg.get(key, []) if kw.lower() in blob]
        if hits:
            findings.append(
                Finding(
                    fid, title, sev,
                    detail="Matched: " + ", ".join(sorted(set(hits))[:8]),
                    recommendation="Social-engineering indicator; weigh with technical findings.",
                )
            )
    return findings
