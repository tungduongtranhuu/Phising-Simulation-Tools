"""Thin wrapper over dnspython with safe timeouts and simple helpers."""

from __future__ import annotations

from functools import lru_cache

try:
    import dns.resolver
    import dns.exception
    HAVE_DNS = True
except ImportError:  # pragma: no cover
    HAVE_DNS = False

DEFAULT_TIMEOUT = 5.0


def _make_resolver():
    r = dns.resolver.Resolver()
    r.timeout = DEFAULT_TIMEOUT
    r.lifetime = DEFAULT_TIMEOUT
    return r


@lru_cache(maxsize=256)
def query(name: str, rdtype: str) -> tuple[str, ...]:
    """Return record strings for ``name``/``rdtype``. Empty tuple on any miss.

    TXT records are returned as the concatenated, unquoted string.
    """
    if not HAVE_DNS or not name:
        return ()
    try:
        answers = _make_resolver().resolve(name, rdtype)
    except Exception:
        return ()
    out: list[str] = []
    for rdata in answers:
        if rdtype == "TXT":
            try:
                out.append(b"".join(rdata.strings).decode("utf-8", "replace"))
            except Exception:
                out.append(rdata.to_text().strip('"'))
        else:
            out.append(rdata.to_text())
    return tuple(out)


def txt(name: str) -> tuple[str, ...]:
    return query(name, "TXT")


def nameservers(domain: str) -> tuple[str, ...]:
    return tuple(ns.rstrip(".") for ns in query(domain, "NS"))


def mx(domain: str) -> tuple[str, ...]:
    return query(domain, "MX")
