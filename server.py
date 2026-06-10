from http.server import HTTPServer, SimpleHTTPRequestHandler
import json, urllib.request, urllib.error, os

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PORT    = int(os.environ.get("PORT", 5000))

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def log_message(self, fmt, *args):
        print(f"[server] {fmt % args}")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)

        try:
            payload = json.loads(body)
            payload["model"] = "claude-sonnet-4-20250514"
            payload["max_tokens"] = 1000

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type":      "application/json",
                    "x-api-key":         API_KEY,
                    "anthropic-version": "2023-06-01",
                },
                method="POST",
            )
            with urllib.request.urlopen(req) as r:
                resp_data = r.read()

            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(resp_data)

        except urllib.error.HTTPError as e:
            err = e.read().decode()
            print(f"[error] Anthropic API: {e.code}")
            self.send_response(e.code)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(err.encode())

        except Exception as e:
            print(f"[error] {e}")
            self.send_response(500)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
    else:
        server = HTTPServer(("0.0.0.0", PORT), Handler)
        print(f"Server running on port {PORT}")
        server.serve_forever()
