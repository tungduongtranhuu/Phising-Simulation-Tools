"""Email analysis orchestrator (Module B)."""

from __future__ import annotations

import re
from pathlib import Path

from ..models import EmailReport, Finding, IOCs, Severity
from ..utils import registered_domain
from . import attachments, content, headers, scorer, sender, urls
from .parser import parse_file

_DKIM_SELECTOR_RE = re.compile(r"\bs=([^;]+)", re.IGNORECASE)


def analyse_file(
    path: str | Path,
    *,
    allow_network: bool = True,
    enrich=None,
    cross_check_dns: bool = True,
) -> EmailReport:
    """Analyse one .eml file and return a scored report.

    ``enrich`` is an optional callable (from phishguard.intel) that takes IOCs
    and returns extra Findings. ``allow_network`` gates WHOIS / DNS / TI.
    """
    parsed = parse_file(path)
    report = EmailReport(file=Path(path).name)
    report.subject = parsed.header("subject")

    auth = headers.parse_auth_results(parsed)
    report.auth = auth

    header_findings, hmeta = headers.analyse(parsed, auth)
    report.findings += header_findings
    report.sender = hmeta.get("from_addr", "")
    report.sender_domain = hmeta.get("from_domain", "")
    report.sender_ip = hmeta.get("sender_ip", "")

    # Sender domain analysis
    sender_findings, _ = sender.analyse(
        hmeta.get("from_name", ""), report.sender_domain, allow_network
    )
    report.findings += sender_findings

    # URLs
    url_findings, found_urls = urls.analyse(parsed.text, parsed.html)
    report.findings += url_findings

    # Attachments
    att_findings, hashes = attachments.analyse(parsed.attachments, parsed.text)
    report.findings += att_findings

    # Content keywords
    report.findings += content.analyse(report.subject, parsed.text, parsed.html)

    # B7 — cross-check sender domain DNS posture (missing DMARC = easy to spoof)
    if cross_check_dns and allow_network and report.sender_domain:
        report.findings += _dns_cross_check(report.sender_domain, parsed)

    # Collect IOCs (stored raw; output layers defang them)
    url_domains = sorted({registered_domain(u) for u in found_urls if registered_domain(u)})
    report.iocs = IOCs(
        urls=found_urls,
        ips=[report.sender_ip] if report.sender_ip else [],
        domains=url_domains,
        hashes=hashes,
    )

    # Threat-intel enrichment (optional, networked, cached)
    if enrich is not None and allow_network:
        try:
            report.findings += enrich(report.iocs)
        except Exception:
            pass

    return scorer.score(report)


def _dns_cross_check(domain: str, parsed) -> list[Finding]:
    from ..dns_audit import audit  # local import avoids import cost when unused

    selectors = []
    for sig in parsed.all_headers("DKIM-Signature"):
        m = _DKIM_SELECTOR_RE.search(sig)
        if m:
            selectors.append(m.group(1).strip())

    dns_report = audit(
        domain, allow_network=False, do_zone_transfer=False,
        do_takeover=False, dkim_selectors=selectors,
    )
    findings: list[Finding] = []
    has_dmarc = bool(dns_report.records.get("dmarc"))
    if not has_dmarc:
        findings.append(
            Finding(
                "B7", "Sender domain has no DMARC", Severity.MEDIUM,
                detail=f"{domain} publishes no DMARC record — trivially spoofable.",
                recommendation="Low trust in the From address; corroborate via other signals.",
            )
        )
    return findings
