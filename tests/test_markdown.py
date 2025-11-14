"""Unit tests for markdown utilities."""

from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.converters import summarize_sections
from app.markdown import sanitize_markdown


class MarkdownUtilsTests(unittest.TestCase):
    """Validate markdown helpers."""

    def test_sanitize_markdown_normalizes_spacing(self):
        raw = "Linha 1\r\nLinha   2\tcom   espaços"
        expected = "Linha 1\nLinha 2 com espaços"
        self.assertEqual(sanitize_markdown(raw), expected)

    def test_summarize_sections_adds_headings(self):
        sections = ["Primeiro documento", "Segundo documento"]
        combined = summarize_sections(sections)
        expected = "## Documento 1\n\nPrimeiro documento\n\n## Documento 2\n\nSegundo documento"
        self.assertEqual(combined, expected)

    def test_summarize_sections_handles_empty_entries(self):
        sections = ["", "Texto"]
        combined = summarize_sections(sections)
        self.assertIn("_Sem conteúdo extraído._", combined)
        self.assertIn("Texto", combined)


if __name__ == "__main__":
    unittest.main()
