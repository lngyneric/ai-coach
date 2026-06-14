#!/usr/bin/env python3
"""OpenAI-compatible chat proxy. Reads API key from env to avoid hardcoding."""
import http.server, urllib.request, json, sys, os
API_KEY = os.environ.get('OPENCODE_API_KEY') or os.environ.get('OPENAI_API_KEY', '')
if not API_KEY:
    print('FATAL: set OPENCODE_API_KEY or OPENAI_API_KEY env var', file=sys.stderr)
    sys.exit(1)
UPSTREAM = 'https://opencode.ai/zen/go/v1'
PROXY = 'http://127.0.0.1:7897'

class H(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()
    def do_POST(self):
        path = self.path.replace('/api/chat','')
        url = UPSTREAM + path
        cl = int(self.headers.get('Content-Length',0))
        body = self.rfile.read(cl)
        req = urllib.request.Request(url, data=body, method='POST')
        req.add_header('Content-Type','application/json')
        req.add_header('Authorization','Bearer '+API_KEY)
        proxy = urllib.request.ProxyHandler({'https':PROXY})
        opener = urllib.request.build_opener(proxy)
        try:
            resp = opener.open(req, timeout=120)
            self.send_response(200)
            self.send_header('Content-Type','text/event-stream')
            self.send_header('Access-Control-Allow-Origin','*')
            self.end_headers()
            while True:
                chunk = resp.read(4096)
                if not chunk: break
                self.wfile.write(chunk)
                self.wfile.flush()
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(json.dumps({'error':str(e)}).encode())
    def log_message(self, f, *a): pass

port = int(sys.argv[1]) if len(sys.argv)>1 else 18954
http.server.HTTPServer(('0.0.0.0',port), H).serve_forever()