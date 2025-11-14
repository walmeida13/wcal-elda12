"""Helper functions to communicate with Google Vision API via REST."""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

VISION_IMAGE_ENDPOINT = "https://vision.googleapis.com/v1/images:annotate"
VISION_FILE_ENDPOINT = "https://vision.googleapis.com/v1/files:annotate"


class VisionAPIError(RuntimeError):
    """Raised when Google Vision API returns an error response."""


def build_image_request_payload(content: bytes, mime_type: str) -> Dict[str, Any]:
    """Construct the JSON payload for Vision API image OCR."""
    encoded = base64.b64encode(content).decode("utf-8")
    return {
        "requests": [
            {
                "image": {"content": encoded},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                "imageContext": {
                    "languageHints": ["pt", "en"],
                    "mimeType": mime_type,
                },
            }
        ]
    }


def build_file_request_payload(content: bytes, mime_type: str) -> Dict[str, Any]:
    """Construct the JSON payload for Vision API file OCR (PDF/TIFF)."""
    encoded = base64.b64encode(content).decode("utf-8")
    return {
        "requests": [
            {
                "inputConfig": {"content": encoded, "mimeType": mime_type},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
            }
        ]
    }


def extract_text(content: bytes, mime_type: str, api_key: str) -> str:
    """Send the request to Google Vision and return extracted text."""
    normalized_mime = mime_type.lower()
    if normalized_mime in {"application/pdf", "image/tiff"}:
        payload = build_file_request_payload(content, normalized_mime)
        endpoint = VISION_FILE_ENDPOINT
    else:
        payload = build_image_request_payload(content, normalized_mime)
        endpoint = VISION_IMAGE_ENDPOINT

    data = json.dumps(payload).encode("utf-8")
    request = Request(
        url=f"{endpoint}?key={api_key}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=90) as response:
            body = response.read()
    except HTTPError as exc:  # pragma: no cover - network errors
        detail = exc.read().decode("utf-8", errors="ignore")
        raise VisionAPIError(f"Erro HTTP {exc.code} ao acessar Google Vision: {detail}") from exc
    except URLError as exc:  # pragma: no cover - network errors
        raise VisionAPIError(f"Não foi possível conectar ao Google Vision: {exc.reason}") from exc

    parsed: Dict[str, Any] = json.loads(body.decode("utf-8"))
    responses = parsed.get("responses", [])
    if not responses:
        raise VisionAPIError("Resposta inesperada da API do Google Vision.")

    first = responses[0]
    if "error" in first:
        error_info = first["error"].get("message", "Erro desconhecido")
        raise VisionAPIError(f"Google Vision retornou erro: {error_info}")

    annotation: Optional[Dict[str, Any]] = first.get("fullTextAnnotation")
    if annotation and annotation.get("text"):
        return annotation["text"]

    return ""
