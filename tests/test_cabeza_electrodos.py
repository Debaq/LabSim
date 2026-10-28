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
    m.elegir_herramienta("electrodo")
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


def _montaje(semilla=4):
    import random
    m = ce.MontajeElectrodos(rng=random.Random(semilla))
    m.resize(840, 600)
    m.show()
    return m


def _frotar(m, sitio, herramienta, ida_y_vuelta=False, dx=40):
    """Una pasada de verdad con el mouse sobre el sitio."""
    c = m.cabeza
    m.elegir_herramienta(herramienta)
    p0 = next(p for s, p in c._visibles() if s["id"] == sitio).toPoint()
    pasos = [p0 + QPoint(dx * k // 8, 0) for k in range(1, 9)]
    if ida_y_vuelta:
        pasos += [p0 + QPoint(dx * k // 8, 0) for k in range(7, -1, -1)]
    QTest.mousePress(c, Qt.MouseButton.LeftButton, pos=p0)
    for q in pasos:
        QTest.mouseMove(c, q)
    QTest.mouseRelease(c, Qt.MouseButton.LeftButton, pos=pasos[-1])


def test_las_impedancias_se_ven_al_medir():
    m = _montaje()
    for sitio in ("Cz", "M2", "Fpz"):
        m._poner(sitio)
    assert m.impedancias.informe() is None            # todavía sin medir
    m.medir()
    assert set(m.impedancias.medido) == {"activo", "referencia", "tierra"}
    # Sin preparar la piel ninguno queda en norma, y queda anotado.
    assert all(m.impedancias.estado(r) != "ok" for r in m.impedancias.medido)
    assert ("electrodo_sin_preparar", "Cz") in m.errores


def test_alcohol_y_gel_bajan_la_impedancia():
    piel = ce.Piel(__import__("random").Random(1))
    sin = piel.impedancia("Cz")
    piel.pasada("Cz", "alcohol")
    piel.pasada("Cz", "alcohol")
    con_alcohol = piel.impedancia("Cz")
    assert abs(con_alcohol - sin * ce.ALCOHOL_FACTOR[2]) < 1e-9
    piel.pasada("Cz", "alcohol")                       # más alcohol no baja más
    assert piel.impedancia("Cz") == con_alcohol
    for _ in range(8):
        piel.pasada("Cz", "gel")
    assert piel.impedancia("Cz") < ce.limites()[0]
    assert piel.errores == []


def test_gel_sin_alcohol_rinde_menos():
    import random
    con, sin = ce.Piel(random.Random(3)), ce.Piel(random.Random(3))
    con.pasada("Fpz", "alcohol")
    for _ in range(5):
        con.pasada("Fpz", "gel")
        sin.pasada("Fpz", "gel")
    assert sin.impedancia("Fpz") > con.impedancia("Fpz") / ce.ALCOHOL_FACTOR[1]
    assert ("gel_sin_alcohol", "Fpz") in sin.errores


def test_de_mas_irrita_y_no_baja():
    piel = ce.Piel(__import__("random").Random(2))
    piel.pasada("Cz", "alcohol")
    for _ in range(ce.GEL_MAX_PASADAS):
        piel.pasada("Cz", "gel")
    tope = piel.impedancia("Cz")
    assert "Cz" not in piel.irritada
    piel.pasada("Cz", "gel")
    assert "Cz" in piel.irritada and piel.impedancia("Cz") == tope
    assert piel.impedancia("Cz") >= piel.piso["Cz"]


def test_la_pasada_con_el_mouse():
    m = _montaje()
    m.cabeza.mirar(0, 20)
    piel = m.impedancias.piel
    _frotar(m, "Cz", "alcohol")
    assert piel.alcohol["Cz"] == 1
    _frotar(m, "Cz", "gel")
    _frotar(m, "Cz", "gel")                            # misma dirección: cuentan enteras
    assert piel.gel["Cz"] == 2.0 and not piel.ida_vuelta.get("Cz")
    _frotar(m, "Cz", "gel", ida_y_vuelta=True)         # frotar como lija: media
    assert piel.gel["Cz"] == 2.5 and piel.ida_vuelta["Cz"] == 1
    _frotar(m, "Cz", "gel", dx=-40)                    # al revés que la anterior
    assert piel.ida_vuelta["Cz"] == 2
    assert m.cabeza.giro == 0                          # frotar no gira la cabeza


def test_con_el_electrodo_puesto_no_se_frota():
    m = _montaje()
    m.cabeza.mirar(0, 20)
    m._poner("Cz")
    _frotar(m, "Cz", "gel")
    assert not m.impedancias.piel.gel.get("Cz")
    m._quitar("activo")
    _frotar(m, "Cz", "gel")
    assert m.impedancias.piel.gel["Cz"] == 1.0


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
