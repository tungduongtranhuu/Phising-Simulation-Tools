"""MX, NS, CAA, MTA-STS, TLS-RPT checks (A1, A6, A8, A9, A10)."""

from __future__ import annotations

from ..models import Finding, Severity
from . import resolver

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]


def check(domain: str, records: dict, allow_network: bool = True) -> list[Finding]:
    findings: list[Finding] = []

    # A1 — MX
    mx = resolver.mx(domain)
    records["mx"] = list(mx)
    if not mx:
        findings.append(
            Finding(
                "A1", "No MX record", Severity.INFO,
                detail=f"{domain} has no MX; it should not send/receive mail.",
                recommendation="If this domain sends mail, add MX and an SPF -all; otherwise fine.",
            )
        )

    # A10 — Name servers
    ns = resolver.nameservers(domain)
    records["ns"] = list(ns)
    if len(ns) == 1:
        findings.append(
            Finding(
                "A10", "Only one name server", Severity.LOW, detail=ns[0],
                recommendation="Use >=2 name servers, ideally on diverse networks, for resilience.",
            )
        )

    # A6 — CAA
    caa = resolver.query(domain, "CAA")
    records["caa"] = list(caa)
    if not caa:
        findings.append(
            Finding(
                "A6", "No CAA record", Severity.LOW,
                detail="Any CA may issue certificates for this domain.",
                recommendation='Add a CAA record, e.g. 0 issue "letsencrypt.org".',
            )
        )

    # A8 — MTA-STS
    mta_txt = resolver.txt(f"_mta-sts.{domain}")
    policy_mode = None
    if allow_network and requests is not None and mta_txt:
        try:
            r = requests.get(
                f"https://mta-sts.{domain}/.well-known/mta-sts.txt", timeout=5,
            )
            if r.ok:
                for line in r.text.splitlines():
                    if line.lower().startswith("mode:"):
                        policy_mode = line.split(":", 1)[1].strip().lower()
        except Exception:
            pass
    records["mta_sts"] = {"txt": list(mta_txt), "mode": policy_mode}
    if not mta_txt:
        findings.append(
            Finding(
                "A8", "No MTA-STS policy", Severity.LOW,
                detail="No _mta-sts TXT record; downgrade attacks on inbound TLS are possible.",
                recommendation="Publish an MTA-STS policy in enforce mode.",
            )
        )
    elif policy_mode == "testing":
        findings.append(
            Finding(
                "A8", "MTA-STS in testing mode", Severity.LOW,
                detail="Policy mode is 'testing'; it is not enforced.",
                recommendation="Switch MTA-STS mode to 'enforce'.",
            )
        )

    # A9 — TLS-RPT
    tlsrpt = resolver.txt(f"_smtp._tls.{domain}")
    records["tls_rpt"] = list(tlsrpt)
    if not tlsrpt:
        findings.append(
            Finding(
                "A9", "No TLS-RPT record", Severity.LOW,
                detail="No _smtp._tls TXT record; you receive no SMTP TLS failure reports.",
                recommendation='Add TLS-RPT, e.g. "v=TLSRPTv1; rua=mailto:tlsrpt@yourdomain".',
            )
        )
    return findings
