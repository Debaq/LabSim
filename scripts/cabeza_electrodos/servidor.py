"""Sirve www/ y guarda lo que la página manda por POST en out/."""
import http.server, os, sys, pathlib
BASE = pathlib.Path(__file__).parent
OUT = BASE / "out"
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(BASE / "www"), **k)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        datos = self.rfile.read(n)
        nombre = self.path.strip("/").replace("/", "_")
        (OUT / nombre).write_bytes(datos)
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a):
        pass
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
