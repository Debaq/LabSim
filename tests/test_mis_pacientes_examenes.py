""""Mis pacientes" (core/mis_pacientes.py).

Lista de atenciones cerradas a la izquierda y la elegida a la derecha
(resumen, conversación, ficha, exámenes). En Exámenes, el ABR/ECochG se abre
en el módulo para mirarlo; el resto no se abre en la app: el PDF está en la
web.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # noqa: E402,F401  crea la QApplication
from core import mis_pacientes as mp  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

INFORMES = [
    {"tipo": "ABR", "updated_at": "2026-09-10 10:40", "data": {"curvas": {"R1": {}}}},
    {"tipo": "EOA", "updated_at": "2026-09-10 10:20", "data": {"pruebas": {}}},
]
ATENCIONES = [
    {"appointment_id": 7, "nombre": "Benja", "apellido": "Soto", "fecha": "2026-09-10",
     "hora": "10:00", "procedimiento": "PEATC", "stats": {"long_pauses": 2}},
    {"appointment_id": 99, "nombre": "Ana", "apellido": "Rojas", "fecha": "2026-09-01",
     "hora": "09:00", "procedimiento": "Audiometría", "practica": True},
]


class _Sincrono:
    """hilos.en_fondo sin hilo: corre y avisa en el acto."""
    @staticmethod
    def en_fondo(funcion, *args, listo=None, **_kw):
        r = funcion(*args)
        if listo:
            listo(r)


class Main:
    def __init__(self):
        self.abiertos = []
        self.data_login = {"user": "alumno"}

    def abrir_abr_consulta(self, data, aviso):
        self.abiertos.append((data, aviso))


def _ventana():
    mp.hilos = _Sincrono
    mp.mis_atenciones = lambda: ATENCIONES
    mp.mis_informes = lambda cita: INFORMES if cita == 7 else []
    mp.mi_conversacion = lambda cita: []
    mp.MisPacientesWidget._leer_todo = staticmethod(lambda: (mp.mis_atenciones(), {}, {}))
    main = Main()
    w = mp.MisPacientesWidget(main)
    w.refresh()
    return w, main


def test_abre_la_primera_atencion():
    w, _ = _ventana()
    assert len(w._filas) == 2
    assert w._actual.it["appointment_id"] == 7
    assert w.lbl_paciente.text() == "Benja Soto"
    assert "2 atenciones" in w.lbl_resumen.text() and "1 de práctica" in w.lbl_resumen.text()
    assert w.lbl_practica.isHidden()


def test_lista_los_examenes_de_la_atencion():
    w, _ = _ventana()
    assert len(w._examenes) == 2
    assert len(w.botones_abr) == 1          # solo el ABR se abre en la app
    assert "web" in w.lbl_examenes.text()


def test_el_abr_se_abre_para_mirar():
    w, main = _ventana()
    w.botones_abr[0].click()
    data, aviso = main.abiertos[0]
    assert data == INFORMES[0]["data"]
    assert "solo lectura" in aviso and "Benja Soto" in aviso


def test_los_demas_no_se_abren_en_la_app():
    w, main = _ventana()
    w._ver_en_abr(INFORMES[1])
    assert main.abiertos == []


def test_atencion_sin_examenes():
    w, _ = _ventana()
    QTest.keyClick(w, Qt.Key.Key_Down)
    assert w._actual.it["appointment_id"] == 99
    assert w._examenes == [] and w.botones_abr == []
    assert "no tiene exámenes" in w.lbl_examenes.text()
    assert not w.lbl_practica.isHidden()


def test_buscar():
    w, _ = _ventana()
    w.buscar.setText("audiometria")
    assert [f.isHidden() for f in w._filas] == [True, False]
    assert w._actual.it["appointment_id"] == 99   # lo abierto quedó fuera


def test_respuesta_tardia_no_pisa():
    w, _ = _ventana()
    otra = w._filas[1].it
    w._mostrar_examenes(otra, INFORMES)      # llega lo de una atención ya dejada
    assert len(w.botones_abr) == 1 and len(w._examenes) == 2


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
