"""Jinja2 HTML report generation."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..utils import defang, defang_ip

_TEMPLATE_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)
_env.filters["defang"] = defang
_env.filters["defang_ip"] = defang_ip


def render_email_html(report) -> str:
    tmpl = _env.get_template("report.html.j2")
    return tmpl.render(r=report, kind="email")


def render_dns_html(report) -> str:
    tmpl = _env.get_template("report.html.j2")
    return tmpl.render(r=report, kind="dns")


def write_html(report, path: str | Path, kind: str = "email") -> None:
    html = render_email_html(report) if kind == "email" else render_dns_html(report)
    Path(path).write_text(html, encoding="utf-8")
