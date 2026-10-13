"""Rich terminal rendering for DNS and email reports."""

from __future__ import annotations

import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..models import DnsReport, EmailReport, Severity
from ..utils import defang, defang_ip

# On Windows the default console codepage (cp1252) cannot encode characters that
# routinely appear in email (accents, arrows, defanged markers). Force UTF-8.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

console = Console()

_SEV_STYLE = {
    Severity.CRITICAL: "bold white on red",
    Severity.HIGH: "bold red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "cyan",
    Severity.INFO: "dim",
}
_VERDICT_STYLE = {"phishing": "bold white on red", "suspicious": "bold yellow", "clean": "bold green"}
_GRADE_STYLE = {"A": "bold green", "B": "green", "C": "yellow", "D": "red", "F": "bold white on red"}


def _findings_table(report) -> Table:
    t = Table(show_lines=False, expand=True)
    t.add_column("ID", width=5)
    t.add_column("Severity", width=9)
    t.add_column("Finding")
    t.add_column("Pts", justify="right", width=5)
    for f in sorted(report.findings, key=lambda x: x.points, reverse=True):
        style = _SEV_STYLE.get(f.severity, "")
        t.add_row(f.id, f"[{style}]{f.severity.value}[/]", f.title, str(f.points))
    return t


def render_dns(report: DnsReport) -> None:
    gstyle = _GRADE_STYLE.get(report.grade, "")
    console.print(
        Panel(
            f"[bold]{report.domain}[/]\nScore: [bold]{report.score}/100[/]   "
            f"Grade: [{gstyle}]{report.grade}[/]",
            title="PhishGuard · DNS Audit", border_style="blue",
        )
    )
    if report.findings:
        console.print(_findings_table(report))
        for f in report.findings:
            if f.recommendation:
                console.print(f"  [dim]→ {f.id}:[/] {f.recommendation}")
    else:
        console.print("[green]No issues found.[/]")


def render_email(report: EmailReport) -> None:
    vstyle = _VERDICT_STYLE.get(report.verdict, "")
    auth = report.auth
    console.print(
        Panel(
            f"[bold]{report.subject or '(no subject)'}[/]\n"
            f"From: {report.sender}   IP: {defang_ip(report.sender_ip) or 'n/a'}\n"
            f"Auth: spf={auth.get('spf') or '?'} dkim={auth.get('dkim') or '?'} "
            f"dmarc={auth.get('dmarc') or '?'}\n"
            f"Score: [bold]{report.score}[/]   "
            f"Verdict: [{vstyle}] {report.verdict.upper()} [/]   "
            f"MITRE: {', '.join(report.mitre) or '-'}",
            title=f"PhishGuard · Email Analysis · {report.file}", border_style="blue",
        )
    )
    if report.findings:
        console.print(_findings_table(report))

    iocs = report.iocs
    if iocs.urls or iocs.ips or iocs.hashes:
        ioc_t = Table(title="IOCs (defanged)", expand=True)
        ioc_t.add_column("Type", width=8)
        ioc_t.add_column("Value")
        for u in iocs.urls:
            ioc_t.add_row("url", defang(u))
        for ip in iocs.ips:
            ioc_t.add_row("ip", defang_ip(ip))
        for h in iocs.hashes:
            ioc_t.add_row("sha256", h)
        console.print(ioc_t)


def render_summary(reports: list[EmailReport]) -> None:
    t = Table(title="Batch summary", expand=True)
    t.add_column("File")
    t.add_column("Verdict")
    t.add_column("Score", justify="right")
    t.add_column("Sender")
    for r in reports:
        vstyle = _VERDICT_STYLE.get(r.verdict, "")
        t.add_row(r.file, f"[{vstyle}]{r.verdict}[/]", str(r.score), r.sender_domain)
    console.print(t)
    counts: dict[str, int] = {}
    for r in reports:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    console.print("  ".join(f"{k}={v}" for k, v in sorted(counts.items())))
