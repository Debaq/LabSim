"""Registro del audiómetro para leer el examen desde el backend (v2).

Cada estímulo tiene que traer la foto del equipo con los dos canales (el
ruido del otro canal antes había que adivinarlo), y la mano del paciente
tiene que quedar registrada cuando cambia: es lo que vio el alumno.

core.base crea un QApplication al importarse -> QT_QPA_PLATFORM=offscreen.
"""

import os
import re
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # noqa: E402,F401  (crea el QApplication)
import audiometria.Audiometer as modulo  # noqa: E402


def pad(filas):
    return filas + [filas[-1]] * (15 - len(filas))


def caso_anacusia_od():
    """OD anacúsico, OI normal: sin enmascarar, el OD responde por sombra."""
    return {
        "id": 9, "gender": 1, "edad": 24, "sector": "Camara_sono",
        "Aerea": pad([[90, 5]] * 9), "Osea": pad([[90, 5]] * 9),
        "Aerea_mkg": pad([[90, 5]] * 9), "Osea_mkg": pad([[90, 5]] * 9),
        "LDL": pad([[120, 100]] * 9),
        "UMD": [{"int": 110, "percentage": 0},
                {"int": 40, "percentage": 100}],
        "SDT": [90, 5], "SRT": [90, 5], "recruit": [False, False],
        "Z_OD": "A", "Z_OI": "A",
    }


class _Cola:
    def __init__(self):
        self.eventos = []

    def push(self, action, payload=None):
        self.eventos.append((action, payload))

    def de(self, action):
        return [p for a, p in self.eventos if a == action]


def _audiometro():
    cola = _Cola()
    original = modulo.get_log_queue
    modulo.get_log_queue = lambda: cola
    try:
        a = modulo.Audiometer(caso_anacusia_od())
    finally:
        modulo.get_log_queue = original
    return a, cola


def test_el_caso_cargado_queda_con_la_foto_del_equipo():
    _a, cola = _audiometro()
    cargado = cola.de("audio_caso_cargado")
    assert len(cargado) == 1
    estado = cargado[0]["estado"]
    assert len(estado["canales"]) == 2
    assert cargado[0]["v"] == 2 and cargado[0]["case_id"] == 9


def test_cada_estimulo_trae_los_dos_canales():
    a, cola = _audiometro()
    a.Helper_Stim(0, play=True)
    a.Helper_Stim(0, play=False)
    pulsos = cola.de("audio_stim_button")
    assert [p["play"] for p in pulsos] == [True, False]
    for p in pulsos:
        canales = p["estado"]["canales"]
        assert len(canales) == 2
        assert set(canales[1]) >= {"on", "intensity", "stim", "output", "trans"}
        assert p["estado"]["prueba"] == a.lbl_prueba.text()


def test_la_mano_del_paciente_queda_registrada():
    a, cola = _audiometro()
    a.lbl_output[0].setText("Derecha")
    a.lbl_trans[0].setText(modulo.trans_list[0])
    a.supra("colocar_fonos")
    a.talkback()
    # OD anacúsico sin enmascarar: a 60 dB responde por el OI (sombra en 45)
    a.lbl_intencity[0].setText("60 dB HL")
    a.Helper_Stim(0, play=True)
    a.Helper_Stim(0, play=False)
    assert [p["mano"] for p in cola.de("audio_respuesta")] == [True, False]
    # la instrucción vigente viaja en la foto de cada estímulo
    assert cola.de("audio_stim_button")[0]["estado"]["instruccion"] == "colocar_fonos"


def test_bajo_la_sombra_no_hay_respuesta():
    a, cola = _audiometro()
    a.lbl_output[0].setText("Derecha")
    a.lbl_trans[0].setText(modulo.trans_list[0])
    a.supra("colocar_fonos")
    a.talkback()
    a.lbl_intencity[0].setText("30 dB HL")
    a.Helper_Stim(0, play=True)
    a.Helper_Stim(0, play=False)
    assert cola.de("audio_respuesta") == []


def test_la_hora_lleva_milisegundos():
    import sqlite3
    import tempfile
    from pathlib import Path

    from backend.log_queue import LocalLogQueue

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "logs.db"
        LocalLogQueue(ruta).push("x", {})
        with sqlite3.connect(ruta) as conn:
            (ts,) = conn.execute("SELECT ts FROM pending_logs").fetchone()
    assert re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3}", ts)


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
