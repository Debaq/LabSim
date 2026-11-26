"""Barra de la estación OSCE: el alumno escribe su número, ve su nombre y
confirma (ahí parte su tiempo); cada caso abre con sus indicaciones y el
equipo bloqueado hasta aceptarlas; la ventanita deja ir y volver entre los
casos y al volver el caso queda como lo dejó; la entrega lleva lo de todos
en orden (null en los que no abrió) y con el tiempo cumplido se entrega sola."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from core import hilos, osce  # noqa: E402
from core.osce_barra import BarraOsce  # noqa: E402


class Equipo:
    """Lo que main le pasa a la barra: registra qué se abrió, con qué, y el bloqueo."""

    def __init__(self):
        self.abiertas = []      # (tarea, hecho)
        self.cerradas = 0
        self.bloqueado = None
        self.marca = 0          # lo "hecho" en el caso abierto

    def abrir(self, tarea, hecho=None):
        self.abiertas.append((tarea, hecho))
        self.marca = (hecho or {}).get("marca", 0)

    def entrega(self):
        t = self.abiertas[-1][0]
        return {"modulo": t["modulo"], "caso": t["caso"]["id"], "marca": self.marca}

    def cerrar(self):
        self.cerradas += 1

    def bloquear(self, si):
        self.bloqueado = si


RESPUESTA = {
    "ok": True, "codigo": "ABC123", "numero": 7, "tipo": "config_equipo",
    "ventana": {"inicio_s": 0, "fin_s": 480},
    "tareas": [
        {"n": 0, "titulo": "PEATC umbral", "peso": 30.0, "modulo": "ABR", "prueba": "ABR", "curvas": [],
         "caso": {"id": "a"}, "indicaciones": "Lactante que refiere. Busca el umbral."},
        {"n": 1, "titulo": "ECochG", "peso": 25.0, "modulo": "ABR", "prueba": "ECochG", "curvas": [], "caso": {"id": "b"}},
        {"n": 2, "titulo": "cVEMP", "peso": 45.0, "modulo": "VEMP", "prueba": "CVEMP", "curvas": [], "caso": {"id": "c"}},
    ],
}


def _barra():
    osce.activo = False          # sin reloj ni pendientes contra un servidor
    osce.estacion = {"titulo": "Configuración", "osce": "OSCE", "tipo": "config_equipo"}
    eq = Equipo()
    b = BarraOsce(eq.abrir, eq.entrega, eq.cerrar, eq.bloquear)
    b._entro(dict(RESPUESTA))
    return b, eq


def test_numero_luego_nombre_y_recien_ahi_abre():
    osce.activo = False
    osce.estacion = {"titulo": "Configuración", "osce": "OSCE", "tipo": "config_equipo", "codigo": "EST-001"}
    eq = Equipo()
    b = BarraOsce(eq.abrir, eq.entrega, eq.cerrar, eq.bloquear)
    llamadas = []
    orig = hilos.en_fondo

    def en_fondo(fn, *args, listo=None, fallo=None, **kw):
        llamadas.append(fn)
        if fn is osce.entrar:
            listo({"ok": True, "codigo": "ABC123", "numero": 7, "nombre": "Ana Pérez", "partio": False})
        elif fn is osce.confirmar:
            listo(dict(RESPUESTA))
    hilos.en_fondo = en_fondo
    try:
        b.campo.setText("7")
        b.entrar()
        assert eq.abiertas == [] and "Ana Pérez" in b.lbl_nombre.text() and b.btn_soy.isVisibleTo(b)
        assert "parte al confirmar" in b.lbl_estado.text()
        b.no_soy()
        assert b.campo.isVisibleTo(b) and not b.btn_soy.isVisibleTo(b) and b.alumno is None
        b.campo.setText("7")
        b.entrar()
        b.confirmar()
    finally:
        hilos.en_fondo = orig
    assert llamadas.count(osce.confirmar) == 1
    assert b.alumno == "ABC123" and [t["caso"]["id"] for t, _ in eq.abiertas] == ["a"]
    b.detener()


def test_indicaciones_bloquean_hasta_aceptar():
    b, eq = _barra()
    assert eq.bloqueado is True
    v = b.casos
    assert v is not None and "Caso 1 de 3" in v.lbl_caso.text() and "30 %" in v.lbl_caso.text()
    assert "Lactante" in v.txt.toPlainText() and v.btn_acepto.isVisibleTo(v)
    assert not v.btn_sig.isVisibleTo(v), "no se navega sin aceptar"
    b.aceptar_indicaciones()
    assert eq.bloqueado is False and not v.btn_acepto.isVisibleTo(v) and v.btn_sig.isVisibleTo(v)
    assert not v.btn_ant.isEnabled()
    b.detener()


def test_ir_y_volver_conserva_lo_hecho():
    b, eq = _barra()
    b.aceptar_indicaciones()
    eq.marca = 11                     # configuró algo en el caso a
    b.caso_siguiente()
    assert [t["caso"]["id"] for t, _ in eq.abiertas] == ["a", "b"] and eq.cerradas == 1
    assert eq.bloqueado is True, "caso nuevo: sus indicaciones primero"
    b.aceptar_indicaciones()
    eq.marca = 22
    b.caso_anterior()
    tarea, hecho = eq.abiertas[-1]
    assert tarea["caso"]["id"] == "a" and hecho == {"modulo": "ABR", "caso": "a", "marca": 11}
    assert eq.bloqueado is False, "indicaciones ya aceptadas: el equipo queda libre"
    b.ir_a(2)
    b.ir_a(5)       # fuera de rango: nada
    assert eq.abiertas[-1][0]["modulo"] == "VEMP" and len(eq.abiertas) == 4
    b.detener()


def test_entrega_lleva_todos_los_casos_en_orden():
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
        b.aceptar_indicaciones()
        b.caso_siguiente()
        b.entregar(auto=True)
    finally:
        hilos.en_fondo = orig
        osce.guardar_pendiente, osce.borrar_pendiente = guardar, borrar
    e = enviado["entrega"]
    assert e["auto"] is True
    assert e["tareas"] == [{"modulo": "ABR", "caso": "a", "marca": 0}, {"modulo": "ABR", "caso": "b", "marca": 0}, None], e
    assert b.alumno is None and b.campo.isVisibleTo(b) and not b.casos.isVisible()
    assert eq.bloqueado is False, "el equipo queda libre para el siguiente alumno"
    b.detener()


def test_tiempo_cumplido_entrega_sola():
    b, eq = _barra()
    enviado = []
    orig = hilos.en_fondo
    hilos.en_fondo = lambda fn, *a, **kw: enviado.append(fn)
    guardar = osce.guardar_pendiente
    osce.guardar_pendiente = lambda *a: None
    b._queda = lambda: 0.0
    try:
        b._cada_tic()
    finally:
        hilos.en_fondo = orig
        osce.guardar_pendiente = guardar
    assert osce.entregar in enviado and eq.bloqueado is True and "Se acabó el tiempo" in b.lbl_estado.text()
    b.ir_a(1)
    assert len(eq.abiertas) == 1, "con el tiempo cumplido ya no se cambia de caso"
    b.detener()


def test_estacion_de_un_solo_caso_como_antes():
    osce.activo = False
    osce.estacion = {"titulo": "Marcaje", "osce": "OSCE", "tipo": "marcaje"}
    eq = Equipo()
    b = BarraOsce(eq.abrir, eq.entrega, eq.cerrar, eq.bloquear)
    b._entro({"codigo": "X", "numero": 2, "tipo": "marcaje", "modulo": "ABR", "prueba": "ABR",
              "curvas": [["OD", 80]], "caso": {"id": "z"}, "ventana": {}})
    assert eq.abiertas[0][0]["caso"]["id"] == "z" and eq.abiertas[0][0]["curvas"] == [["OD", 80]]
    b.aceptar_indicaciones()
    assert not b.casos.btn_sig.isVisibleTo(b.casos) and "Caso 1 de 1" in b.casos.lbl_caso.text()
    b.detener()


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK", flush=True)
    print("TODOS LOS TESTS PASARON", flush=True)
    os._exit(0)
