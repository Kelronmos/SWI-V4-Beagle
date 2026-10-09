"""Minimal Beagle dashboard API — not authorization."""
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_ROOT = Path(".")


def serve(host: str, port: int, root: Path) -> None:
    global _ROOT
    _ROOT = root
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    class H(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            print(f"[beagle] {fmt % args}")

        def _json(self, code: int, obj: Any) -> None:
            data = json.dumps(obj, indent=2, default=str).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path in ("/", "/index.html"):
                html = (_ROOT / "dashboard" / "frontend" / "index.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)
                return
            if path == "/api/status":
                return self._json(200, {
                    "product": "SWI V4 Beagle",
                    "PROVEN": False,
                    "SEALED": False,
                    "AUTHORIZED": False,
                    "PRODUCTION_AUTHORIZED": False,
                    "note": "Dashboard ≠ authorization",
                })
            if path == "/api/runs":
                runs = []
                exp = _ROOT / "exports"
                if exp.exists():
                    for d in sorted(exp.iterdir(), reverse=True):
                        if d.is_dir() and d.name.startswith("RUN-"):
                            runs.append({"id": d.name})
                return self._json(200, {"runs": runs})
            self._json(404, {"error": "NOT_FOUND"})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if path == "/api/audit":
                from swi_beagle.pipeline import run_audit_pipeline

                pipe = run_audit_pipeline([_ROOT.parent], _ROOT, export=True)
                return self._json(200, {
                    "execution_id": pipe.get("execution_id"),
                    "PIPELINE_READY": (pipe.get("readiness") or {}).get("PIPELINE_READY"),
                    "AUTHORIZED": False,
                })
            if path in ("/api/rebuild",):
                return self._json(403, {
                    "error": "EXPLICIT_CONFIRMATION_REQUIRED",
                    "AUTHORIZED": False,
                    "message": "Default is AUDIT only. Rebuild is not automatic.",
                })
            self._json(404, {"error": "NOT_FOUND"})

    print(f"SWI V4 Beagle dashboard http://{host}:{port}")
    print("AUTHORIZED=NO — begin with AUDIT")
    ThreadingHTTPServer((host, port), H).serve_forever()
