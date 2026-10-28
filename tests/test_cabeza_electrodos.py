"""Montaje de electrodos sobre la cabeza giratoria (core/cabeza_electrodos.py).

Las fotos, la piel (malla) y los sitios salen de labyrinthus3d
(scripts/cabeza_electrodos/). Estos tests miran:

- que la cámara de LabSim es la de las fotos (proyectar y tocar la piel
  calzan con lo que guardó cada cuadro);
- que se frota una zona y no un punto, y que lo que baja la impedancia es
  lo que cubrió el lugar donde quedó el electrodo;
- que alcohol, gel, ida y vuelta e irritación hacen lo que dice la práctica;
- que los electrodos van donde se hace clic, uno por lugar, y que 1 y 2
  canales llevan sus cables de lado.
"""
import os
import random
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
os.chdir(RAIZ)

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from core import cabeza_electrodos as ce  # noqa: E402
import numpy as np  # noqa: E402
from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402


def _sitio(sid):
    d = ce.datos()
    i = d["por_id"][sid]
    return d["pos"][i], d["normales"][i]


def _montaje(semilla=4):
    m = ce.MontajeElectrodos(rng=random.Random(semilla))
    m.resize(840, 600)
    m.show()
    return m


def _en_pantalla(m, sid):
    return m.cabeza.en_pantalla(*_sitio(sid)).toPoint()


def _frotar(m, centro, herramienta, ida_y_vuelta=False, dx=36):
    """Una pasada de verdad con el mouse, centrada en `centro`."""
    c = m.cabeza
    m.elegir_herramienta(herramienta)
    p0 = centro - QPoint(dx // 2, 0)
    pasos = [p0 + QPoint(dx * k // 10, 0) for k in range(1, 11)]
    if ida_y_vuelta:
        pasos += [p0 + QPoint(dx * k // 10, 0) for k in range(9, -1, -1)]
    QTest.mousePress(c, Qt.MouseButton.LeftButton, pos=p0)
    for q in pasos:
        QTest.mouseMove(c, q)
    QTest.mouseRelease(c, Qt.MouseButton.LeftButton, pos=pasos[-1])


def _linea(punto, largo=0.03, n=12, eje=(1.0, 0.0, 0.0)):
    """Puntos de una pasada recta que cruza `punto` (para la Piel sola)."""
    eje = np.asarray(eje)
    return np.array([punto + eje * (k / (n - 1) - 0.5) * largo for k in range(n)])


# ---------------------------------------------------------------- geometría

def test_el_paquete_esta_completo():
    d = ce.datos()
    assert len(d["indice"]) == len(d["yaws"]) * len(d["pitches"])
    for sitio in ("Cz", "Fpz", "Fz", "M1", "M2", "A1", "A2"):
        assert sitio in d["por_id"], sitio
    fila = d["cuadros"]["0_0"]
    for sitio in ("Fpz", "A1", "A2"):
        assert fila[d["por_id"][sitio]] is not None, sitio
    assert fila[d["por_id"]["Oz"]] is None


def test_la_camara_es_la_de_las_fotos():
    """Proyectar el punto 3D de un sitio cae donde la foto lo guardó, y
    tocar ese pixel vuelve a la piel junto al sitio. Lo de tocar, solo en
    los sitios que se ven de frente: uno de canto queda 1 mm sobre la piel y
    el rayo rasante pasa por encima (en three.js también)."""
    g, d = ce.geometria(), ce.datos()
    for clave in ("0_0", "30_20", "-20_90", "60_180", "10_270"):
        p, y = map(int, clave.split("_"))
        px, vis = g.proyectar(d["pos"], d["normales"], p, y)
        r = g.rotacion(p, y)
        for i, xy in enumerate(d["cuadros"][clave]):
            if xy is None:
                continue
            assert vis[i] and np.hypot(*(px[i] - xy)) < 0.5, (clave, i)
            mundo = r @ d["pos"][i]
            hacia_camara = (g.ojo - mundo) / np.linalg.norm(g.ojo - mundo)
            if (r @ d["normales"][i]) @ hacia_camara > 0.5:
                tocado = g.rayo(xy[0], xy[1], p, y)
                assert tocado is not None and np.linalg.norm(tocado[0] - d["pos"][i]) < 0.006, (clave, i)


def test_cada_cuadro_se_lee():
    c = ce.CabezaElectrodos()
    for clave in ("0_0", "60_180", "-20_358"):
        assert not c._pixmap(clave).isNull(), clave


# ---------------------------------------------------------------- la piel

def test_sin_preparar_ninguno_queda_en_norma():
    piel = ce.Piel(random.Random(1))
    for sid in ("Cz", "Fpz", "M2", "A1"):
        assert piel.impedancia(_sitio(sid)[0]) > ce.limites()[0], sid


def test_alcohol_y_gel_bajan_donde_se_paso():
    piel = ce.Piel(random.Random(1))
    cz, n = _sitio("Cz")
    sin = piel.impedancia(cz)
    for _ in range(2):
        piel.pasada("alcohol", _linea(cz), [n] * 12)
    assert abs(piel.impedancia(cz) - sin * ce.ALCOHOL_FACTOR[2]) < 1e-9
    for _ in range(8):
        piel.pasada("gel", _linea(cz), [n] * 12)
    assert piel.impedancia(cz) < ce.limites()[0]
    # 2 cm al lado no se limpió nada: sigue como estaba.
    al_lado = cz + np.array([0.0, 0.0, 0.02])
    assert piel.pasadas(al_lado) == (0, 0, 0)
    assert piel.errores == []


def test_gel_sin_alcohol_rinde_menos():
    con, sin = ce.Piel(random.Random(3)), ce.Piel(random.Random(3))
    fpz, n = _sitio("Fpz")
    con.pasada("alcohol", _linea(fpz), [n] * 12)
    for _ in range(5):
        con.pasada("gel", _linea(fpz), [n] * 12)
        sin.pasada("gel", _linea(fpz), [n] * 12)
    assert sin.impedancia(fpz) > con.impedancia(fpz) / ce.ALCOHOL_FACTOR[1]
    assert ("gel_sin_alcohol", "Fpz") in sin.errores


def test_al_reves_es_ida_y_vuelta_y_de_mas_irrita():
    piel = ce.Piel(random.Random(2))
    cz, n = _sitio("Cz")
    piel.pasada("alcohol", _linea(cz), [n] * 12)
    piel.pasada("gel", _linea(cz), [n] * 12)
    piel.pasada("gel", _linea(cz)[::-1], [n] * 12)       # al revés que la anterior
    assert piel.pasadas(cz)[2] == 1
    for _ in range(ce.GEL_MAX_PASADAS):
        piel.pasada("gel", _linea(cz), [n] * 12)
    assert piel.irritada(cz) and piel.resumen(cz) == "piel irritada"
    assert ("piel_irritada", "Cz") in piel.errores
    assert piel.impedancia(cz) >= piel.piso["Cz"]


# ---------------------------------------------------------------- con el mouse

def test_frotar_con_el_mouse_limpia_una_zona():
    m = _montaje()
    m.cabeza.mirar(0, 60)
    cz = _en_pantalla(m, "Cz")
    _frotar(m, cz, "alcohol")
    _frotar(m, cz, "gel")
    _frotar(m, cz, "gel", ida_y_vuelta=True)
    piel = m.impedancias.piel
    assert len(piel.trazos) == 3 and m.cabeza.giro == 0     # frotar no gira
    assert piel.pasadas(_sitio("Cz")[0]) == (1, 1.5, 1)


def test_el_electrodo_va_donde_se_hace_clic():
    m = _montaje()
    m.elegir_herramienta("electrodo")
    m.cabeza.mirar(0, 0)
    fpz = _en_pantalla(m, "Fpz")
    QTest.mouseClick(m.cabeza, Qt.MouseButton.LeftButton, pos=fpz)
    QTest.mouseClick(m.cabeza, Qt.MouseButton.LeftButton, pos=fpz + QPoint(30, 0))
    montaje = m.montaje()
    assert montaje["activo"]["sitio"] == "Fpz" and montaje["activo"]["distancia_mm"] < 3
    assert montaje["referencia"]["distancia_mm"] > 5        # libre: no salta a un punto
    assert ("electrodo_sin_preparar", "Fpz") in m.errores


def test_con_el_electrodo_puesto_no_se_frota():
    m = _montaje()
    m.cabeza.mirar(0, 60)
    m.poner_en_sitio("Cz")
    _frotar(m, _en_pantalla(m, "Cz"), "gel")
    assert m.impedancias.piel.trazos == []
    m._quitar("activo")
    _frotar(m, _en_pantalla(m, "Cz"), "gel")
    assert len(m.impedancias.piel.trazos) == 1


def test_un_electrodo_por_lugar_y_medir():
    m = _montaje()
    m.poner_en_sitio("Cz")
    assert m.rol_actual == "referencia"                     # pasa solo al que falta
    m.poner_en_sitio("Cz")
    assert list(m.colocados) == ["referencia"]              # el nuevo saca al otro
    m.poner_en_sitio("M2")
    m.poner_en_sitio("Fpz")
    assert m.impedancias.informe() is None                  # todavía sin medir
    m.medir()
    assert set(m.impedancias.medido) == set(m.colocados)


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
    m = _montaje(2)
    m.poner_en_sitio("Cz")
    m.poner_en_sitio("M1")                                  # mastoides izquierda
    z_ref = m.impedancias.z["referencia"]
    m.poner_canales(2)
    # Dos canales: cables de lado. La referencia puesta queda como la de su lado.
    assert set(m.colocados) == {"activo", "ref_izq"}
    assert m.impedancias.z["ref_izq"] == z_ref
    assert m.rol_actual == "ref_der"
    assert not m.botones_rol["ref_der"].isHidden() and m.botones_rol["referencia"].isHidden()
    m.poner_en_sitio("M2")
    m.poner_en_sitio("Fpz")
    assert {r: v["sitio"] for r, v in m.montaje().items()} == \
        {"activo": "Cz", "ref_izq": "M1", "ref_der": "M2", "tierra": "Fpz"}
    m.poner_canales(1)
    # Vuelve a una referencia (la derecha); la izquierda se saca.
    assert {r: v["sitio"] for r, v in m.montaje().items()} == \
        {"activo": "Cz", "referencia": "M2", "tierra": "Fpz"}


def test_ver_puntos():
    m = _montaje()
    m.poner_en_sitio("Cz")
    assert m.lbl_puesto["activo"].text() == "puesto"
    m.btn_ver_puntos.setChecked(True)
    assert m.cabeza.ver_puntos and m.lbl_puesto["activo"].text().startswith("Cz")


def test_colores_de_los_cables():
    assert ce.COLOR_ROL["ref_der"] == ce.tema.OD and ce.COLOR_ROL["ref_izq"] == ce.tema.OI
    assert ce.COLOR_ROL["activo"].upper() == "#FFFFFF"


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
