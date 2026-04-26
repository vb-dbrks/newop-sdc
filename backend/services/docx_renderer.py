"""Render an Approved document snapshot to .docx via python-docx.

See ADR 0009. Per-document-type Word templates live next to this file once authored.
"""


def render_docx(snapshot: dict) -> bytes:
    raise NotImplementedError("TODO: load template, fill from snapshot, return bytes")
