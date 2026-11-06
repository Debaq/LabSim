"""Diapasones con instrucciones y preguntas (2026-11-06).

El paciente contesta lo que le instruyeron o le preguntaron, con los datos
del caso; sin instrucción no sabe qué hacer cuando siente el diapasón. Una
pregunta se contesta y no reemplaza la instrucción vigente.
"""
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("LABSIM_DATA_DIR", tempfile.mkdtemp(prefix="labsim-test-"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # noqa: E402,F401  (crea la QApplication)
import audiometria.Acumetria as A  # noqa: E402

# Como el caso 79 (Víctor, cap. 11): Rinne positivo, Weber al OI. El OI con
# un falso negativo en 1000 Hz para probar la trampa.
CASO = {"id": 79, "edad": 24,
        "Rinne": {"500": {"od": "positivo", "oi": "positivo"},
                  "1000": {"od": "positivo", "oi": "falso_negativo"}},
        "Weber": {"500": "oi", "1000": "centrado"}}


class _Cola:
    def __init__(self):
        self.acciones = []

    def push(self, accion, payload):
        self.acciones.append((accion, payload))


def _modulo():
    w = A.Acumetria(None)
    w.log_queue = _Cola()
    w.la_super(dict(CASO), 102)
    return w


def _ultima(log):
    return log.toPlainText().strip().splitlines()[-1]


def test_sin_instruccion_el_paciente_no_sabe_que_hacer():
    w = _modulo()
    w._rinne_probar_mastoides()
    assert _ultima(w.rinne_log) == f"Paciente {A.NO_SABE}"


def test_con_avise_si_escucha_contesta_si_lo_escucha():
    w = _modulo()
    w._frase("avise_si_escucha")
    w._rinne_probar_mastoides()
    assert _ultima(w.rinne_log) == "Paciente Sí, lo escucho."
    w.rinne_1000.setChecked(True)
    w.rinne_oi.setChecked(True)          # falso negativo: por aire no oye
    w._rinne_probar_pabellon()
    assert _ultima(w.rinne_log) == "Paciente No... no escucho nada."


def test_compare_contesta_solo_con_las_dos_posiciones():
    w = _modulo()
    w._frase("compare_sonidos")
    w._rinne_probar_mastoides()
    assert _ultima(w.rinne_log) == "Paciente Ya."
    w._rinne_probar_pabellon()
    assert "Adelante, frente a la oreja" in _ultima(w.rinne_log)


def test_el_falso_negativo_suena_igual_que_un_negativo():
    w = _modulo()
    w.rinne_1000.setChecked(True)
    w.rinne_oi.setChecked(True)
    w._frase("compare_sonidos")
    w._rinne_probar_mastoides()
    w._rinne_probar_pabellon()
    w._frase("donde_mas_fuerte")
    assert _ultima(w.rinne_log) == "Paciente Atrás, en el hueso. Ahí suena más fuerte."


def test_weber_dice_donde_con_la_instruccion_y_con_la_pregunta():
    w = _modulo()
    w.tabs.setCurrentIndex(1)
    w._frase("igual_ambos")
    assert _ultima(w.weber_log) == "Paciente ¿Qué cosa?", "sin diapasón no hay nada que comparar"
    w._frase("diga_donde")
    w._weber_probar()
    assert _ultima(w.weber_log) == "Paciente En el oído izquierdo."
    w._frase("igual_ambos")
    assert _ultima(w.weber_log) == "Paciente No, más en el izquierdo."
    assert w._instruccion == "diga_donde", "la pregunta no reemplaza la instrucción"


def test_una_instruccion_del_rinne_no_sirve_para_el_weber():
    w = _modulo()
    w.tabs.setCurrentIndex(1)
    w._frase("compare_sonidos")
    w._weber_probar()
    assert _ultima(w.weber_log) == f"Paciente {A.NO_SABE}"


def test_todo_queda_en_el_registro_con_la_verdad_del_caso():
    w = _modulo()
    w._frase("avise_si_escucha")
    w._rinne_probar_mastoides()
    w._frase("lo_escucha")
    acciones = [a for a, _p in w.log_queue.acciones]
    assert acciones == ["ac_instruccion", "ac_rinne_mastoides", "ac_pregunta"], acciones
    _a, pregunta = w.log_queue.acciones[-1]
    assert pregunta["clave"] == "lo_escucha" and pregunta["respuesta"] == "Sí."
    assert pregunta["resultado"] == "positivo" and pregunta["case_id"] == 79


def test_un_paciente_nuevo_empieza_sin_instruccion():
    w = _modulo()
    w._frase("avise_si_escucha")
    w.la_super(dict(CASO, id=80), 103)
    assert w._instruccion is None and w.rinne_log.toPlainText() == ""


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
