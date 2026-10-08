"""Casos de referencia de la respuesta del paciente en umbrales.

labsim_backend/tests/fixtures/audiometria_paciente.json lo leen este test
(contra response.py) y labsim_backend/tests/test_audiometria_paciente.php
(contra AudiometriaPaciente, la copia en PHP que reconstruye los registros
viejos). Si response.py cambia y este test falla, hay que cambiar también
la copia en PHP y el fixture: si no, el backend reconstruye una mano que el
alumno no vio.

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""

import json
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from audiometria.response import ResponseAudiometry  # noqa: E402

FIXTURE = os.path.join(RAIZ, "labsim_backend", "tests", "fixtures", "audiometria_paciente.json")


class _Lbl:
    def setStyleSheet(self, _s):
        pass


class _Audiometro:
    lbl_response = _Lbl()


def _mano(caso, escena):
    r = ResponseAudiometry(_Audiometro())
    r.set_case({**caso, "Aerea": caso["Aerea_mkg"], "Osea": caso["Osea_mkg"]})
    est = escena["estado"]
    c = est["canales"]
    r.data["audio"].update({
        "stimOn": [c[0]["on"], c[1]["on"]], "freq": est["freq_idx"],
        "int": [c[0]["int"], c[1]["int"]], "output": [c[0]["output"], c[1]["output"]],
        "trans": [c[0]["trans"], c[1]["trans"]], "stim": [c[0]["stim"], c[1]["stim"]],
        "test": est["prueba"]})
    r.history_command = [est["instruccion"]] if est["instruccion"] is not None else []
    r.mano = escena["previa"]
    r.response_()
    return r.mano


def test_response_py_da_lo_del_fixture():
    with open(FIXTURE, encoding="utf-8") as f:
        datos = json.load(f)
    distintas = []
    for e in datos["escenas"]:
        obtenido = _mano(datos["casos"][e["caso"]], e)
        if obtenido != e["esperado"]:
            distintas.append(f"{e['nombre']}: {obtenido} (fixture {e['esperado']})")
    assert not distintas, distintas


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
