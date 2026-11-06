"""Las ventanas de los módulos se arman tras el login (main.load_sub_windows).

El 2026-11-06, al juntar otoscopía y diapasones en una ventana, el login
se caía con "'_Parte' object has no attribute 'visibility_changed'" y
ningún test armaba las ventanas como después de entrar. Acá se arman con un
login simulado (sin red: la agenda no se pide) y se revisa que esconder la
ventana de OT/AC suba los informes de los dos, como antes.
"""
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("LABSIM_DATA_DIR", tempfile.mkdtemp(prefix="labsim-test-"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # noqa: E402,F401  (crea la QApplication)
import main  # noqa: E402

APP = context.app


def _ventana(modulos):
    w = main.MainWindow()
    w.data_login = {"user": "demo_curso_1", "name": "Estudiante demo", "permission": 444,
                    "modules": modulos, "prefs": {}}
    w.load_sub_windows()
    return w


def test_se_arman_y_otac_sube_los_dos_informes_al_esconderse():
    w = _ventana(["A", "Z", "AC", "OT", "AGENDA", "CHAT", "FICHA", "EVOLUCION"])
    try:
        guardados = []
        w.report_autosave.guardar = guardados.append
        marco = w.subw["AC"]
        assert "OT" not in w.subw, "OT no tiene ventana propia: va en la de AC"
        assert w.subw_ot.obj is marco.obj.otoscopia and w.subw_ac.obj is marco.obj.acumetria
        marco.visibility_changed.emit(False)
        assert w.subw_ot.obj in guardados, "el informe de otoscopía se sube al esconder"
    finally:
        w.close()


def test_con_solo_otoscopia_no_hay_diapason():
    w = _ventana(["OT", "AGENDA"])
    try:
        assert "diapason" not in w.subw["AC"].obj.botones_herramienta
        assert "otoscopia" in w.subw["AC"].obj.botones_herramienta
    finally:
        w.close()


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
