from phishguard.email_analysis import urls


def test_link_text_mismatch_detected():
    html = '<a href="http://evil.xyz/login">https://bank.fr</a>'
    findings, extracted = urls.analyse("", html)
    ids = {f.id for f in findings}
    assert "B12" in ids  # text/href mismatch
    assert any("evil.xyz" in u for u in extracted)


def test_ip_url_and_risky_tld():
    text = "Visit http://185.12.3.4/login and http://promo.top/win"
    findings, _ = urls.analyse(text, "")
    ids = {f.id for f in findings}
    assert "B14" in ids  # raw IP
    assert "B15" in ids  # risky TLD


def test_clean_url_no_findings():
    findings, _ = urls.analyse("See https://github.com/notifications", "")
    assert findings == []
