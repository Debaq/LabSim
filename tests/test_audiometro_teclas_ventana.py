"""Teclas del audiómetro: el filtro va en la ventana nativa principal (su
QWindow), no en QApplication. En QApplication cada evento de la app pasaba
por Python mientras el audiómetro estaba abierto, también los de objetos a
medio destruir (mismo mal que el del MDI, tickets 35, 36, 43 del
2026-11-05). Las teclas tienen que seguir llegando aunque el foco esté en
otra parte de la ventana, y el audiómetro va dentro de una escena con zoom
(core/reparto.py)."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
os.chdir(RAIZ)  # context.get_resource() usa rutas relativas a la raíz

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import (QApplication, QLineEdit, QPushButton,  # noqa: E402
                               QVBoxLayout, QWidget)

from audiometria.ventana import AudiometriaWindow  # noqa: E402


def _vueltas(n=5):
    for _ in range(n):
        QApplication.processEvents()


def _principal():
    """Una ventana principal con el audiómetro y otros controles al lado."""
    host = QWidget()
    lay = QVBoxLayout(host)
    v = AudiometriaWindow(None)
    otro = QPushButton("otro módulo")
    texto = QLineEdit()
    lay.addWidget(otro)
    lay.addWidget(texto)
    lay.addWidget(v, 1)
    host.resize(1366, 760)
    host.show()
    _vueltas()
    return host, v.audiometro, otro, texto


def _tecla(dic, valor):
    return next(k for k, v in dic.items() if v == valor)


def test_el_filtro_va_en_la_ventana_nativa_no_en_la_app():
    host, a, *_ = _principal()
    assert a._filter_installed
    assert a._filtro_en is host.windowHandle()
    a.hide()
    assert not a._filter_installed and a._filtro_en is None
    a.show()
    _vueltas()
    assert a._filtro_en is host.windowHandle()
    host.close()


def test_el_dial_sube_aunque_el_foco_este_en_otro_control():
    host, a, otro, _texto = _principal()
    otro.setFocus()
    _vueltas()
    antes = a.dial_ch0.value()
    QTest.keyPress(host.windowHandle(), Qt.Key(_tecla(a._dial_keys, (0, True))))
    _vueltas()
    assert a.dial_ch0.value() != antes
    host.close()


def test_el_estimulo_sigue_la_tecla_apretada_y_soltada():
    host, a, *_ = _principal()
    eventos = []
    a.btn_stims[0].pressed.connect(lambda: eventos.append("press"))
    a.btn_stims[0].released.connect(lambda: eventos.append("release"))
    tecla = Qt.Key(_tecla(a._stim_keys, 0))
    QTest.keyPress(host.windowHandle(), tecla)
    QTest.keyRelease(host.windowHandle(), tecla)
    _vueltas()
    assert eventos == ["press", "release"], eventos
    host.close()


def test_escribiendo_en_un_campo_de_texto_no_mueve_el_dial():
    host, a, _otro, texto = _principal()
    texto.setFocus()
    _vueltas()
    antes = a.dial_ch0.value()
    QTest.keyPress(host.windowHandle(), Qt.Key(_tecla(a._dial_keys, (0, True))))
    _vueltas()
    assert a.dial_ch0.value() == antes
    host.close()


def test_teclas_en_otra_ventana_no_llegan_al_audiometro():
    """Un diálogo u otra ventana de primer nivel: antes (filtro en la app)
    una tecla ahí también movía el audiómetro."""
    host, a, *_ = _principal()
    otra = QWidget()
    otra.resize(300, 200)
    otra.show()
    _vueltas()
    antes = a.dial_ch0.value()
    QTest.keyPress(otra.windowHandle(), Qt.Key(_tecla(a._dial_keys, (0, True))))
    _vueltas()
    assert a.dial_ch0.value() == antes
    otra.close()
    host.close()


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
