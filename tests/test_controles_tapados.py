"""Ningún control de las ventanas de la app queda tapado (2026-11-06).

En Acumetría un QWidget suelto, metido en la pestaña sin layout, quedaba de
640x480 encima del panel y se tragaba todos los clics: los diapasones no
respondían en el práctico y no quedaba nada en el registro. QTest.mouseClick
no lo ve (manda el evento directo al botón). Acá se arma cada ventana, se
recorren sus pestañas y, por cada botón o campo visible, se pregunta qué
widget recibe el clic en su centro, como el mouse. En 1000x680, el tamaño
de los equipos del laboratorio (ver labsim_resolucion_pcs_menor).
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
os.environ.setdefault("LABSIM_DATA_DIR", tempfile.mkdtemp(prefix="labsim-test-"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtWidgets import (QAbstractButton, QAbstractSlider, QAbstractSpinBox, QComboBox,
                               QLineEdit, QPlainTextEdit, QStackedWidget, QTabWidget, QTextEdit,
                               QAbstractScrollArea, QToolBox)
from core.base import context

APP = context.app
from core.h_win import FrameSubMdi  # noqa: E402

LOGIN = {"user": "demo", "name": "Demo", "permission": 444, "modules": None, "prefs": {}}
CONTROLES = (QAbstractButton, QAbstractSlider, QAbstractSpinBox, QComboBox, QLineEdit,
             QPlainTextEdit, QTextEdit)


def fabricas():
    from audiometria.ventana import AudiometriaWindow
    from audiometria.Acumetria import Acumetria
    from audiometria.Otoscopia import Otoscopia
    from audiometria.ventana_ot_ac import OtoscopiaAcumetriaWindow
    from impedanciometria.ventana import ImpedanciometriaWindow
    from abr.AbrMainWindow import AbrMainWindow
    from abr.AabrMainWindow import AabrMainWindow
    from oae.OaeMainWindow import OaeMainWindow
    from vemp.VempMainWindow import VempMainWindow
    from agenda.ChatPaciente import ChatPacienteWidget
    from agenda import Agenda
    from core.ficha import HojaPrevia
    from auth.login import MainLogin
    from core import soporte
    from nasal.equipos import RinomanometriaWindow, RinometriaWindow
    from nasal.CpapWindow import CpapWindow
    from nasal.EspirometriaWindow import EspirometriaWindow
    from nasal.OlfatometriaWindow import OlfatometriaWindow
    from nasal.PolisomnografiaWindow import PolisomnografiaWindow
    from nasal.PrickWindow import PrickWindow
    from nasal.RinoscopiaWindow import RinoscopiaWindow
    return {
        "Audiometría": lambda: AudiometriaWindow(None, comandos=True, listas=True),
        "Acumetría": lambda: Acumetria(None),
        "Otoscopía y diapasones": lambda: OtoscopiaAcumetriaWindow(Otoscopia(None), Acumetria(None)),
        "Otoscopía": lambda: Otoscopia(None),
        "Impedanciometría": lambda: ImpedanciometriaWindow(),
        "ABR": lambda: AbrMainWindow(data_login=LOGIN),
        "AABR": lambda: AabrMainWindow(data_login=LOGIN),
        "EOA": lambda: OaeMainWindow(data_login=LOGIN),
        "VEMP": lambda: VempMainWindow(data_login=LOGIN),
        "Chat paciente": lambda: ChatPacienteWidget("Demo"),
        "Ficha clínica": lambda: Agenda.FichaClinicaWidget(),
        "Evolución": lambda: Agenda.EvolucionWidget(),
        "Hoja previa": lambda: HojaPrevia(),
        "Ingreso": lambda: MainLogin(),
        "Soporte (Configuración)": lambda: soporte.PaginaSoporte(),
        "Rinomanometría": lambda: RinomanometriaWindow(data_login=LOGIN),
        "Rinometría": lambda: RinometriaWindow(data_login=LOGIN),
        "Rinoscopía": lambda: RinoscopiaWindow(data_login=LOGIN),
        "Espirometría": lambda: EspirometriaWindow(data_login=LOGIN),
        "Olfatometría": lambda: OlfatometriaWindow(data_login=LOGIN),
        "Prick": lambda: PrickWindow(data_login=LOGIN),
        "Polisomnografía": lambda: PolisomnografiaWindow(data_login=LOGIN),
        "CPAP": lambda: CpapWindow(data_login=LOGIN),
    }


def _pump():
    for _ in range(4):
        APP.processEvents()


def _ruta(w):
    partes = []
    while w is not None and len(partes) < 5:
        partes.append(f"{type(w).__name__}('{w.objectName()}')")
        w = w.parentWidget()
    return " < ".join(partes)


def _revisar(win, raiz, hallados, contexto):
    vistos = {}
    for tipo in CONTROLES:
        for c in raiz.findChildren(tipo):
            vistos[id(c)] = c
    for c in vistos.values():
        if not c.isVisible() or c.width() < 4 or c.height() < 4:
            continue
        centro = c.rect().center()
        if c.visibleRegion().isEmpty() or not c.visibleRegion().contains(centro):
            continue   # fuera de la vista (scroll) o tapado por su propio padre: no es el caso
        p = c.mapTo(win, centro)
        bajo = win.childAt(p)
        if bajo is c or (bajo is not None and c.isAncestorOf(bajo)):
            continue
        clave = (type(c).__name__, c.objectName(), (c.text() if hasattr(c, "text") else "")[:30])
        if clave in hallados:
            continue
        hallados[clave] = (contexto, _ruta(c), _ruta(bajo) if bajo else None,
                           bajo.geometry().getRect() if bajo else None)


def _paginas(raiz):
    """Recorre pestañas y pilas para que se vean todas las páginas."""
    for tabs in raiz.findChildren(QTabWidget):
        for i in range(tabs.count()):
            yield f"pestaña '{tabs.tabText(i)}'", (lambda t=tabs, i=i: t.setCurrentIndex(i))
    for tb in raiz.findChildren(QToolBox):
        for i in range(tb.count()):
            yield f"toolbox {i}", (lambda t=tb, i=i: t.setCurrentIndex(i))


def escanear(nombre, fabrica, tam):
    w = fabrica()
    marco = FrameSubMdi(w, expand=True)
    marco.resize(*tam)
    marco.show()
    _pump()
    win = marco.window()
    hallados = {}
    _revisar(win, w, hallados, "inicio")
    for ctx, ir in list(_paginas(w)):
        ir()
        _pump()
        _revisar(win, w, hallados, ctx)
    marco.close()
    return hallados



def test_ningun_control_de_las_ventanas_queda_tapado():
    tapados = []
    for nombre, fabrica in fabricas().items():
        for clave, (ctx, ruta, tapa, geo) in escanear(nombre, fabrica, (1000, 680)).items():
            tapados.append(f"{nombre} [{ctx}] {clave}: lo tapa {tapa} {geo}")
    assert not tapados, "\n".join(tapados)


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {nombre}")
            except AssertionError as exc:
                fallas += 1
                print(f"FAIL {nombre}: {exc}")
    sys.exit(1 if fallas else 0)
