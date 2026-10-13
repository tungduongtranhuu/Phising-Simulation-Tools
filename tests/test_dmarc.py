from phishguard.dns_audit import dmarc


def test_parse_tags():
    tags = dmarc.parse("v=DMARC1; p=quarantine; rua=mailto:a@b.com; pct=50")
    assert tags["v"] == "DMARC1"
    assert tags["p"] == "quarantine"
    assert tags["rua"] == "mailto:a@b.com"
    assert tags["pct"] == "50"


def test_parse_ignores_blanks():
    tags = dmarc.parse("v=DMARC1;p=reject;")
    assert tags["p"] == "reject"
    assert "v" in tags
