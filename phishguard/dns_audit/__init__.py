"""DNS security audit orchestrator (Module A)."""

from __future__ import annotations

from ..models import DnsReport
from ..utils import registered_domain
from . import dkim, dmarc, dnssec, records, scorer, spf, takeover, zone_transfer
from .resolver import HAVE_DNS


def audit(
    domain: str,
    *,
    allow_network: bool = True,
    do_zone_transfer: bool = True,
    do_takeover: bool = True,
    dkim_selectors: list[str] | None = None,
) -> DnsReport:
    """Run all DNS checks for ``domain`` and return a scored report.

    ``allow_network`` governs outbound HTTP (MTA-STS fetch, crt.sh). DNS queries
    always run when dnspython is available.
    """
    domain = registered_domain(domain) or domain.strip().lower()
    report = DnsReport(domain=domain)

    if not HAVE_DNS:
        report.records["error"] = "dnspython not installed; run: pip install dnspython"
        return scorer.score(report)

    rec = report.records
    report.findings += spf.check(domain, rec)
    report.findings += dmarc.check(domain, rec)
    report.findings += dkim.check(domain, rec, extra_selectors=dkim_selectors)
    report.findings += dnssec.check(domain, rec)
    report.findings += records.check(domain, rec, allow_network=allow_network)
    report.findings += zone_transfer.check(domain, rec, enabled=do_zone_transfer)
    report.findings += takeover.check(domain, rec, enabled=do_takeover and allow_network)

    return scorer.score(report)
