"""Logging filter that scrubs emails and token-shaped strings.

Installed in `backend.main` on the root logger. PHI is never logged; emails
and bearer/PAT tokens are redacted to `<email>` / `<token>` so log lines
remain useful for debugging without leaking identity or credentials.
"""

from __future__ import annotations

import logging
import re

# Conservative patterns: aggressive enough to catch most leaks, narrow enough
# not to mangle ordinary log lines.
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Databricks PATs and JWTs share the dapi-/eyJ- prefix shapes; bearer tokens
# typically have base64url payloads ≥ 40 chars.
_TOKEN_RE = re.compile(r"\b(?:dapi[A-Za-z0-9-]{20,}|eyJ[A-Za-z0-9_\-./]{20,}|Bearer\s+[A-Za-z0-9_\-.~+/=]{20,})\b")


def _redact(text: str) -> str:
    text = _EMAIL_RE.sub("<email>", text)
    text = _TOKEN_RE.sub("<token>", text)
    return text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = _redact(record.msg)
            if record.args:
                record.args = tuple(
                    _redact(a) if isinstance(a, str) else a for a in record.args
                )
        except Exception:  # never let logging blow up the request
            pass
        return True


def install(level: int = logging.INFO) -> None:
    """Install the redaction filter on the root logger."""
    root = logging.getLogger()
    root.setLevel(level)
    # Idempotent — don't double-install.
    if any(isinstance(f, RedactingFilter) for f in root.filters):
        return
    root.addFilter(RedactingFilter())
    for handler in root.handlers:
        handler.addFilter(RedactingFilter())
