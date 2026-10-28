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


def test_impedancias_se_ven_al_medir_y_bajan_al_limpiar():
    import random
    m = ce.MontajeElectrodos(rng=random.Random(4))
    for sitio in ("Cz", "M2", "Fpz"):
        m._poner(sitio)
    assert m.impedancias.informe() is None            # todavía sin medir
    m.medir()
    antes = dict(m.impedancias.medido)
    assert set(antes) == {"activo", "referencia", "tierra"}
    m.limpiar_piel("activo")
    assert "activo" not in m.impedancias.medido        # cambió: hay que volver a medir
    assert m.impedancias.informe() is None
    m.medir()
    assert m.impedancias.medido["activo"] < antes["activo"]


def test_limpiar_tiene_piso_y_el_cuero_cabelludo_da_mas():
    import random
    imp = ce.Impedancias(random.Random(1))
    altos = []
    for semilla in range(40):
        imp.rng = random.Random(semilla)
        imp.poner("activo", "Cz")
        imp.poner("tierra", "Fpz")
        altos.append(imp.z["activo"] > imp.z["tierra"])
        for _ in range(12):
            imp.limpiar("activo")
        assert imp.z["activo"] >= ce.PISO_KOHM[0]
    assert sum(altos) > 30      # el vértex con pelo casi siempre sale más alto


def test_en_norma_con_los_limites_del_abr():
    from abr.ABR_generator import IMPEDANCE_BALANCE_LIMIT_KOHM, IMPEDANCE_LIMIT_KOHM
    imp = ce.Impedancias()
    imp.z = {"activo": IMPEDANCE_LIMIT_KOHM - 0.1, "referencia": 3.5, "tierra": 3.5}
    imp.medir()
    assert imp.informe()[2]
    imp.z["referencia"] = IMPEDANCE_LIMIT_KOHM - 0.1 - IMPEDANCE_BALANCE_LIMIT_KOHM - 0.5
    imp.medir()
    assert not imp.informe()[2]          # todos bajo el límite, pero desbalanceados
    assert imp.estado("activo") == "ok"


def test_uno_y_dos_canales():
    import random
    m = ce.MontajeElectrodos(rng=random.Random(2))
    m._poner("Cz")
    m._poner("M1")                       # mastoides izquierda
    z_ref = m.impedancias.z["referencia"]
    m.poner_canales(2)
    # Dos canales: cables de lado. La referencia puesta queda como la de su lado.
    assert m.colocados == {"activo": "Cz", "ref_izq": "M1"}
    assert m.impedancias.z["ref_izq"] == z_ref
    assert m.rol_actual == "ref_der"
    assert not m.botones_rol["ref_der"].isHidden() and m.botones_rol["referencia"].isHidden()
    m._poner("M2")
    m._poner("Fpz")
    assert m.colocados == {"activo": "Cz", "ref_izq": "M1", "ref_der": "M2", "tierra": "Fpz"}
    m.poner_canales(1)
    # Vuelve a una referencia (la derecha); la izquierda se saca.
    assert m.colocados == {"activo": "Cz", "referencia": "M2", "tierra": "Fpz"}
    assert set(m.impedancias.z) == {"activo", "referencia", "tierra"}


def test_colores_de_los_cables():
    assert ce.COLOR_ROL["ref_der"] == ce.tema.OD and ce.COLOR_ROL["ref_izq"] == ce.tema.OI
    assert ce.COLOR_ROL["activo"].upper() == "#FFFFFF"
    assert "ref_ipsi" not in ce.COLOR_ROL and "ref_contra" not in ce.COLOR_ROL


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
