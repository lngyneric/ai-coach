#!/usr/bin/env python3
"""Minimal MDF API proxy for local development.

Implements the POST /v1/text2mdf contract expected by the gen_mdf service.
Start with: python3 mdf-proxy.py [port]
Default port: 8801
"""

import json
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler


class MDFProxyHandler(BaseHTTPRequestHandler):
    """Handle MDF API requests — implements /v1/text2mdf endpoint."""

    def _json_response(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(body, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-App-Id")
        self.end_headers()

    def do_GET(self):
        self._json_response(200, {"status": "ok", "service": "mdf-proxy"})

    def do_POST(self):
        if self.path != "/v1/text2mdf":
            self._json_response(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length > 0 else {}
        except json.JSONDecodeError:
            self._json_response(400, {"error": "invalid JSON"})
            return

        text = body.get("text", "").strip()
        language = body.get("language", "English")

        if not text:
            self._json_response(400, {"error": "text is required"})
            return

        # Wrap input text into MarkdownFlow-like structure
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        parts = []
        for i, line in enumerate(lines):
            parts.append(f"## Part {i + 1}\n\n{line}")

        content_prompt = "\n\n".join(parts)

        response = {
            "content_prompt": content_prompt,
            "request_id": "local-mdf-proxy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "input_length": len(text),
                "output_length": len(content_prompt),
                "language": language,
                "user_id": "local",
            },
        }
        self._json_response(200, response)

    def log_message(self, fmt, *args):
        print(f"[mdf-proxy] {args[0]}")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8801
    server = HTTPServer(("0.0.0.0", port), MDFProxyHandler)
    print(f"MDF proxy running on http://localhost:{port}")
    print(f"  Endpoint: POST http://localhost:{port}/v1/text2mdf")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
