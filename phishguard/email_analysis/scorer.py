"""Weighted scoring, verdict, and MITRE ATT&CK mapping for email reports."""

from __future__ import annotations

from ..config import email_thresholds, email_weights
from ..models import EmailReport, Finding


def _weight_key(f: Finding) -> str | None:
    t = f.title.lower()
    fid = f.id
    if fid == "B1":
        if t.startswith("dmarc"):
            return "dmarc_fail"
        if t.startswith("spf"):
            return "spf_fail"
        if t.startswith("dkim"):
            return "dkim_fail"
    if fid == "B3":
        return "replyto_differs"
    if fid == "B4":
        return "display_name_spoof"
    if fid == "B8":
        return "domain_young"
    if fid in ("B9", "B10"):
        return "lookalike_domain"
    if fid == "B12":
        return "link_text_mismatch"
    if fid in ("B13", "B14"):
        return "url_ip_or_shortener"
    if fid in ("B20", "B21", "B19"):
        return "dangerous_attachment"
    if fid == "B22" and "auto-executing" in t:
        return "office_macro_autorun"
    if fid == "VT":
        return "vt_detected"
    if fid == "ABUSE":
        return "abuseipdb_high"
    if fid == "B24":
        return "pressure_keywords"
    if fid == "B25":
        return "financial_keywords"
    if fid == "B26":
        return "generic_greeting"
    return None


# finding id -> MITRE technique
_MITRE = {
    "B20": "T1566.001", "B21": "T1566.001", "B19": "T1566.001", "B22": "T1566.001",
    "B12": "T1566.002", "B13": "T1566.002", "B14": "T1566.002",
    "B16": "T1566.002", "B17": "T1566.002",
    "B8": "T1583.001", "B9": "T1583.001", "B10": "T1583.001",
}


def score(report: EmailReport) -> EmailReport:
    weights = email_weights()
    thresholds = email_thresholds()
    cap = weights.get("keyword_cap", 15)

    total = 0
    keyword_total = 0
    mitre: set[str] = set()

    for f in report.findings:
        key = _weight_key(f)
        if key:
            pts = weights.get(key, 0)
            if key in ("pressure_keywords", "financial_keywords", "generic_greeting"):
                allowed = max(0, min(pts, cap - keyword_total))
                keyword_total += allowed
                f.points = allowed
                total += allowed
            else:
                f.points = pts
                total += pts
        if f.id in _MITRE:
            mitre.add(_MITRE[f.id])

    report.score = total
    if total >= thresholds.get("phishing", 60):
        report.verdict = "phishing"
    elif total >= thresholds.get("suspicious", 30):
        report.verdict = "suspicious"
    else:
        report.verdict = "clean"
    report.mitre = sorted(mitre)
    return report
