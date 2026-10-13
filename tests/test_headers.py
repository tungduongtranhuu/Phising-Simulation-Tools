from phishguard.email_analysis.parser import ParsedEmail
from phishguard.email_analysis import headers
from phishguard.utils import split_address


def test_split_address():
    assert split_address('"PayPal Support" <a@b.xyz>') == ("PayPal Support", "a@b.xyz")
    assert split_address("plain@domain.com") == ("", "plain@domain.com")


def _email(**hdrs):
    import email
    msg = email.message.EmailMessage()
    for k, v in hdrs.items():
        msg[k.replace("_", "-")] = v
    p = ParsedEmail(path="x", msg=msg)
    p.headers = {k.lower(): str(v) for k, v in msg.items()}
    return p


def test_parse_auth_results():
    p = _email(
        Authentication_Results="mx; spf=fail; dkim=none; dmarc=fail",
    )
    auth = headers.parse_auth_results(p)
    assert auth == {"spf": "fail", "dkim": "none", "dmarc": "fail"}


def test_first_external_ip_picks_public_origin():
    p = _email()
    p.msg.add_header("Received", "from internal (10.0.0.5) by mx")
    p.msg.add_header("Received", "from evil (185.220.101.47) by relay")
    # bottom-up: the oldest hop (added first here is 'top'); public IP returned
    assert headers.first_external_ip(p) == "185.220.101.47"
