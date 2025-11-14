"""Conversion utilities for supported file types."""

from __future__ import annotations

import io
import mimetypes
import zipfile
from typing import Iterable, List
from xml.etree import ElementTree as ET

from .config import get_google_api_key
from .google_vision import VisionAPIError, extract_text
from .markdown import sanitize_markdown

DOCX_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}

IMAGE_PREFIX = "image/"


class ConversionError(RuntimeError):
    """Represents an error during file conversion."""


def detect_mime_type(filename: str) -> str | None:
    """Return a MIME type based on the filename extension."""
    guessed, _ = mimetypes.guess_type(filename)
    return guessed


def convert_docx_to_markdown(data: bytes) -> str:
    """Extract text from a DOCX document and produce Markdown."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            with archive.open("word/document.xml") as document_xml:
                tree = ET.parse(document_xml)
    except (KeyError, zipfile.BadZipFile) as exc:
        raise ConversionError("Arquivo DOCX inválido ou corrompido.") from exc

    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: List[str] = []

    for paragraph in tree.findall(".//w:body/w:p", namespace):
        texts: List[str] = []
        for node in paragraph.findall(".//w:t", namespace):
            if node.text:
                texts.append(node.text)
        paragraph_text = "".join(texts).strip()
        if paragraph_text:
            paragraphs.append(paragraph_text)

    if not paragraphs:
        return "_Documento sem conteúdo legível._"

    markdown = "\n\n".join(paragraphs)
    return sanitize_markdown(markdown)


def convert_with_vision(data: bytes, mime_type: str, filename: str) -> str:
    """Use Google Vision API to convert the file into Markdown text."""
    api_key = get_google_api_key()
    if not api_key:
        raise ConversionError(
            "A chave de API do Google Vision não está configurada. "
            "Defina a variável de ambiente GOOGLE_VISION_API_KEY."
        )

    try:
        text = extract_text(data, mime_type, api_key)
    except VisionAPIError as exc:
        raise ConversionError(str(exc)) from exc

    if not text.strip():
        return f"_Nenhum texto identificado em {filename}._"

    return sanitize_markdown(text)


def convert_file(filename: str, data: bytes, mime_type: str | None) -> str:
    """Convert a file buffer to Markdown depending on its type."""
    normalized_mime = (mime_type or detect_mime_type(filename) or "").lower()

    if filename.lower().endswith(".docx") or normalized_mime in DOCX_MIME_TYPES:
        return convert_docx_to_markdown(data)

    if normalized_mime.startswith(IMAGE_PREFIX):
        return convert_with_vision(data, normalized_mime, filename)

    if filename.lower().endswith(".pdf") or normalized_mime == "application/pdf":
        return convert_with_vision(data, "application/pdf", filename)

    raise ConversionError(
        "Tipo de arquivo não suportado. Faça upload de PDFs, imagens ou documentos DOCX."
    )


def summarize_sections(sections: Iterable[str]) -> str:
    """Combine multiple markdown sections into a single document."""
    normalized: List[str] = []
    for index, section in enumerate(sections, start=1):
        content = section.strip()
        if not content:
            content = "_Sem conteúdo extraído._"
        normalized.append(f"## Documento {index}\n\n{content}")
    return "\n\n".join(normalized)
