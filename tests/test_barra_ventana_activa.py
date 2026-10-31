"""La ventana activa y su ✕ en la barra de la ventana principal, como la
barra de menú del Mac: los exámenes a pantalla completa no tienen barra
propia y se cierran desde ahí. Configuración va arriba, junto al usuario."""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtWidgets import QLabel  # noqa: E402

import main  # noqa: E402
from core.h_win import FrameSubMdi  # noqa: E402

APP = main.context.app


def _esperar():
    # El aviso del MDI va diferido (QTimer 0).
    for _ in range(3):
        APP.processEvents()


def _ventana():
    w = main.MainWindow()
    w.resize(1366, 768)
    w.show()
    w.btns_actions()
    _esperar()
    return w


def _abrir(w, nombre, pos_z, size):
    frame = FrameSubMdi(QLabel(nombre), expand=True)
    w.create_sub_window(frame, nombre, pos_z=pos_z, fix=(False, True), size=size,
                        position=[10, 10])
    _esperar()
    return frame


def test_configuracion_junto_al_usuario():
    w = _ventana()
    layout = w.horizontalLayout_6
    assert layout.indexOf(w.btn_configuracion) == layout.indexOf(w.btn_login) - 1
    assert w.btn_configuracion.isVisibleTo(w)
    assert w.layoutAction.indexOf(w.btn_configuracion) == -1
    assert not hasattr(w, "cerrar_ventanas")


def test_sin_ventanas_no_hay_nombre():
    w = _ventana()
    for sub in w.mdi_area.subWindowList():
        sub.hide()
    _esperar()
    assert not w.lbl_ventana_activa.isVisibleTo(w)
    assert not w.btn_cerrar_activa.isVisibleTo(w)


def test_examen_full_sin_barra_propia_y_se_cierra_desde_arriba():
    w = _ventana()
    examen = _abrir(w, "Audiómetro", len(w.modules.data) - 1, "max")
    assert not examen.barra.isVisibleTo(examen)
    assert w.lbl_ventana_activa.text() == "Audiómetro"
    assert w.btn_cerrar_activa.isVisibleTo(w)
    w.btn_cerrar_activa.click()
    _esperar()
    assert examen.parent().isHidden()


def test_la_ventana_de_encima_manda_y_al_cerrarla_vuelve_el_examen():
    w = _ventana()
    examen = _abrir(w, "Audiómetro", len(w.modules.data) - 1, "max")
    acumetria = _abrir(w, "Acumetría", len(w.modules.data) - 2, (480, 420))
    assert acumetria.barra.isVisibleTo(acumetria)
    assert w.lbl_ventana_activa.text() == "Acumetría"
    w.btn_cerrar_activa.click()
    _esperar()
    assert acumetria.parent().isHidden()
    assert not examen.parent().isHidden()
    assert w.lbl_ventana_activa.text() == "Audiómetro"


def test_cerrar_sesion_limpia_la_barra():
    w = _ventana()
    w._limpiar_barras()
    _esperar()
    assert w.lbl_ventana_activa is None
    assert not w.btn_configuracion.isVisibleTo(w)


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"ok   {nombre}")
