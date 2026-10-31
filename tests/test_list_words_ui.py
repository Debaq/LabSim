"""Lista de palabras (audiometria/ListWords.py): la grilla armada a mano
conserva lo que el resto del código espera de los botones."""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # crea la QApplication  # noqa: F401
from PySide6.QtWidgets import QPushButton
from audiometria import ListWords as LW


def _botones(w):
    return [b for b in w.findChildren(QPushButton) if LW.ListWords._BOTON_PALABRA.match(b.objectName())]


def test_seis_listas_de_25_con_el_nombre_que_espera_pushaudio():
    # 5 de bisílabos y términos conocidos + 1 de compuestas (SRT)
    w = LW.ListWords(None)
    botones = _botones(w)
    assert len(botones) == 150
    assert len({b.objectName() for b in botones}) == 150
    # el número del nombre es la posición en la lista (indexa list_response)
    assert w.findChild(QPushButton, "btn_f25_2").text() == "Liso"
    assert w.findChild(QPushButton, "btn_g1").text() == "Barco"
    assert w.findChild(QPushButton, "btn_s19").text() == "Sacacorchos"


def test_elegir_lista_cambia_la_grilla():
    w = LW.ListWords(None)
    w.grupo_listas.button(4).click()
    assert w.paginas.currentIndex() == 4
    assert w.paginas.currentWidget().findChild(QPushButton, "btn_h1").text() == "Sol"


def test_la_palabra_dictada_se_atenua_y_el_dictado_se_avisa():
    w = LW.ListWords(None)
    btn = w.findChild(QPushButton, "btn_l3")
    w._marcar_usada(btn)
    assert btn.property("usada") == "true"
    w._limpiar_usadas()
    assert not btn.property("usada")
    w._mostrar_dictado(True, 40)
    assert "40 dB" in w.lbl_dictado.text()
    w._mostrar_dictado(False)
    assert "Sin dictado" in w.lbl_dictado.text()
