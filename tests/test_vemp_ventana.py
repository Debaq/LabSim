"""La ventana del VEMP en las pantallas de los PC del laboratorio: entra sin
cortarse en el área MDI de 1366x768, 1280x720 y 1024x768, y los mandos pasan
a dos columnas solo cuando en una no caben a lo alto."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(RAIZ)  # context.get_resource() usa rutas relativas a la raíz

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from PySide6.QtWidgets import QApplication  # noqa: E402

from test_vemp import caso  # noqa: E402
from vemp.VempMainWindow import VempMainWindow  # noqa: E402

# Área MDI de cada resolución (la misma que usan los tests del audiómetro).
AREAS = ((1366, 660), (1280, 610), (1024, 660))


def _ventana(ancho, alto, con_caso=True):
    v = VempMainWindow(data_login={"name": "Prueba"})
    if con_caso:
        v.la_super(caso(), appointment_id=1)
    v.resize(ancho, alto)
    v.show()
    QApplication.processEvents()
    return v


def test_entra_en_el_area_mdi():
    for ancho, alto in AREAS:
        v = _ventana(ancho, alto)
        minimo = v.minimumSizeHint()
        assert minimo.width() <= ancho and minimo.height() <= alto, (ancho, alto, minimo)
        assert (v.width(), v.height()) == (ancho, alto)
        v.close()


def test_el_emg_se_ve_entero():
    """El medidor de EMG es lo que se mira mientras se registra: no puede
    quedar abajo del scroll de los mandos."""
    for ancho, alto in AREAS:
        v = _ventana(ancho, alto)
        barra = v.izquierda.verticalScrollBar()
        assert barra.maximum() == 0, (ancho, alto, barra.maximum())
        fondo = v.caja_emg.mapTo(v.izquierda.viewport(), v.caja_emg.rect().bottomLeft())
        assert fondo.y() <= v.izquierda.viewport().height(), (ancho, alto)
        v.close()


def test_dos_columnas_solo_si_falta_alto():
    v = _ventana(1366, 660)
    assert v.dos_columnas is False          # cabe en una: trazas más anchas
    v.resize(1280, 610)
    QApplication.processEvents()
    assert v.dos_columnas is True
    v.resize(1920, 970)
    QApplication.processEvents()
    assert v.dos_columnas is False
    v.close()


def test_sin_caso_no_se_registra():
    v = _ventana(1366, 660, con_caso=False)
    assert not v.control.btn_registrar.isEnabled()
    assert not v.control.btn_detener.isEnabled()
    assert not v.control.caja_estimulo.isEnabled()
    v.la_super(caso(), appointment_id=1)
    assert v.control.btn_registrar.isEnabled()
    v.close()


def test_la_cabecera_sigue_a_los_mandos():
    """Intensidad, tasa y barridos cambian lo que dice la cabecera (antes
    quedaba con los valores viejos hasta tocar otro control)."""
    v = _ventana(1366, 660)
    v.control.sb_promedios.setValue(500)
    assert '500 barridos' in v.lbl_estado.text()
    v.control.sb_int.setValue(v.control.sb_int.minimum())
    assert v.pill_condicion.text().startswith(f'{v.control.sb_int.minimum()} dB')
    v.close()


if __name__ == "__main__":
    for nombre, prueba in list(globals().items()):
        if nombre.startswith("test_") and callable(prueba):
            prueba()
            print("ok", nombre)
