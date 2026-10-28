"""Cabeza giratoria para poner electrodos (core/cabeza_electrodos.py).

Los cuadros y los sitios salen de labyrinthus3d (scripts/cabeza_electrodos/).
Estos tests miran que el paquete esté completo y que el widget gire, elija
el sitio bajo el clic y lleve un electrodo por sitio.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
os.chdir(RAIZ)

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from core import cabeza_electrodos as ce  # noqa: E402
from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402


def test_el_paquete_esta_completo():
    d = ce.datos()
    assert len(d["indice"]) == len(d["yaws"]) * len(d["pitches"])
    for sitio in ("Cz", "Fpz", "Fz", "M1", "M2", "A1", "A2"):
        assert sitio in d["por_id"], sitio
    # De frente se ven Fpz y los dos lóbulos, no el inion.
    fila = d["cuadros"]["0_0"]
    for sitio in ("Fpz", "A1", "A2"):
        assert fila[d["por_id"][sitio]] is not None, sitio
    assert fila[d["por_id"]["Oz"]] is None


def test_cada_cuadro_se_lee():
    c = ce.CabezaElectrodos()
    for clave in ("0_0", "60_180", "-20_358"):
        assert not c._pixmap(clave).isNull(), clave


def test_clic_y_un_electrodo_por_sitio():
    m = ce.MontajeElectrodos()
    m.resize(760, 520)
    m.show()
    m.cabeza.mirar(0, 30)
    sitio, punto = next((s, p) for s, p in m.cabeza._visibles() if s["id"] == "Cz")
    QTest.mouseClick(m.cabeza, Qt.MouseButton.LeftButton, pos=punto.toPoint())
    assert m.colocados == {"activo": "Cz"}
    assert m.rol_actual == "referencia"          # pasa solo al que falta
    QTest.mouseClick(m.cabeza, Qt.MouseButton.LeftButton, pos=punto.toPoint())
    assert m.colocados == {"referencia": "Cz"}   # el sitio queda con uno solo


def test_arrastrar_gira_y_no_pone():
    m = ce.MontajeElectrodos()
    m.resize(760, 520)
    m.show()
    c = m.cabeza
    QTest.mousePress(c, Qt.MouseButton.LeftButton, pos=QPoint(100, 200))
    for x in range(110, 210, 10):
        QTest.mouseMove(c, QPoint(x, 200))
    QTest.mouseRelease(c, Qt.MouseButton.LeftButton, pos=QPoint(200, 200))
    assert c.giro > 30
    assert m.colocados == {}


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
