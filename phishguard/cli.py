"""PhishGuard command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from . import __version__

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # pragma: no cover
    pass

app = typer.Typer(
    add_completion=False,
    help="PhishGuard — static phishing email analysis & DNS security audit (defensive).",
    no_args_is_help=True,
)


def _version_cb(value: bool):
    if value:
        typer.echo(f"PhishGuard {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", callback=_version_cb, is_eager=True, help="Show version and exit."
    ),
):
    """Defensive tooling only: PhishGuard never sends mail, opens links, or runs files."""


@app.command()
def dns(
    domain: str = typer.Argument(..., help="Domain to audit, e.g. example.com"),
    fmt: str = typer.Option("console", "--format", "-f", help="console | json"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Write output to file"),
    offline: bool = typer.Option(False, "--offline", help="No outbound HTTP (MTA-STS, crt.sh)"),
    no_zone_transfer: bool = typer.Option(
        False, "--no-zone-transfer", help="Skip AXFR test (only test domains you may test)"
    ),
    no_takeover: bool = typer.Option(False, "--no-takeover", help="Skip subdomain-takeover scan"),
    html: Optional[Path] = typer.Option(None, "--html", help="Write an HTML report to this path"),
    siem: bool = typer.Option(False, "--siem", help="Append a compact alert line for Wazuh"),
):
    """Audit a domain's email/DNS security posture (SPF, DMARC, DKIM, DNSSEC, ...)."""
    from .dns_audit import audit
    from .output import console, html_report, json_out, siem as siem_out

    report = audit(
        domain,
        allow_network=not offline,
        do_zone_transfer=not no_zone_transfer,
        do_takeover=not no_takeover,
    )

    if fmt == "json":
        text = json_out.to_json(report)
        if output:
            output.write_text(text, encoding="utf-8")
            console.console.print(f"[green]Wrote[/] {output}")
        else:
            typer.echo(text)
    else:
        console.render_dns(report)
        if output:
            output.write_text(json_out.to_json(report), encoding="utf-8")

    if html:
        html_report.write_html(report, html, kind="dns")
        console.console.print(f"[green]HTML report:[/] {html}")
    if siem:
        path = siem_out.emit(report)
        console.console.print(f"[green]SIEM line appended:[/] {path}")


@app.command("email")
def email_cmd(
    target: Path = typer.Argument(..., help="A .eml file, or a directory of .eml files"),
    fmt: str = typer.Option("console", "--format", "-f", help="console | json"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Write JSON to this file"),
    html: Optional[Path] = typer.Option(None, "--html", help="Write an HTML report (single file)"),
    siem: bool = typer.Option(False, "--siem", help="Append a compact alert line for Wazuh"),
    offline: bool = typer.Option(False, "--offline", help="No WHOIS / DNS / threat-intel calls"),
    summary: bool = typer.Option(False, "--summary", help="Batch mode: print a summary table"),
):
    """Analyse one .eml file (or a folder) for phishing indicators."""
    from .email_analysis import analyse_file
    from .intel import build_enricher
    from .output import console, html_report, json_out, siem as siem_out

    enrich = build_enricher(offline=offline)

    files: list[Path]
    if target.is_dir():
        files = sorted(target.rglob("*.eml"))
        if not files:
            console.console.print(f"[yellow]No .eml files found in {target}[/]")
            raise typer.Exit(1)
    else:
        files = [target]

    reports = []
    for f in files:
        try:
            report = analyse_file(f, allow_network=not offline, enrich=enrich)
        except Exception as exc:  # keep batch going
            console.console.print(f"[red]Failed on {f}: {exc}[/]")
            continue
        reports.append(report)

        if not summary and fmt == "console":
            console.render_email(report)
        elif not summary and fmt == "json":
            typer.echo(json_out.to_json(report))

        if siem:
            siem_out.emit(report)

    if summary:
        console.render_summary(reports)

    if output and reports:
        import json as _json
        payload = [r.to_dict() for r in reports] if len(reports) > 1 else reports[0].to_dict()
        output.write_text(_json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        console.console.print(f"[green]Wrote[/] {output}")

    if html and reports:
        html_report.write_html(reports[0], html, kind="email")
        console.console.print(f"[green]HTML report:[/] {html}")


if __name__ == "__main__":
    app()
