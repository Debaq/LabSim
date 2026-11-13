"""Reger: balance monoaural bifrecuencial (2026-11-13).

El alumno presenta la frecuencia conservada, cambia a mano a la patológica
y la presenta en el mismo oído; "¿El primero o el segundo?" compara las dos
últimas presentaciones con la curva de igual sonoridad del Fowler (umbral de
cada frecuencia, patrón de reclutamiento de la patológica).

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # noqa: E402,F401
from audiometria.comandos_voz import PREGUNTAS  # noqa: E402
from audiometria.response import ESTIMULO_ENCENDIDO, ResponseAudiometry  # noqa: E402

F1000, F4000 = 3, 6


class _Lbl:
    def setStyleSheet(self, _s):
        pass


class _Audio:
    lbl_response = _Lbl()


class _Sender:
    def __init__(self, name, text):
        self._n, self._t = name, text

    def objectName(self):
        return self._n

    def text(self):
        return self._t


def _r(patron="none"):
    # OD: 1 kHz conservado (10), 4 kHz patológico (40); OI normal
    tabla = [[10, 10] for _ in range(15)]
    tabla[F4000] = [40, 10]
    r = ResponseAudiometry(_Audio())
    r.set_case({"Aerea": tabla, "Osea": tabla, "Aerea_mkg": tabla, "Osea_mkg": tabla,
                "LDL": [[110, 110] for _ in range(15)],
                "Fowler": {"patterns": {str(F4000): patron}}})
    r.rol_player("reger")
    r.data["audio"].update({"test": "Umbrales", "stim": [0, 3], "output": [0, 1],
                            "trans": [0, 0], "stimOn": [False, False]})
    return r


def _presentar(r, freq, nivel):
    r.data["audio"]["freq"] = freq
    r.data["audio"]["int"] = [nivel, 0]
    r.set_config(_Sender("lbl_stimOn_ch0", ESTIMULO_ENCENDIDO))
    r.set_config(_Sender("lbl_stimOn_ch0", ""))


def _par(r, nivel_ref, nivel_pat):
    _presentar(r, F1000, nivel_ref)
    _presentar(r, F4000, nivel_pat)
    return r.respuesta_a("primero_o_segundo")


def test_es_pregunta():
    assert "primero_o_segundo" in PREGUNTAS


def test_sin_dos_presentaciones_no_sabe():
    r = _r()
    assert r.respuesta_a("primero_o_segundo") == "nose"
    _presentar(r, F1000, 30)
    assert r.respuesta_a("primero_o_segundo") == "nose"


def test_sin_reclutamiento_la_diferencia_se_mantiene():
    r = _r("none")
    assert _par(r, 30, 30) == "elprimero"     # 4 kHz a 30: bajo su umbral (40)
    assert _par(r, 30, 60) == "iguales"       # +30 dB, la diferencia de umbrales
    assert _par(r, 90, 100) == "elprimero"


def test_con_reclutamiento_completo_iguala_al_mismo_nivel():
    r = _r("complete")
    assert _par(r, 30, 60) == "iguales"       # todavía paralelas
    assert _par(r, 90, 90) == "iguales"       # al final del reclutamiento
    assert _par(r, 90, 100) == "elsegundo"


def test_el_orden_cambia_la_respuesta():
    r = _r("none")
    _presentar(r, F4000, 60)
    _presentar(r, F1000, 20)
    assert r.respuesta_a("primero_o_segundo") == "elprimero"


def test_el_pulsado_no_abre_otra_presentacion():
    r = _r("none")
    _presentar(r, F1000, 30)
    for _ in range(4):
        _presentar(r, F4000, 70)
    assert [p["freq"] for p in r._reger] == [F1000, F4000]
