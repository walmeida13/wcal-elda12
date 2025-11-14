"""HTTP server that exposes OCR to Markdown conversion endpoints."""

from __future__ import annotations

import json
import os
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from io import BytesIO
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

from .config import get_google_api_key, load_env
from .converters import ConversionError, convert_file, summarize_sections

load_env()

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = ROOT / "public"


class OCRRequestHandler(SimpleHTTPRequestHandler):
    """Serve static assets and handle OCR conversion requests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def log_message(self, format: str, *args):  # noqa: A003 - keep signature
        """Prefix log messages with timestamp."""
        timestamp = time.strftime("[%d/%b/%Y %H:%M:%S]")
        message = f"{timestamp} {self.address_string()} - " + format % args
        print(message)

    def do_OPTIONS(self):  # noqa: N802 - inherited signature
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):  # noqa: N802 - inherited signature
        parsed_path = urlparse(self.path)
        if parsed_path.path != "/api/process":
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint não encontrado")
            return

        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            self.send_error(HTTPStatus.BAD_REQUEST, "Conteúdo deve ser multipart/form-data")
            return

        boundary_token = "boundary="
        if boundary_token not in content_type:
            self.send_error(HTTPStatus.BAD_REQUEST, "Boundary do formulário não localizado")
            return

        boundary = content_type.split(boundary_token, 1)[1]
        boundary_bytes = ("--" + boundary).encode("utf-8")
        remainbytes = int(self.headers.get("Content-Length", 0))

        files: List[Dict[str, bytes]] = []

        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary_bytes not in line:
                break
            disposition_line = self.rfile.readline()
            remainbytes -= len(disposition_line)
            if b"filename=" not in disposition_line:
                self._discard_part(remainbytes, boundary_bytes)
                continue
            filename = self._extract_filename(disposition_line)
            content_type_line = self.rfile.readline()
            remainbytes -= len(content_type_line)
            file_mime = self._extract_mime(content_type_line)
            blank = self.rfile.readline()
            remainbytes -= len(blank)
            file_data = self._read_to_boundary(remainbytes, boundary_bytes)
            remainbytes -= len(file_data)
            files.append({"filename": filename, "mime": file_mime, "data": file_data})
            # consume trailing CRLF after data
            tail = self.rfile.readline()
            remainbytes -= len(tail)
            if remainbytes <= 0:
                break

        if not files:
            self.send_error(HTTPStatus.BAD_REQUEST, "Nenhum arquivo enviado")
            return

        responses: List[str] = []
        for file_info in files:
            try:
                result = convert_file(
                    file_info["filename"], file_info["data"], file_info["mime"]
                )
            except ConversionError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            responses.append(result)

        combined = summarize_sections(responses)
        file_name = f"documento-unificado-{int(time.time())}.md"
        payload = {"markdown": combined, "fileName": file_name}
        self._send_json(HTTPStatus.OK, payload)

    # Helpers -----------------------------------------------------------------

    def _send_json(self, status: HTTPStatus, payload: Dict[str, str]):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _extract_filename(self, disposition_line: bytes) -> str:
        parts = disposition_line.decode("utf-8", errors="ignore").split(";")
        for part in parts:
            part = part.strip()
            if part.startswith("filename="):
                filename = part.split("=", 1)[1].strip('"')
                return os.path.basename(filename)
        return f"arquivo-{int(time.time())}"

    def _extract_mime(self, content_type_line: bytes) -> str:
        decoded = content_type_line.decode("utf-8", errors="ignore").strip()
        if ":" in decoded:
            return decoded.split(":", 1)[1].strip()
        return ""

    def _read_to_boundary(self, remainbytes: int, boundary: bytes) -> bytes:
        buffer = BytesIO()
        while remainbytes > 0:
            line = self.rfile.readline()
            if not line:
                break
            remainbytes -= len(line)
            if line.startswith(boundary):
                break
            if boundary in line:
                index = line.index(boundary)
                buffer.write(line[:index])
                break
            buffer.write(line)

        data = buffer.getvalue()
        if data.endswith(b"\r\n"):
            data = data[:-2]
        return data

    def _discard_part(self, remainbytes: int, boundary: bytes) -> None:
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                break


def run_server(port: int = 8000) -> None:
    from http.server import HTTPServer

    handler = OCRRequestHandler
    httpd = HTTPServer(("0.0.0.0", port), handler)
    print(f"Servidor iniciado em http://0.0.0.0:{port}")
    if not get_google_api_key():
        print("Aviso: GOOGLE_VISION_API_KEY não está definida. Uploads PDF/imagem falharão.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Encerrando servidor...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    run_server(port)
