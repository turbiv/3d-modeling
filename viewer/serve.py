"""Local CAD viewer server (stdlib only, localhost only).

Serves viewer/index.html, printer.json, and out/<part>/ exports.
/api/parts lists exported parts, newest first, so the page can follow edits live.
Usage: python viewer/serve.py [port]   (default 3940)
"""

import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
OUT = (ROOT / "out").resolve()
INDEX = ROOT / "viewer" / "index.html"
PRINTER = ROOT / "printer.json"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_bytes(self, data: bytes, ctype: str):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path in ("/", "/index.html"):
            return self.send_bytes(INDEX.read_bytes(), "text/html; charset=utf-8")
        if path == "/api/printer":
            return self.send_bytes(PRINTER.read_bytes(), "application/json")
        if path == "/api/parts":
            parts = []
            if OUT.is_dir():
                for d in OUT.iterdir():
                    stl = d / f"{d.name}.stl"
                    if stl.is_file():
                        parts.append({"name": d.name, "mtime": stl.stat().st_mtime})
            parts.sort(key=lambda p: p["mtime"], reverse=True)
            return self.send_bytes(json.dumps(parts).encode(), "application/json")
        if path.startswith("/out/"):
            f = (ROOT / path.lstrip("/")).resolve()
            if f.is_file() and OUT in f.parents:
                ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
                return self.send_bytes(f.read_bytes(), ctype)
        self.send_error(404)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3940
    print(f"CAD viewer on http://localhost:{port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
