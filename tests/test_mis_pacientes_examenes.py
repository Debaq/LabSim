"""Pestaña "Exámenes" de "Mis pacientes" (core/mis_pacientes.py).

Lista los informes de una atención cerrada. El ABR/ECochG se abre en el
módulo para mirarlo; el resto no se abre en la app: el PDF está en la web.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # noqa: E402,F401  crea la QApplication
from core import mis_pacientes as mp  # noqa: E402

INFORMES = [
    {"tipo": "ABR", "updated_at": "2026-09-10 10:40", "data": {"curvas": {"R1": {}}}},
    {"tipo": "EOA", "updated_at": "2026-09-10 10:20", "data": {"pruebas": {}}},
]
ATENCION = {"appointment_id": 7, "nombre": "Benja", "apellido": "Soto", "fecha": "2026-09-10"}


class Main:
    def __init__(self):
        self.abiertos = []

    def abrir_abr_consulta(self, data, aviso):
        self.abiertos.append((data, aviso))


def _pestana():
    mp.mis_informes = lambda cita: INFORMES if cita == 7 else []
    main = Main()
    w = mp.MisPacientesWidget(main)
    w._mostrar_examenes(ATENCION)
    return w, main


def test_lista_los_examenes_de_la_atencion():
    w, _ = _pestana()
    assert w.tabla_examenes.rowCount() == 2
    assert w.tabla_examenes.item(0, 0).text() == "PEATC (ABR)"
    assert "web" in w.lbl_examenes.text()


def test_el_abr_se_abre_para_mirar():
    w, main = _pestana()
    w.tabla_examenes.selectRow(0)
    assert w.btn_ver_abr.isEnabled()
    w.btn_ver_abr.click()
    data, aviso = main.abiertos[0]
    assert data == INFORMES[0]["data"]
    assert "solo lectura" in aviso and "Benja Soto" in aviso


def test_los_demas_no_se_abren_en_la_app():
    w, main = _pestana()
    w.tabla_examenes.selectRow(1)
    assert not w.btn_ver_abr.isEnabled()
    w._ver_en_abr()
    assert main.abiertos == []


def test_atencion_sin_examenes():
    w, _ = _pestana()
    w._mostrar_examenes({"appointment_id": 99})
    assert w.tabla_examenes.rowCount() == 0
    assert "no tiene exámenes" in w.lbl_examenes.text()


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
