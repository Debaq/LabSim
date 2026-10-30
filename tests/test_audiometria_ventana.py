"""El audiómetro en una sola ventana (audiometria/ventana.py): comandos de
voz y listas de palabras a la vista, sin plegarse, en cualquier ancho."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
os.chdir(RAIZ)  # context.get_resource() usa rutas relativas a la raíz

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from PySide6.QtWidgets import QApplication  # noqa: E402

from audiometria.ventana import LOGO, AudiometriaWindow  # noqa: E402
from audiometria.comandos_voz import ComandosVoz  # noqa: E402


def _ventana(ancho, alto=650, **kw):
    v = AudiometriaWindow(None, **kw)
    v.resize(ancho, alto)
    v.show()
    QApplication.processEvents()
    return v


def _logo(v, activa=True):
    v.audiometro.prueba_cambio.emit(LOGO if activa else "Umbrales")
    QApplication.processEvents()


def test_ancha_tres_columnas_y_listas_solo_con_logo():
    v = _ventana(1366)
    assert v._modo == "lado"
    assert v.comandos.isVisible() and v.aviso_listas.isVisible()
    assert not v.listas.isVisible()
    # comandos a la izquierda del audiómetro, listas a la derecha
    assert v.comandos.geometry().right() < v.audiometro.geometry().left()
    _logo(v)
    assert v.listas.isVisible() and not v.aviso_listas.isVisible()
    assert v.listas.geometry().left() > v.audiometro.geometry().right()
    _logo(v, False)
    assert not v.listas.isVisible() and v.aviso_listas.isVisible()


def test_1280_todavia_cabe_lado_a_lado():
    assert _ventana(1280)._modo == "lado"


def test_angosta_comparten_la_columna_derecha_sin_esconderse():
    v = _ventana(1024)
    assert v._modo == "columna"
    assert v.comandos.isVisible()
    assert v.comandos.geometry().left() > v.audiometro.geometry().right()
    _logo(v)
    assert v.listas.isVisible() and v.comandos.isVisible()
    assert v.listas.geometry().top() > v.comandos.geometry().bottom()
    # nada se sale de la ventana
    for w in (v.comandos, v.listas, v.audiometro):
        assert w.geometry().right() <= v.width()


def test_sin_permiso_no_aparece_su_panel():
    v = _ventana(1366, listas=False)
    _logo(v)
    assert not v.listas.isVisible() and not v.aviso_listas.isVisible()
    v = _ventana(1366, comandos=False)
    assert not v.comandos.isVisible()


def test_las_columnas_siguen_al_ancho():
    v = _ventana(1024)
    _logo(v)
    assert v.comandos.columnas == 1
    assert v.listas.columnas in (2, 3)
    v = _ventana(1920)
    _logo(v)
    assert v.comandos.columnas >= 2
    assert v.listas.columnas >= 4


def test_la_frase_elegida_llega_al_audiometro():
    v = _ventana(1366)
    v.comandos.botones["cambie_de_volumen"].click()
    assert v.audiometro.state_supra[1] == "cambie_de_volumen"
    v.comandos.silencio()
    assert v.audiometro.state_supra == [None, None]


def test_cada_instruccion_dice_su_prueba_y_se_busca_por_ella():
    c = ComandosVoz()
    btn = c.botones["cambie_de_volumen"]
    assert btn.property("rotulo") == "Cambie de volumen"
    assert "SISI" in [lbl.text() for lbl in btn.findChildren(type(c.lbl_frase))]
    c.buscar.setText("sisi")
    assert [b for b in c.botones.values() if not b.isHidden()] == [btn]
    c.buscar.setText("fowler")
    visibles = {k for k, b in c.botones.items() if not b.isHidden()}
    assert visibles == {"dos_pitos", "sonidos_iguales", "en_qué_oído"}


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    # Cerrarlas saca el filtro de teclas de cada audiómetro: si queda
    # puesto, el cierre de Qt lo llama ya sin Python y ensucia la salida.
    for w in QApplication.topLevelWidgets():
        w.close()
    QApplication.processEvents()
    print("TODOS LOS TESTS PASARON")
