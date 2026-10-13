import re

from phishguard.dns_audit import spf


def test_all_mechanism_regex():
    assert re.search(r"([~\-+?])all\b", "v=spf1 include:_spf.google.com -all").group(1) == "-"
    assert re.search(r"([~\-+?])all\b", "v=spf1 +all").group(1) == "+"
    assert re.search(r"([~\-+?])all\b", "v=spf1 ?all").group(1) == "?"


def test_count_lookups_counts_mechanisms(monkeypatch):
    # No recursion into includes (stub record lookups to empty).
    monkeypatch.setattr(spf, "_spf_records", lambda d: [])
    record = "v=spf1 include:a.com include:b.com a mx -all"
    # include x2 + a + mx = 4 top-level lookups
    assert spf._count_lookups(record, "x.com") == 4
