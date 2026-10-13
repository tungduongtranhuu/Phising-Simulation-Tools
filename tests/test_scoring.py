from phishguard.models import DnsReport, EmailReport, Finding, Severity
from phishguard.email_analysis import scorer as email_scorer
from phishguard.dns_audit import scorer as dns_scorer
from phishguard.email_analysis import sender


def test_email_verdict_phishing():
    r = EmailReport()
    r.findings = [
        Finding("B1", "DMARC fail", Severity.HIGH),
        Finding("B9", "Lookalike of paypal.com (distance 1)", Severity.HIGH),
        Finding("B12", "Link text differs from destination", Severity.HIGH),
    ]
    email_scorer.score(r)
    assert r.score >= 60
    assert r.verdict == "phishing"
    assert "T1566.002" in r.mitre and "T1583.001" in r.mitre


def test_email_keyword_cap():
    r = EmailReport()
    r.findings = [
        Finding("B24", "Pressure", Severity.LOW),
        Finding("B25", "Financial", Severity.LOW),
        Finding("B26", "Generic greeting", Severity.INFO),
    ]
    email_scorer.score(r)
    assert r.score <= 15  # keyword groups capped


def test_dns_grade_from_penalties():
    r = DnsReport(domain="x.com")
    r.findings = [
        Finding("A2", "No SPF record", Severity.HIGH),
        Finding("A3", "No DMARC record", Severity.HIGH),
    ]
    dns_scorer.score(r)
    assert r.score == 50  # 100 - 25 - 25
    assert r.grade == "D"


def test_lookalike_detection():
    findings = sender.check_lookalike("paypa1.com")
    assert any(f.id == "B9" for f in findings)
    assert sender.check_lookalike("github.com") == []  # not in brand list -> no FP
