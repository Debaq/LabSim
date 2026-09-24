"""Diálogo de Configuración (core/configuracion.py): atajos y mouse para
zurdos, guardados en el perfil del usuario."""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtGui import QKeySequence  # noqa: E402
from PySide6.QtWidgets import QDialogButtonBox  # noqa: E402

from core.base import context  # noqa: E402,F401
from core import configuracion, helpers  # noqa: E402
from core.preferencias import preferencias  # noqa: E402


def _dialogo(prefs=None):
    preferencias().cargar(prefs or {})
    return configuracion.ConfiguracionDialog()


def _guardar_habilitado(d):
    return d.botones.button(QDialogButtonBox.StandardButton.Save).isEnabled()


def test_muestra_las_teclas_vigentes():
    d = _dialogo({"atajos": {"a_ch1_subir": "Up"}})
    assert d._tecla("a_ch1_subir") == "Up"
    assert d._tecla("a_ch1_bajar") == "S"


def test_no_deja_guardar_teclas_repetidas():
    d = _dialogo()
    d.editores["a_ch2_subir"].setKeySequence(QKeySequence("W"))
    assert not _guardar_habilitado(d)
    assert "repetida" in d.lbl_error.text()
    d._restaurar()
    assert _guardar_habilitado(d)


def test_guarda_solo_lo_que_cambio_y_el_mouse():
    enviado = []

    def guardar(prefs):
        enviado.append(prefs)
        return prefs
    helpers.guardar_preferencias = guardar
    d = _dialogo()
    d.editores["a_ch1_subir"].setKeySequence(QKeySequence("Up"))
    d.chk_zurdo.setChecked(True)
    d._guardar()
    assert enviado == [{"mouse_zurdo": True, "atajos": {"a_ch1_subir": "Up"}}]
    assert preferencias().mouse_zurdo()
    assert preferencias().atajos() == {"a_ch1_subir": "Up"}


def test_si_falla_el_servidor_lo_dice_y_no_cierra():
    def falla(prefs):
        raise RuntimeError("sin red")
    helpers.guardar_preferencias = falla
    d = _dialogo()
    d._guardar()
    assert "sin red" in d.lbl_error.text()
    assert d.result() == 0


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
