# PhishGuard

**Static phishing-email analysis & DNS security audit — a defensive (blue-team) CLI.**

PhishGuard answers two questions a SOC analyst and a mail admin ask every day:

1. **Is this `.eml` a phishing email?** — it parses the message statically, checks
   SPF/DKIM/DMARC results, From/Reply-To/Return-Path consistency, the `Received`
   chain, lookalike/young sender domains, URLs, attachments and content, extracts
   and enriches IOCs, then scores the message and maps it to MITRE ATT&CK.
2. **Is this domain configured to resist email spoofing and DNS attacks?** — it
   audits SPF, DMARC, DKIM, DNSSEC, CAA, MX/NS, MTA-STS, TLS-RPT, open zone
   transfers and dangling-CNAME subdomain takeover, and grades it A–F.

> **It is defensive and static by design.** PhishGuard never sends email, never
> opens a link, and never executes an attachment. It is not a phishing-campaign
> tool. See [Safety & ethics](#safety--ethics).

## Architecture

```
  example.com ─▶ ┌─────────────┐ ◀─ suspicious.eml
                 │  CLI (typer)│
                 └──────┬──────┘
         ┌──────────────┴──────────────┐
         ▼                             ▼
  Module A: DNS Audit          Module B: Email Analysis
  SPF/DMARC/DKIM/DNSSEC         parser ▸ headers ▸ sender
  CAA/MX/NS/MTA-STS/TLS-RPT     urls ▸ attachments ▸ content
  zone transfer ▸ takeover              │
         │                     Threat-intel enrichment
         │                     (VirusTotal / AbuseIPDB / URLhaus)
         └───────────┬──────────────────┘
                     ▼
         Scoring ▸ verdict ▸ MITRE ATT&CK
   ┌─────────┬──────────┬───────────┬──────────────┐
   Terminal  JSON       HTML        alerts.json ─▶ Wazuh
```

## Install

```bash
python -m pip install -r requirements.txt       # core features
# optional deep-inspection libs (DKIM verify, WHOIS, file-type, macros):
python -m pip install -e ".[full]"
cp .env.example .env                             # add free API keys (optional)
```

Core features work with no API keys and with `--offline`. Optional libraries
(`dkimpy`, `python-whois`, `python-magic`, `oletools`) enable extra checks; when
they are absent those checks are skipped, not failed.

## Usage

```bash
# DNS audit
python -m phishguard dns example.com
python -m phishguard dns example.com --format json -o report.json
python -m phishguard dns zonetransfer.me        # learning domain with open AXFR

# Email analysis
python -m phishguard email samples/phishing/paypal_lookalike.eml
python -m phishguard email samples/phishing/paypal_lookalike.eml --html report.html --siem
python -m phishguard email samples/ --summary   # batch a folder
python -m phishguard email sample.eml --offline # no WHOIS/DNS/TI calls
```

(After `pip install -e .` the shorter `phishguard ...` command also works.)

## Checks

**DNS audit (Module A):** MX · SPF (`+all`, `?all`, >10 lookups, multiples) ·
DMARC (`p=none`, missing `rua`, `pct<100`) · DKIM (common selectors, weak keys) ·
DNSSEC · CAA · open zone transfer (AXFR) · MTA-STS · TLS-RPT · name-server
diversity · subdomain takeover (crt.sh + dangling CNAME).

**Email analysis (Module B):** auth results · DKIM re-verify · From/Reply-To/
Return-Path · display-name spoofing · `Received` chain / origin IP · Message-ID ·
sender-domain DNS cross-check · domain age · typosquatting · punycode · link-text
vs href · IP/shortener URLs · risky TLDs · credential keywords · HTML forms ·
attachment hashing · real file type · dangerous & double extensions · Office
macros · password-protected archives · urgency/financial/greeting keywords.

## Scoring

- **Email:** findings add up. `0–29 clean`, `30–59 suspicious`, `≥60 phishing`.
- **DNS:** starts at 100, penalties subtract. `A≥90 · B≥75 · C≥60 · D≥40 · F<40`.

Weights, keywords, brands and risky TLDs live in `config/*.yaml` — tune without
touching code.

## MITRE ATT&CK

`T1566.001` Spearphishing Attachment · `T1566.002` Spearphishing Link ·
`T1583.001` Acquire Infrastructure: Domains.

## SIEM (Wazuh)

`--siem` appends one compact JSON line per result to `alerts.json`
(`/var/log/phishguard/alerts.json` on Linux; `logs/alerts.json` on Windows dev).
Wire it up with the files in [`wazuh/`](wazuh/): add `ossec_localfile.xml` to the
agent's `ossec.conf` and `local_rules.xml` to the manager, then validate with
`wazuh-logtest`.

## Evaluation (false-positive tracking)

Always test against **legitimate** mail too, so you can report a false-positive
rate (a question interviewers love).

| Dataset  | Emails | Correct | False positive | False negative |
|----------|--------|---------|----------------|----------------|
| Phishing | …      | …       | –              | …              |
| Legit    | …      | –       | …              | –              |

Fill this in after running the tool over your sample corpus.

## Tests

```bash
python -m pytest -q
```

## Safety & ethics

- Static analysis only; work inside a VM when handling live samples.
- Never open links or attachments from analysed email.
- Only send **hashes** to VirusTotal — never upload files.
- All IOCs in reports are **defanged** (`hxxp`, `[.]`).
- Only run zone-transfer / subdomain scans against domains you own or are
  authorised to test (e.g. `zonetransfer.me`).
- Never commit API keys (`.env` is git-ignored) or real personal email.

## Roadmap

IMAP ingestion of a reporting mailbox · QR-code (quishing) detection · small
FastAPI UI · STIX/MISP export · Sigma rules.

## License

MIT
