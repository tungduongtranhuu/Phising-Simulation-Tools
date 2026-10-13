# Sample emails

- `phishing/` — synthetic (fabricated) phishing emails for testing detection.
  They contain **no** real links or payloads (the attachment is a 20-byte stub).
- `legit/` — legitimate-style emails to measure the **false-positive** rate.
  Only files named `example_*.eml` are committed; any real personal email you
  drop here is git-ignored. **Never commit real personal mail.**

Add more real-world phishing samples from public corpora (e.g. search GitHub for
`phishing_pot`) into `phishing/`. Always analyse statically — never open links
or attachments.
