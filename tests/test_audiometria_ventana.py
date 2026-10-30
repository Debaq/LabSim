"""El audiómetro en una sola ventana (audiometria/ventana.py): reparto
1:3:1 con el audiómetro al centro, y comandos de voz y listas de palabras a
la vista, sin plegarse, en cualquier ancho."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
os.chdir(RAIZ)  # context.get_resource() usa rutas relativas a la raíz

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from PySide6.QtCore import QPoint, QRect  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from audiometria.ventana import LOGO, AudiometriaWindow  # noqa: E402
from audiometria.comandos_voz import ComandosVoz  # noqa: E402


def _ventana(ancho, alto=650, **kw):
    v = AudiometriaWindow(None, **kw)
    v.resize(ancho, alto)
    v.show()
    QApplication.processEvents()
    return v


def _rect(v, w):
    """El rectángulo de `w` en coordenadas de la ventana: los paneles van
    dentro de su columna."""
    return QRect(w.mapTo(v, QPoint(0, 0)), w.size())


def _logo(v, activa=True):
    v.audiometro.prueba_cambio.emit(LOGO if activa else "Umbrales")
    QApplication.processEvents()


def _dibujado(v):
    """Lo que ocupa el audiómetro en pantalla, ya con su zoom."""
    e = v.escalado
    arriba_izq = e.mapTo(v, e.mapFromScene(0, 0))
    lado = e.base * e.escala
    return QRect(arriba_izq, lado)


def test_comandos_a_la_izquierda_y_listas_solo_con_logo():
    v = _ventana(1366, 660)
    assert v.comandos.isVisible() and v.aviso_listas.isVisible()
    assert not v.listas.isVisible()
    assert _rect(v, v.comandos).right() < _dibujado(v).left()
    _logo(v)
    assert v.listas.isVisible() and not v.aviso_listas.isVisible()
    assert _rect(v, v.listas).left() > _dibujado(v).right()
    _logo(v, False)
    assert not v.listas.isVisible() and v.aviso_listas.isVisible()


def test_reparto_1_3_1_con_el_audiometro_al_centro():
    for ancho, alto in ((1920, 970), (1366, 660), (1280, 610), (1024, 660)):
        v = _ventana(ancho, alto)
        _logo(v)
        quinto = (ancho - 4 * 6) / 5
        assert abs(v.col_izq.width() - quinto) <= 2, ancho
        assert abs(v.col_der.width() - quinto) <= 2, ancho
        assert abs(v.escalado.width() - 3 * quinto) <= 3, ancho
        a = _dibujado(v)
        # llena su parte (a lo ancho o a lo alto, sin deformarse) y al medio
        assert a.width() >= v.escalado.width() - 3 or a.height() >= v.escalado.height() - 3
        assert abs(a.center().x() - ancho / 2) <= 3, ancho
        assert abs(a.center().y() - alto / 2) <= 3, ancho
        for w in (v.comandos, v.listas):
            assert _rect(v, w).right() <= ancho
    assert _ventana(1920, 970).escalado.escala > 1.4       # lo más grande
    v = _ventana(1366, 660, listas=False)                  # aunque un lateral quede vacío
    assert abs(_dibujado(v).center().x() - 1366 / 2) <= 3


def test_sin_permiso_no_aparece_su_panel():
    v = _ventana(1366, listas=False)
    _logo(v)
    assert not v.listas.isVisible() and not v.aviso_listas.isVisible()
    v = _ventana(1366, comandos=False)
    assert not v.comandos.isVisible()


def test_las_columnas_siguen_al_ancho():
    v = _ventana(1024, 660)
    _logo(v)
    assert v.comandos.columnas == 1
    assert v.listas.columnas == 2
    v = _ventana(1920, 970)
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
