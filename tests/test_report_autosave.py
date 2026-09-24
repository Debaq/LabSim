"""Guardado automático de los informes de examen (core/report_autosave.py).

Antes el informe se subía solo al cerrar la atención: si la app se cerraba
o el alumno atendía a otro paciente, las curvas se perdían. Acá se prueba
el mecanismo, sin red: sube lo que cambió, no resube lo mismo, y cada
subida manda su propia copia de las imágenes.
"""

import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # crea la QApplication
from core import report_autosave as ra

APP = context.app


class Modulo:
    def __init__(self):
        self.data = {"curvas": {"R1": 80}}
        self.exportes = 0
        self.dir = tempfile.mkdtemp()

    def exportar(self):
        self.exportes += 1
        ruta = os.path.join(self.dir, "0.jpg")
        with open(ruta, "wb") as f:
            f.write(b"jpg%d" % self.exportes)
        return {"0": ruta}

    def report_job(self):
        if self.data is None:
            return None
        return {"appointment_id": 42, "tipo": "ABR", "data": dict(self.data),
                "images": self.exportar}


def _con_subidas():
    subidas = []

    def subir(job, client=None):
        rutas = job.get("images_listas") or {}
        imagenes = {k: open(v, "rb").read() for k, v in rutas.items()}
        subidas.append((job["tipo"], job["data"], imagenes, dict(rutas)))
    ra.subir = subir
    return subidas


def _tick(auto, modulo=None):
    auto.guardar(modulo)
    auto.esperar()
    APP.processEvents()   # la señal de fin de la subida cruza de hilo


def test_sube_lo_que_cambio_y_no_repite():
    subidas = _con_subidas()
    m = Modulo()
    auto = ra.ReportAutosave(lambda: [m])
    auto.iniciar()
    _tick(auto)
    assert len(subidas) == 1 and subidas[0][1] == {"curvas": {"R1": 80}}
    _tick(auto)
    assert len(subidas) == 1          # nada cambió: ni se exportan imágenes
    assert m.exportes == 1
    m.data["curvas"]["R2"] = 60
    _tick(auto)
    assert len(subidas) == 2
    auto.detener()


def test_modulo_sin_nada_no_sube():
    subidas = _con_subidas()
    m = Modulo()
    m.data = None
    auto = ra.ReportAutosave(lambda: [m])
    _tick(auto)
    assert subidas == []


def test_cada_subida_lleva_su_copia_de_las_imagenes():
    subidas = _con_subidas()
    m = Modulo()
    auto = ra.ReportAutosave(lambda: [m])
    _tick(auto)
    tipo, data, imagenes, rutas = subidas[0]
    assert imagenes == {"0": b"jpg1"}
    assert rutas["0"] != os.path.join(m.dir, "0.jpg")
    assert not os.path.exists(rutas["0"])   # la copia se borra al terminar


def test_una_subida_fallida_se_reintenta():
    m = Modulo()
    intentos = []

    def falla(job, client=None):
        intentos.append(1)
        raise RuntimeError("sin red")
    ra.subir = falla
    auto = ra.ReportAutosave(lambda: [m])
    _tick(auto)
    _tick(auto)
    assert len(intentos) == 2   # no quedó marcada como subida


def test_iniciar_olvida_la_atencion_anterior():
    subidas = _con_subidas()
    m = Modulo()
    auto = ra.ReportAutosave(lambda: [m])
    _tick(auto)
    auto.iniciar()
    _tick(auto)
    assert len(subidas) == 2
    auto.detener()


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {nombre}")
            except AssertionError as exc:
                fallas += 1
                print(f"FAIL {nombre}: {exc!r}")
    sys.exit(1 if fallas else 0)
