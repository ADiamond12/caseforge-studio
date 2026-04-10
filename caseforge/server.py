from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from .service import DossierService


def run_server(host: str = "127.0.0.1", port: int = 8127) -> int:
    service = DossierService()
    web_root = Path(__file__).resolve().with_name("web")
    project_root = Path(__file__).resolve().parent.parent
    outputs_root = project_root / "outputs"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlsplit(self.path)
            path = unquote(parsed.path)
            query = parse_qs(parsed.query)
            if path in {"/", "/index.html"}:
                self._serve_file(web_root / "index.html")
                return
            if path in {"/app.js", "/styles.css"}:
                self._serve_file(web_root / path.lstrip("/"))
                return
            if path == "/health":
                self._json_response({"status": "ok"})
                return
            if path == "/api/dossiers":
                limit = self._coerce_limit(query.get("limit", ["8"])[0])
                self._json_response({"items": service.list_records(limit=limit)})
                return
            if path == "/api/dossiers/compare":
                try:
                    comparison = service.compare_records(self._coerce_compare_slugs(query))
                except ValueError as exc:
                    self._json_response({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                    return
                except FileNotFoundError as exc:
                    self._json_response({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                    return
                self._json_response(comparison)
                return
            if path.startswith("/outputs/"):
                relative = path.removeprefix("/outputs/")
                self._serve_file((outputs_root / relative).resolve(), allowed_root=outputs_root.resolve())
                return
            if path.startswith("/api/dossiers/"):
                slug = path.removeprefix("/api/dossiers/").strip("/")
                try:
                    record = service.load_public_payload(slug)
                except FileNotFoundError:
                    self._json_response({"error": f"dossier not found: {slug}"}, status=HTTPStatus.NOT_FOUND)
                    return
                self._json_response(record)
                return

            self._json_response({"error": f"unknown route: {path}"}, status=HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlsplit(self.path).path)
            if path not in {"/api/dossiers", "/api/dossiers/preview"}:
                self._json_response({"error": f"unknown route: {path}"}, status=HTTPStatus.NOT_FOUND)
                return

            content_length = int(self.headers.get("Content-Length", "0") or "0")
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._json_response({"error": "invalid json payload"}, status=HTTPStatus.BAD_REQUEST)
                return

            brief = str(payload.get("brief", "")).strip()
            if not brief:
                self._json_response({"error": "`brief` is required"}, status=HTTPStatus.BAD_REQUEST)
                return

            if path == "/api/dossiers/preview":
                result = service.preview_from_payload(payload)
                self._json_response(service.preview_public_payload(result), status=HTTPStatus.OK)
                return

            result = service.generate_from_payload(payload)
            self._json_response(service.to_public_payload(result), status=HTTPStatus.CREATED)

        def log_message(self, format: str, *args: object) -> None:
            return

        def _serve_file(self, path: Path, *, allowed_root: Path | None = None) -> None:
            try:
                resolved = path.resolve(strict=True)
            except FileNotFoundError:
                self._json_response({"error": f"file not found: {path.name}"}, status=HTTPStatus.NOT_FOUND)
                return

            if allowed_root is not None and not str(resolved).startswith(str(allowed_root)):
                self._json_response({"error": "path escapes allowed root"}, status=HTTPStatus.FORBIDDEN)
                return

            content_type, _ = mimetypes.guess_type(resolved.name)
            body = resolved.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json_response(self, payload: dict[str, object], *, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        @staticmethod
        def _coerce_limit(value: str) -> int:
            try:
                parsed = int(value)
            except ValueError:
                return 8
            return min(max(parsed, 1), 30)

        @staticmethod
        def _coerce_compare_slugs(query: dict[str, list[str]]) -> list[str]:
            slugs = [value.strip() for value in query.get("slug", []) if value.strip()]
            if slugs:
                return slugs

            if not query.get("slugs"):
                return []

            return [value.strip() for value in query["slugs"][0].split(",") if value.strip()]

    server = ThreadingHTTPServer((host, port), Handler)
    try:
        print(f"CaseForge Studio running at http://{host}:{port}")
        print("Press Ctrl+C to stop.")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down CaseForge Studio.")
    finally:
        server.server_close()
    return 0
