"""Medición de tiempos en terreno (core/tiempos.py): bloqueos con su pila,
red en el hilo de la ventana, resumen por minuto."""

import json
import os
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_DATOS = tempfile.mkdtemp(prefix="labsim-tiempos-")
os.environ.setdefault("LABSIM_DATA_DIR", _DATOS)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtCore import QTimer  # noqa: E402

from core.base import context  # noqa: E402
from core import tiempos  # noqa: E402


def _esperar_bucle(ms):
    fin = time.monotonic() + ms / 1000
    while time.monotonic() < fin:
        context.app.processEvents()
        time.sleep(0.005)


def _eventos():
    tiempos._vaciar()
    with open(tiempos._archivo.name, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def _bloquea_la_ventana():
    time.sleep(0.5)


def test_ruta_sin_consulta_ni_ids():
    assert tiempos._ruta("https://x.cl/api/sync.php?since=2026&token=abc") == "/api/sync.php"
    assert tiempos._ruta("https://x.cl/api/citas/123/notas/45") == "/api/citas/:n/notas/:n"


def test_bloqueo_con_pila_y_http_en_ui():
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            time.sleep(0.2)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    assert tiempos.instalar()
    tiempos.iniciar_ui()
    _esperar_bucle(150)

    tiempos.marca("mostrar Prueba")
    QTimer.singleShot(0, _bloquea_la_ventana)
    _esperar_bucle(900)

    import requests
    requests.get(f"http://127.0.0.1:{srv.server_port}/api/citas/7?x=1", timeout=5)

    tiempos._resumen()
    ev = _eventos()
    bloqueos = [e for e in ev if e["tipo"] == "bloqueo"]
    assert bloqueos, ev
    b = max(bloqueos, key=lambda e: e["ms"])
    assert 400 <= b["ms"] <= 900, b
    assert b["tras"] == "mostrar Prueba", b
    assert any("_bloquea_la_ventana" in p["pila"] for p in b["pilas"]), b

    http = [e for e in ev if e["tipo"] == "lento" and e["nombre"].startswith("http")]
    assert http and http[0]["hilo"] == "ui" and http[0]["nombre"] == "http GET /api/citas/:n", http
    assert http[0]["estado"] == 200

    res = [e for e in ev if e["tipo"] == "resumen"][-1]
    assert "bucle: retraso" in res["metricas"] and "http en hilo ui" in res["metricas"]
    assert res["proceso"]["hilos"] >= 2
    assert next(e for e in ev if e["tipo"] == "sistema")["version"] is not None
    srv.shutdown()


if __name__ == "__main__":
    test_ruta_sin_consulta_ni_ids()
    test_bloqueo_con_pila_y_http_en_ui()
    print("ok")
