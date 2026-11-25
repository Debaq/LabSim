"""El VEMP en una estación OSCE (core/osce.py): mismo contrato que el ABR.

- Configuración/protocolo: mandos al azar, nunca en la rutina del protocolo.
- Marcaje: registra las curvas pedidas con el músculo en la banda; la
  verdad (si hay respuesta, picos y umbral) sale del motor.
- La entrega trae panel, curvas en orden con sus marcas, y verdad.
"""
import json
import os
import random
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
REPO = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(REPO)

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from test_vemp import caso  # noqa: E402
from vemp import protocol  # noqa: E402
from vemp.VempMainWindow import VempMainWindow  # noqa: E402


def _estacion(tipo, prueba=protocol.CVEMP, curvas=(), semilla=1, umbral=100):
    v = VempMainWindow(data_login={"name": "Estación OSCE", "user": "osce"})
    v.la_super(caso(umbral_od=umbral, umbral_oi=umbral), "osce-T24-TFJ")
    v.osce_preparar(tipo, prueba, list(curvas), random.Random(semilla))
    return v


def test_sorteo_nunca_en_la_rutina():
    for semilla in range(10):
        v = _estacion("config_equipo", semilla=semilla)
        a = v.control.ajustes()
        rutina = VempMainWindow.OSCE_RUTINA[protocol.CVEMP]
        assert a.polaridad != rutina["polaridad"] and a.freq != rutina["freq"]
        assert a.filtro_alto != rutina["filtro_alto"] and a.filtro_bajo != rutina["filtro_bajo"]
        assert abs(a.tasa - rutina["tasa"]) > 0.05 and a.maniobra != rutina["maniobra"]
        assert a.subtipo == protocol.CVEMP


def test_ovemp_abre_en_ovemp():
    v = _estacion("protocolo", prueba=protocol.OVEMP)
    assert v.control.subtipo() == protocol.OVEMP


def test_marcaje_registra_y_trae_la_verdad():
    v = _estacion("marcaje", curvas=[("OD", 120), ("OD", 90), ("OI", 120)], umbral=100)
    curvas = v.osce_curvas()
    assert [(c["side"], c["int"]) for c in curvas] == [("OD", 120), ("OD", 90), ("OI", 120)], curvas
    assert all(c["emg_ok"] == "sí" and c["pol"] == "Rarefacción" for c in curvas), curvas
    verdad = v.osce_verdad()
    nombres = [c["nombre"] for c in curvas]
    assert verdad[nombres[0]]["visible"] and not verdad[nombres[1]]["visible"], verdad
    assert verdad[nombres[0]]["threshold"] == 100.0
    assert set(verdad[nombres[0]]["waves"]) == {"p13", "n23"}
    assert 10 < verdad[nombres[0]]["waves"]["p13"]["lat"] < 18


def test_entrega_serializable_con_marcas():
    v = _estacion("marcaje", curvas=[("OD", 120)])
    nombre = v.osce_curvas()[0]["nombre"]
    v._marcar(nombre, "p13", 13.2, 40.0)
    entrega = json.loads(json.dumps(v.osce_entrega()))
    assert entrega["modulo"] == "VEMP" and entrega["panel"]["subtipo"] == protocol.CVEMP
    assert entrega["curvas"][0]["marcas"]["p13"] == 13.2 and entrega["curvas"][0]["marcas"]["n23"] is None
    assert nombre in entrega["verdad"]


def test_en_la_estacion_el_registro_sale_al_instante():
    v = _estacion("protocolo", umbral=90)
    c = v.control
    c.cb_maniobra.setCurrentText("Rotación cefálica sostenida")
    c.cb_transductor.setCurrentText(protocol.AEREO)
    c.sb_int.setValue(120)
    c.sb_promedios.setValue(200)
    v.segundos_sostenido = 0.0
    v.iniciar()
    assert v.estado == "detenido" and not v.timer_captura.isActive()
    regs = list(v.sesion.registros.values())
    assert len(regs) == 1 and regs[0].terminado and regs[0].aceptados >= 200, regs


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK", flush=True)
    print("TODOS LOS TESTS PASARON", flush=True)
    os._exit(0)
