from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .agent import StubLLM
from .memory import LocalMemory, NoMemory
from .run import run_arm
from .sim import make_stream

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"


def evaluate(n: int, seed: int) -> dict:
    stream = make_stream(n, seed)
    result = {}
    for name, memory in {"none": NoMemory(), "local": LocalMemory()}.items():
        rows, windows = run_arm(memory, StubLLM(), stream)
        result[name] = {
            "windows": windows,
            "n": len(rows),
            "total_auto_correct": sum(row["auto_correct"] for row in rows),
            "total_auto_wrong": sum(row["auto_wrong"] for row in rows),
            "policy_breaches": sum(row["over_limit_auto"] for row in rows),
            "rows": rows[-12:],
        }
    return {"mode": "offline", "seed": seed, "n": n, "results": result}


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json({"status": "ok", "backend": "offline-demo", "hindsight_url": "http://localhost:8888"})
            return
        if path in ("/", "/index.html"):
            self._serve_file("index.html", "text/html; charset=utf-8")
            return
        if path == "/styles.css":
            self._serve_file("styles.css", "text/css; charset=utf-8")
            return
        if path == "/app.js":
            self._serve_file("app.js", "text/javascript; charset=utf-8")
            return
        self._send_json({"detail": "Not Found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/eval":
            self._send_json({"detail": "Not Found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(size) or b"{}")
            n = max(10, min(150, int(body.get("n", 20))))
            seed = int(body.get("seed", 7))
            self._send_json(evaluate(n, seed))
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            self._send_json({"detail": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception as error:
            self._send_json({"detail": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def _serve_file(self, name: str, content_type: str) -> None:
        try:
            data = (WEB_DIR / name).read_bytes()
        except FileNotFoundError:
            self._send_json({"detail": "Frontend asset not found"}, HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args) -> None:
        print(f"[web] {format % args}")


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Precedent dashboard: http://localhost:8000", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()