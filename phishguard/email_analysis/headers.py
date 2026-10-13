"""Header analysis: auth results, From/Reply-To/Return-Path, Received chain."""

from __future__ import annotations

import re

from ..models import Finding, Severity
from ..utils import registered_domain, split_address
from .parser import ParsedEmail

_IP_RE = re.compile(r"[\[(]?((?:\d{1,3}\.){3}\d{1,3})[\])]?")
_PRIVATE_PREFIXES = ("10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.",
                     "172.2", "172.30.", "172.31.", "127.", "169.254.", "::1")


def parse_auth_results(parsed: ParsedEmail) -> dict[str, str]:
    """Extract spf/dkim/dmarc verdicts from Authentication-Results headers."""
    result = {"spf": "", "dkim": "", "dmarc": ""}
    blob = " ".join(parsed.all_headers("Authentication-Results")).lower()
    blob += " " + " ".join(parsed.all_headers("ARC-Authentication-Results")).lower()
    for mech in ("spf", "dkim", "dmarc"):
        m = re.search(rf"\b{mech}=(\w+)", blob)
        if m:
            result[mech] = m.group(1)
    return result


def first_external_ip(parsed: ParsedEmail) -> str:
    """Walk Received headers bottom-up; return first public IP (the origin)."""
    received = parsed.all_headers("Received")
    for hop in reversed(received):
        for m in _IP_RE.finditer(hop):
            ip = m.group(1)
            if not ip.startswith(_PRIVATE_PREFIXES):
                return ip
    return ""


def analyse(parsed: ParsedEmail, auth: dict[str, str]) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    meta: dict = {}

    # B1 — authentication results
    for mech, label, fid in (("spf", "SPF", "B1"), ("dkim", "DKIM", "B1"), ("dmarc", "DMARC", "B1")):
        verdict = auth.get(mech, "")
        if verdict in ("fail", "softfail", "none", "permerror", "temperror"):
            sev = Severity.HIGH if verdict == "fail" and mech == "dmarc" else Severity.MEDIUM
            findings.append(
                Finding(
                    fid, f"{label} {verdict}", sev,
                    detail=f"Authentication-Results reports {mech}={verdict}.",
                    recommendation="Treat unauthenticated mail with suspicion; verify the sender.",
                )
            )

    # B3 / B4 — From vs Reply-To vs Return-Path
    from_name, from_addr = split_address(parsed.header("from"))
    _, reply_addr = split_address(parsed.header("reply-to"))
    _, return_path = split_address(parsed.header("return-path"))
    from_dom = registered_domain(from_addr)
    meta["from_name"] = from_name
    meta["from_addr"] = from_addr
    meta["from_domain"] = from_dom

    if reply_addr and registered_domain(reply_addr) != from_dom:
        findings.append(
            Finding(
                "B3", "Reply-To domain differs from From", Severity.MEDIUM,
                detail=f"From={from_addr} but Reply-To={reply_addr}.",
                recommendation="Replies would go elsewhere — common in BEC/phishing.",
            )
        )
    if return_path and registered_domain(return_path) != from_dom:
        findings.append(
            Finding(
                "B3", "Return-Path domain differs from From", Severity.LOW,
                detail=f"From={from_addr} but Return-Path={return_path}.",
                recommendation="Mismatch can indicate spoofing (note: legit ESPs also do this).",
            )
        )

    # B5 — originating IP
    ip = first_external_ip(parsed)
    meta["sender_ip"] = ip

    # B6 — Message-ID domain
    msgid = parsed.header("message-id")
    if msgid and from_dom:
        m = re.search(r"@([^>]+)>?", msgid)
        if m and registered_domain(m.group(1)) != from_dom:
            findings.append(
                Finding(
                    "B6", "Message-ID domain mismatch", Severity.LOW,
                    detail=f"Message-ID host {m.group(1)} != From domain {from_dom}.",
                    recommendation="Minor signal; weigh with other findings.",
                )
            )
    return findings, meta
