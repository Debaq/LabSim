"""Weber audiométrico e IWA (2026-11-13).

Con "Weber audiométrico" y el tono por vibrador, el paciente dice dónde lo
oye más fuerte; "¿Dónde lo escucha ahora?" lo pregunta en cada nivel. Un
componente conductivo lo lleva a ese oído; si no, va a la cóclea mejor hasta
que el reclutamiento del otro oído lo alcanza (IWA): completo -> al medio,
sobrerreclutamiento -> al oído con pérdida, sin reclutamiento -> sigue en el
sano.

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # noqa: E402,F401
from audiometria.comandos_voz import PREGUNTAS  # noqa: E402
from audiometria.response import ResponseAudiometry  # noqa: E402

F1000 = 3


class _Lbl:
    def setStyleSheet(self, _s):
        pass


class _Audio:
    lbl_response = _Lbl()


def _tabla(od, oi):
    return [[od, oi] for _ in range(15)]


def _r(aerea, osea, patron=None):
    r = ResponseAudiometry(_Audio())
    caso = {"Aerea": aerea, "Osea": osea, "Aerea_mkg": aerea, "Osea_mkg": osea,
            "LDL": _tabla(110, 110)}
    if patron:
        caso["Fowler"] = {"patterns": {str(F1000): patron}}
    r.set_case(caso)
    r.history_command = ["weber_audiometrico"]
    return r


def _donde(r, nivel, trans=1):
    r.data["audio"].update({"test": "Umbrales", "freq": F1000, "stimOn": [True, False],
                            "stim": [0, 3], "int": [nivel, 0], "output": [0, 1],
                            "trans": [trans, 0]})
    return r.respuesta_a("donde_lo_escucha")


def test_la_pregunta_no_cambia_la_instruccion():
    assert "donde_lo_escucha" in PREGUNTAS


def test_simetrico_al_medio_y_bajo_umbral_calla():
    r = _r(_tabla(10, 10), _tabla(10, 10))
    assert _donde(r, 30) == "almedio"
    assert _donde(r, 5) is None


def test_conductivo_va_al_oido_con_la_perdida():
    # OD conductivo (aérea 45, ósea 10), OI normal
    r = _r(_tabla(45, 10), _tabla(10, 10))
    assert _donde(r, 30) == "elderecho"


def test_sensorioneural_va_al_sano_y_sin_reclutamiento_no_se_invierte():
    # OD sensorioneural 40 dB, OI normal
    r = _r(_tabla(40, 10), _tabla(40, 10), patron="none")
    for nivel in range(40, 75, 5):
        assert _donde(r, nivel) == "elizquierdo", nivel
    assert _donde(r, 30) == "elizquierdo"   # el OD no lo oye todavía


def test_iwa_con_reclutamiento_completo_se_centra():
    r = _r(_tabla(40, 10), _tabla(40, 10), patron="complete")
    lados = [_donde(r, n) for n in range(40, 125, 5)]
    assert lados[0] == "elizquierdo"
    assert "almedio" in lados              # el punto de reclutamiento
    assert "elderecho" not in lados


def test_iwa_con_sobrerreclutamiento_pasa_al_oido_con_perdida():
    r = _r(_tabla(40, 10), _tabla(40, 10), patron="over")
    lados = [_donde(r, n) for n in range(40, 125, 5)]
    assert lados[0] == "elizquierdo"
    assert lados[-1] == "elderecho"


def test_por_fono_no_es_weber():
    r = _r(_tabla(10, 10), _tabla(10, 10))
    assert _donde(r, 30, trans=0) == "elderecho"   # el fono derecho
