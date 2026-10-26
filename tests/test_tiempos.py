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


def test_un_cuelgue_que_no_termina_deja_las_pilas_de_todos_los_hilos():
    """Un bloqueo se escribe al terminar; uno que no termina no se escribiría
    nunca. El vigía vuelca las pilas mientras dura."""
    tiempos.COLGADO_MS = 150
    tiempos.COLGADO_CADA_S = 0.1
    QTimer.singleShot(0, lambda: time.sleep(0.7))
    _esperar_bucle(900)
    ev = [e for e in _eventos() if e["tipo"] == "colgado"]
    assert ev, "no hubo volcado"
    assert any("lambda" in e["pilas"]["ui"] or "sleep" in e["pilas"]["ui"] or "test_tiempos" in e["pilas"]["ui"]
               for e in ev), ev[0]["pilas"]
    assert "tiempos" in ev[0]["pilas"] and ev[0]["candado_tomado"] is False


def test_faulthandler_vuelca_sin_pedir_el_gil():
    """Si el hilo de la ventana se traba del todo, el vigía de Python no
    puede ni correr: el volcado lo hace faulthandler desde C."""
    tiempos.CUELGUE_C_S = 0.4
    _esperar_bucle(700)          # el latido arma el volcado
    QTimer.singleShot(0, lambda: time.sleep(1.3))
    _esperar_bucle(1600)
    with open(tiempos._archivo_cuelgue.name, encoding="utf-8") as f:
        texto = f.read()
    assert "most recent call first" in texto and "test_tiempos.py" in texto, texto[:300]


if __name__ == "__main__":
    test_ruta_sin_consulta_ni_ids()
    test_bloqueo_con_pila_y_http_en_ui()
    test_un_cuelgue_que_no_termina_deja_las_pilas_de_todos_los_hilos()
    test_faulthandler_vuelca_sin_pedir_el_gil()
    print("ok")
