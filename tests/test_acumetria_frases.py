"""Diapasones sobre la cabeza, con instrucciones y preguntas (2026-11-06).

El alumno golpea el diapasón, lo apoya donde quiere en la cabeza y le habla
al paciente. El paciente contesta lo que le instruyeron o le preguntaron,
con el caso (diapasones.py); sin instrucción no sabe qué hacer; sin Rinne ni
Weber en el caso el diapasón suena con armónicos.
"""
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("LABSIM_DATA_DIR", tempfile.mkdtemp(prefix="labsim-test-"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np  # noqa: E402

from core.base import context  # noqa: E402,F401  (crea la QApplication)
import audiometria.Acumetria as A  # noqa: E402
from audiometria import cabeza_examen as ce  # noqa: E402
from audiometria import diapasones as dp  # noqa: E402

APP = context.app
# Como el caso 79 (Víctor, cap. 11): Rinne positivo, Weber al OI. En 1000 Hz
# el OI con un falso negativo para probar la trampa.
CASO = {"id": 79, "edad": 24,
        "Aerea": [[20, 15], [25, 10], [35, 15], [40, 25], [60, 35], [85, 45], [90, 55], [100, 55], [115, 65]],
        "Osea": [[20, 15], [25, 10], [35, 15], [40, 25], [60, 35], [85, 45], [90, 55], [100, 55], [115, 65]],
        "Rinne": {"500": {"od": "positivo", "oi": "positivo"},
                  "1000": {"od": "positivo", "oi": "falso_negativo"}},
        "Weber": {"500": "oi", "1000": "centrado"}}


class _Cola:
    def __init__(self):
        self.acciones = []

    def push(self, accion, payload):
        self.acciones.append((accion, payload))


class _Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _modulo(caso=CASO):
    w = A.Acumetria(None)
    w.log_queue = _Cola()
    w._reloj = _Reloj()
    w.la_super(dict(caso), 102)
    return w


def _apoyar(w, sitio):
    w._apoyar(ce._pos(sitio), np.array([0.0, 0.0, 1.0]))


def _ultima(w):
    return w.log.toPlainText().strip().splitlines()[-1]


def test_las_zonas_de_la_cabeza():
    assert ce.zona(ce._pos("M2"))[:2] == ("mastoides", "od")
    assert ce.zona(ce._pos("cae_izq"))[:2] == ("pabellon", "oi")
    assert ce.zona(ce._pos("Cz"))[:2] == ("linea_media", "vertice")
    assert ce.zona(ce._pos("F3"))[0] == "otro"


def test_sin_instruccion_el_paciente_no_sabe_que_hacer():
    w = _modulo()
    w._golpear()
    _apoyar(w, "M2")
    assert _ultima(w) == f"Paciente {A.NO_SABE}"


def test_sin_golpear_no_suena():
    w = _modulo()
    w._frase("avise_si_escucha")
    _apoyar(w, "M2")
    assert _ultima(w) == "Paciente No escucho nada."
    assert w.log_queue.acciones[-1][1]["vibrando"] is False


def test_avise_si_escucha_y_el_falso_negativo_por_aire():
    w = _modulo()
    w.botones_hz["1000"].setChecked(True)
    w._frase("avise_si_escucha")
    w._golpear()
    _apoyar(w, "cae_izq")
    assert _ultima(w) == "Paciente No escucho nada.", "oído muerto: por aire nada"
    _apoyar(w, "M1")
    assert _ultima(w) == "Paciente Sí, lo escucho.", "por hueso sí (lo oye el otro)"


def test_rinne_el_paciente_contesta_solo_lo_que_se_le_pregunta():
    """Instrucción, golpe, mastoides + ¿lo escucha?, frente a la oreja +
    ¿lo escucha?, y recién ahí ¿dónde lo escuchó más fuerte?"""
    w = _modulo()
    w._frase("compare_sonidos")
    w._golpear()
    _apoyar(w, "M2")
    assert _ultima(w).startswith("Tú"), "al apoyarlo no dice nada"
    w._frase("lo_escucha")
    assert _ultima(w) == "Paciente Sí."
    _apoyar(w, "cae_der")
    assert _ultima(w).startswith("Tú"), "no compara antes de que le pregunten"
    w._frase("lo_escucha")
    assert _ultima(w) == "Paciente Sí."
    w._frase("donde_mas_fuerte")
    assert "Adelante, frente a la oreja" in _ultima(w)


def test_el_falso_negativo_suena_como_un_negativo():
    w = _modulo()
    w.botones_hz["1000"].setChecked(True)
    w._frase("compare_sonidos")
    w._golpear()
    _apoyar(w, "M1")
    _apoyar(w, "cae_izq")
    w._frase("lo_escucha")
    assert _ultima(w) == "Paciente No.", "oído muerto: por aire nada"
    w._frase("donde_mas_fuerte")
    assert _ultima(w) == "Paciente Atrás, en el hueso. Ahí suena más fuerte."


def test_weber_en_la_linea_media():
    w = _modulo()
    w._frase("diga_donde")
    w._golpear()
    _apoyar(w, "Cz")
    assert _ultima(w).startswith("Tú"), "espera la pregunta"
    w._frase("donde_mas_fuerte")
    assert _ultima(w) == "Paciente En el oído izquierdo."
    w._frase("igual_ambos")
    assert _ultima(w) == "Paciente No, más en el izquierdo."
    assert w._instruccion == "diga_donde", "la pregunta no reemplaza la instrucción"


def test_el_diapason_se_apaga_con_el_tiempo():
    w = _modulo()
    w._frase("avise_si_escucha")
    w._golpear()
    t_aire, t_hueso = w.modelo.tiempos("500", "od")
    w._reloj.t += t_hueso + 1
    _apoyar(w, "M2")
    assert _ultima(w) == "Paciente Siento que vibra, pero no lo escucho."
    w._frase("escucha_o_vibra")
    assert _ultima(w) == "Paciente Solo siento que vibra."
    assert t_aire > t_hueso, "Rinne positivo: por aire dura más"
    _apoyar(w, "cae_der")
    assert _ultima(w) == "Paciente Sí, lo escucho.", "y frente a la oreja todavía lo oye"


def test_sin_rinne_ni_weber_suena_con_armonicos():
    w = _modulo({"id": 5, "edad": 30, "Aerea": CASO["Aerea"]})
    assert not w.modelo.disponible()
    assert not w.btn_golpear.isEnabled() and not w.lbl_armonicos.isHidden()
    _apoyar(w, "M2")
    assert A.ARMONICOS in _ultima(w)


def test_todo_queda_en_el_registro_con_la_verdad_del_caso():
    w = _modulo()
    w._frase("avise_si_escucha")
    w._golpear()
    _apoyar(w, "M2")
    w._frase("lo_escucha")
    acciones = [a for a, _p in w.log_queue.acciones]
    assert acciones == ["ac_instruccion", "ac_golpe", "ac_apoyo", "ac_pregunta"], acciones
    apoyo = w.log_queue.acciones[2][1]
    assert apoyo["zona"] == "mastoides" and apoyo["oido"] == "od" and apoyo["rinne"] == "positivo"
    assert apoyo["case_id"] == 79 and apoyo["oye"] is True


def test_los_tiempos_siguen_el_rinne_del_caso():
    m = dp.ModeloDiapasones({"Aerea": CASO["Aerea"], "Osea": [[0, 0]] * 9,
                             "Rinne": {"500": {"od": "negativo", "oi": "positivo"}}, "Weber": {"500": "od"}})
    t_aire, t_hueso = m.tiempos("500", "od")
    assert t_aire < t_hueso, "negativo: por hueso dura más"


def test_se_puede_preguntar_despues_de_sacarlo():
    """Se pone en la línea media, se saca y recién ahí se pregunta."""
    w = _modulo()
    w._golpear()
    _apoyar(w, "Cz")
    w._retirar()
    w._frase("donde_mas_fuerte")
    assert _ultima(w) == "Paciente En el oído izquierdo."
    w._frase("igual_ambos")
    assert _ultima(w) == "Paciente No, más en el izquierdo."
    w._frase("lo_escucha")
    assert _ultima(w) == "Paciente Ahora no, ya lo sacó."
    assert w.log_queue.acciones[-1][1]["retirado"] is True


def test_el_rinne_se_compara_tambien_despues_de_sacarlo():
    w = _modulo()
    w._golpear()
    _apoyar(w, "M2")
    _apoyar(w, "cae_der")
    w._retirar()
    w._frase("donde_mas_fuerte")
    assert "Adelante, frente a la oreja" in _ultima(w)


def test_si_no_lo_oia_cuando_lo_saco_lo_dice():
    w = _modulo()
    w._golpear()
    _apoyar(w, "M2")
    w._reloj.t += 200          # ya no se oía
    w._retirar()
    w._frase("escucha_o_vibra")
    assert _ultima(w) == "Paciente Solo sentía que vibraba."


def test_al_golpear_de_nuevo_se_olvida_lo_anterior():
    w = _modulo()
    w._golpear()
    _apoyar(w, "Cz")
    w._retirar()
    w._golpear()
    w._frase("donde_mas_fuerte")
    assert _ultima(w) == "Paciente ¿Qué cosa?"

def test_un_paciente_nuevo_empieza_sin_instruccion():
    w = _modulo()
    w._frase("avise_si_escucha")
    w._golpear()
    w.la_super(dict(CASO, id=80), 103)
    assert w._instruccion is None and w._golpe is None and w.log.toPlainText() == ""


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
            except Exception as exc:  # noqa: BLE001
                fallas += 1
                print(f"ERROR {nombre}: {type(exc).__name__}: {exc}")
    sys.exit(1 if fallas else 0)
