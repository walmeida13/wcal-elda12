"""Utilities for Markdown sanitization."""

from __future__ import annotations

import re

WHITESPACE_RE = re.compile(r"[ \t]+")


def sanitize_markdown(text: str) -> str:
    """Normalize whitespace and line endings for Markdown output."""
    if not text:
        return ""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = WHITESPACE_RE.sub(" ", normalized)
    normalized_lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(normalized_lines).strip()
