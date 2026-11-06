"""Otoscopía sobre la cabeza, como la rinoscopía (2026-11-06): el mouse es
el otoscopio y arrastrar desde la oreja tira del pabellón. Con el pabellón
bien traccionado o no (arriba y atrás; abajo y atrás en menores de 3 años),
la foto se ve entera: la tracción queda en el registro para la evaluación.
"""
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("LABSIM_DATA_DIR", tempfile.mkdtemp(prefix="labsim-test-"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtGui import QColor, QPixmap  # noqa: E402

from core.base import context  # noqa: E402,F401  (crea la QApplication)
import audiometria.Otoscopia as O  # noqa: E402

APP = context.app


class _Cola:
    def __init__(self):
        self.acciones = []

    def push(self, accion, payload):
        self.acciones.append((accion, payload))


def _modulo(edad=40):
    from audiometria.Acumetria import Acumetria
    from audiometria.ventana_ot_ac import OtoscopiaAcumetriaWindow
    w = O.Otoscopia(None)
    w.ventana = OtoscopiaAcumetriaWindow(w, Acumetria(None))   # la cabeza es de la ventana
    w.log_queue = _Cola()
    w.data = {"id": 79, "edad": edad}
    w.appointment_id = 102
    foto = QPixmap(200, 200)
    foto.fill(QColor("pink"))
    w._fotos = {"od": foto, "oi": None}
    return w


def test_la_pared_tapa_segun_la_traccion():
    w = _modulo(edad=40)
    assert w.vista("od")["pared"] == O.PARED["mala"], "sin tracción se ve el contraconducto"
    w._traccionar("od", 1.5, 1.5)                  # arriba y atrás, firme
    assert w._tiron["calidad"] == "buena" and w.vista("od")["pared"] == 0.0
    w._traccionar("od", 0.3, 1.5)                  # casi solo hacia atrás
    assert w._tiron["calidad"] == "regular" and 0 < w.vista("od")["pared"] < O.PARED["mala"]
    w._traccionar("od", -1.5, 1.5)                 # abajo y atrás en un adulto
    assert w._tiron["calidad"] == "mala"
    w._traccionar("od", 0.5, 0.5)                  # buena dirección pero débil
    assert w._tiron["calidad"] == "regular"


def test_adulto_arriba_y_atras_se_ve_todo():
    w = _modulo(edad=40)
    w._traccionar("od", 1.5, 1.5)
    assert w._tiron["correcto"]
    assert w.vista("oi")["texto"] == O.SIN_IMAGEN_TEXTO, "sin foto, otoscopio sin batería"


def test_en_un_bebe_va_abajo_y_atras():
    w = _modulo(edad=1)
    w._traccionar("od", 1.5, 1.5)
    assert not w._tiron["correcto"]
    w._traccionar("od", -1.5, 1.5)
    assert w._tiron["correcto"]


def test_el_especulo_de_adulto_no_entra_en_un_nino():
    w = _modulo(edad=4)
    w.btn_cono_adulto.setChecked(True)
    assert "no entra" in w.vista("od")["texto"]
    w._miro("od")
    assert w.log_queue.acciones[-1][0] == "ot_especulo_grande"


def test_el_mouse_en_el_conducto_es_el_otoscopio():
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import QEvent
    w = _modulo()
    w.cabeza.resize(600, 600)
    w.ventana.elegir_herramienta("otoscopia")   # como en los electrodos: la herramienta se elige
    w.cabeza.show()
    w.cabeza.mirar_oido("od")
    APP.processEvents()
    pos = w.cabeza._centro_conducto("od")
    ev = QMouseEvent(QEvent.Type.MouseMove, QPointF(pos), QPointF(pos), Qt.MouseButton.NoButton,
                     Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    w.cabeza.mouseMoveEvent(ev)
    assert w._dentro == "od" and w.log_queue.acciones[-1][0] == "ot_otoscopio"
    w.cabeza.grab()   # dibuja la lupa sin caerse


def test_el_tiron_del_otro_oido_no_endereza_este():
    w = _modulo()
    w._traccionar("oi", 1.5, 1.5)
    assert w.vista("od")["pared"] == O.PARED["mala"]


def test_queda_en_el_registro():
    w = _modulo()
    w._traccionar("od", 1.5, 1.5)
    w._miro("od")
    acciones = [a for a, _p in w.log_queue.acciones]
    assert acciones == ["ot_traccion", "ot_otoscopio"], acciones
    assert w.log_queue.acciones[-1][1]["traccion_correcta"] is True



def test_el_informe_lleva_las_dos_secciones_y_vuelve():
    w = _modulo()
    inf = w.ventana.informe_acumetria
    inf._ciclar(("500", "od"))                      # (+)
    for _ in range(3):
        inf._ciclar(("1000", "oi"))                 # (+), (−), FN
    inf._weber("500", "oi", True)
    job = w.report_job()
    assert job["tipo"] == "OTOSCOPIA"
    assert job["data"]["acumetria"] == {"rinne": {"500": {"od": "positivo"}, "1000": {"oi": "falso_negativo"}},
                                        "weber": {"500": "oi"}}, job["data"]
    datos = job["data"]
    w.la_super(dict(w.data), 102)                   # retomar: se limpia y vuelve
    assert not inf.tiene_algo()
    assert w.restore_report(datos) and inf.to_dict() == datos["acumetria"]


def test_solo_diapasones_tambien_se_informa():
    w = _modulo()
    assert w.report_job() is None, "sin nada marcado no hay informe"
    w.ventana.informe_acumetria._weber("1000", "centrado", True)
    assert w.report_job()["data"]["acumetria"]["weber"] == {"1000": "centrado"}


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
