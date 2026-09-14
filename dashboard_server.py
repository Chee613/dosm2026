"""Serve the static ReefSafe dashboard with no external API dependency."""

import http.server
import sys
from functools import partial
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8088


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    handler = partial(NoCacheHandler, directory=ROOT / "dashboard")
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler) as server:
        print(f"ReefSafe dashboard: http://127.0.0.1:{PORT}")
        server.serve_forever()
