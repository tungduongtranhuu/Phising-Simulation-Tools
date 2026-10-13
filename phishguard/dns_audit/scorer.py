"""Turn DNS findings into a 0-100 score and an A-F grade.

Each finding is matched to a penalty key (from config/scoring.yaml). The matched
penalty is written back onto the finding's ``points`` field (as a negative) so
reports can show the contribution of each issue.
"""

from __future__ import annotations

from ..config import dns_scoring
from ..models import DnsReport, Finding


def _penalty_key(f: Finding) -> str | None:
    t = f.title.lower()
    if f.id == "A2":
        if "no spf" in t or "multiple spf" in t:
            return "no_spf"
        if "+all" in t:
            return "spf_pass_all"
        return "spf_weak_all"  # ?all, no all, >10 lookups
    if f.id == "A3":
        if "no dmarc" in t:
            return "no_dmarc"
        if "p=none" in t:
            return "dmarc_p_none"
        return None  # missing rua / low pct: informational, no score hit
    if f.id == "A4":
        return "no_dkim"
    if f.id == "A5":
        return "no_dnssec"
    if f.id == "A6":
        return "no_caa"
    if f.id == "A7":
        return "zone_transfer_open"
    if f.id == "A8":
        return "no_mta_sts"
    if f.id == "A9":
        return "no_tls_rpt"
    if f.id == "A11":
        return "subdomain_takeover"
    return None


def score(report: DnsReport) -> DnsReport:
    cfg = dns_scoring()
    penalties = cfg.get("penalties", {})
    score_val = cfg.get("start", 100)

    for f in report.findings:
        key = _penalty_key(f)
        if key and key in penalties:
            pen = penalties[key]
            f.points = -pen
            score_val -= pen

    report.score = max(0, min(100, score_val))

    grades = cfg.get("grades", {"A": 90, "B": 75, "C": 60, "D": 40})
    for grade in ("A", "B", "C", "D"):
        if report.score >= grades.get(grade, 0):
            report.grade = grade
            break
    else:
        report.grade = "F"
    return report
