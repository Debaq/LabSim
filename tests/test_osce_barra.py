"""Barra de la estación OSCE con varias tareas: abre cada una con su
paciente, "Siguiente tarea" pide dos toques y no vuelve, y la entrega lleva
lo de todas en orden (null en las que no alcanzó)."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from core import hilos, osce  # noqa: E402
from core.osce_barra import BarraOsce  # noqa: E402


class Equipo:
    """Lo que main le pasa a la barra: registra qué se abrió y qué se cerró."""

    def __init__(self):
        self.abiertas = []
        self.cerradas = 0

    def abrir(self, tarea):
        self.abiertas.append(tarea)

    def entrega(self):
        t = self.abiertas[-1]
        return {"modulo": t["modulo"], "caso": t["caso"]["id"]}

    def cerrar(self):
        self.cerradas += 1


RESPUESTA = {
    "ok": True, "codigo": "ABC123", "numero": 7, "tipo": "config_equipo",
    "ventana": {"inicio_s": 0, "fin_s": 480},
    "tareas": [
        {"n": 0, "titulo": "PEATC umbral", "peso": 30.0, "modulo": "ABR", "prueba": "ABR", "curvas": [], "caso": {"id": "a"}},
        {"n": 1, "titulo": "ECochG", "peso": 25.0, "modulo": "ABR", "prueba": "ECochG", "curvas": [], "caso": {"id": "b"}},
        {"n": 2, "titulo": "cVEMP", "peso": 45.0, "modulo": "VEMP", "prueba": "CVEMP", "curvas": [], "caso": {"id": "c"}},
    ],
}


def _barra():
    osce.activo = False          # sin reloj ni pendientes contra un servidor
    osce.estacion = {"titulo": "Configuración", "osce": "OSCE", "tipo": "config_equipo"}
    eq = Equipo()
    b = BarraOsce(eq.abrir, eq.entrega, eq.cerrar)
    b._entro(dict(RESPUESTA))
    return b, eq


def test_abre_la_primera_tarea_con_su_paciente():
    b, eq = _barra()
    assert [t["caso"]["id"] for t in eq.abiertas] == ["a"], eq.abiertas
    assert eq.abiertas[0]["codigo"] == "ABC123" and eq.abiertas[0]["tipo"] == "config_equipo"
    assert "Tarea 1 de 3" in b.lbl_tarea.text() and "30 %" in b.lbl_tarea.text(), b.lbl_tarea.text()
    assert b.btn_siguiente.isVisibleTo(b)
    b.detener()


def test_siguiente_pide_dos_toques_y_abre_la_otra():
    b, eq = _barra()
    b.pedir_siguiente()
    assert len(eq.abiertas) == 1 and "No se vuelve" in b.btn_siguiente.text()
    b.pedir_siguiente()
    assert [t["caso"]["id"] for t in eq.abiertas] == ["a", "b"] and eq.cerradas == 1
    assert "Tarea 2 de 3" in b.lbl_tarea.text()
    b.siguiente()
    assert eq.abiertas[-1]["modulo"] == "VEMP"
    assert not b.btn_siguiente.isVisibleTo(b), "en la última no hay siguiente"
    b.siguiente()   # no pasa nada
    assert len(eq.abiertas) == 3
    b.detener()


def test_entrega_lleva_todas_las_tareas_en_orden():
    b, eq = _barra()
    enviado = {}
    orig = hilos.en_fondo

    def en_fondo(fn, *args, listo=None, fallo=None, **kw):
        if fn is osce.entregar:
            enviado["entrega"] = args[1]
            if listo:
                listo({"ok": True})
    hilos.en_fondo = en_fondo
    guardar, borrar = osce.guardar_pendiente, osce.borrar_pendiente
    osce.guardar_pendiente = lambda *a: None
    osce.borrar_pendiente = lambda *a: None
    try:
        b.siguiente()
        b.entregar(auto=True)
    finally:
        hilos.en_fondo = orig
        osce.guardar_pendiente, osce.borrar_pendiente = guardar, borrar
    e = enviado["entrega"]
    assert e["auto"] is True
    assert e["tareas"] == [{"modulo": "ABR", "caso": "a"}, {"modulo": "ABR", "caso": "b"}, None], e
    assert b.alumno is None and b.lbl_tarea.text() == "" and not b.btn_siguiente.isVisibleTo(b)
    b.detener()


def test_estacion_de_una_sola_tarea_como_antes():
    osce.activo = False
    osce.estacion = {"titulo": "Marcaje", "osce": "OSCE", "tipo": "marcaje"}
    eq = Equipo()
    b = BarraOsce(eq.abrir, eq.entrega, eq.cerrar)
    b._entro({"codigo": "X", "numero": 2, "tipo": "marcaje", "modulo": "ABR", "prueba": "ABR",
              "curvas": [["OD", 80]], "caso": {"id": "z"}, "ventana": {}})
    assert eq.abiertas[0]["caso"]["id"] == "z" and eq.abiertas[0]["curvas"] == [["OD", 80]]
    assert b.lbl_tarea.text() == "" and not b.btn_siguiente.isVisibleTo(b)
    b.detener()


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK", flush=True)
    print("TODOS LOS TESTS PASARON", flush=True)
    os._exit(0)
