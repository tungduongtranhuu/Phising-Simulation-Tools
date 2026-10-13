"""Sender domain analysis: display-name spoof, lookalike, punycode, age (B4,B8-B10)."""

from __future__ import annotations

from datetime import datetime, timezone

from ..config import brands as brands_cfg
from ..config import scoring
from ..models import Finding, Severity
from ..utils import levenshtein, registered_domain

try:
    import whois as _whois
except ImportError:  # pragma: no cover
    _whois = None


def _brand_map() -> tuple[dict[str, list[str]], int]:
    cfg = brands_cfg()
    return cfg.get("brands", {}), int(cfg.get("max_distance", 2))


def check_display_name(from_name: str, from_domain: str) -> list[Finding]:
    """B4 — brand word in display name but sender domain isn't the brand's."""
    if not from_name or not from_domain:
        return []
    name_l = from_name.lower()
    brand_map, _ = _brand_map()
    for brand, domains in brand_map.items():
        if brand.replace("-", "") in name_l.replace("-", "") or brand in name_l:
            if from_domain not in domains:
                return [
                    Finding(
                        "B4", f"Display name impersonates '{brand}'", Severity.HIGH,
                        detail=f'"{from_name}" <...@{from_domain}> — domain is not {brand}\'s.',
                        recommendation="Classic brand-impersonation; verify via a known channel.",
                    )
                ]
    return []


def check_lookalike(domain: str) -> list[Finding]:
    """B9/B10 — typosquatting (edit distance) and punycode/homoglyph."""
    findings: list[Finding] = []
    if not domain:
        return findings

    # B10 — punycode
    if "xn--" in domain:
        findings.append(
            Finding(
                "B10", "Punycode (IDN) domain", Severity.HIGH, detail=domain,
                recommendation="Homoglyph attack risk; decode and compare to the real brand.",
            )
        )

    # B9 — typosquatting vs known brand roots
    brand_map, max_dist = _brand_map()
    core = domain.split(".")[0]
    for brand, legit_domains in brand_map.items():
        if domain in legit_domains:
            return findings  # exact legit domain, stop
        for legit in legit_domains:
            legit_core = legit.split(".")[0]
            dist = levenshtein(core, legit_core)
            if 0 < dist <= max_dist:
                findings.append(
                    Finding(
                        "B9", f"Lookalike of {legit} (distance {dist})", Severity.HIGH,
                        detail=f"{domain} is {dist} edits from {legit}.",
                        recommendation="Likely typosquatting; block the domain.",
                    )
                )
                return findings
    return findings


def check_age(domain: str, allow_network: bool) -> tuple[list[Finding], dict]:
    """B8 — domain registered recently (< threshold days)."""
    meta: dict = {}
    if not allow_network or _whois is None or not domain:
        return [], meta
    try:
        info = _whois.whois(domain)
        created = info.creation_date
        if isinstance(created, list):
            created = created[0]
        if not isinstance(created, datetime):
            return [], meta
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - created).days
        meta["domain_age_days"] = age_days
        threshold = scoring().get("email", {}).get("domain_age_days", 30)
        if age_days < threshold:
            return [
                Finding(
                    "B8", f"Domain registered {age_days} days ago", Severity.HIGH,
                    detail=f"{domain} created {created.date()} (< {threshold}d).",
                    recommendation="Newly-registered domains are a strong phishing signal.",
                )
            ], meta
    except Exception:
        return [], meta
    return [], meta


def analyse(from_name: str, from_domain: str, allow_network: bool) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    findings += check_display_name(from_name, from_domain)
    findings += check_lookalike(from_domain)
    age_findings, meta = check_age(from_domain, allow_network)
    findings += age_findings
    return findings, meta
