"""Los exámenes que trae el paciente salen como informe: encabezado,
gráfico, conclusión y firma (core/informe_previo.py).

- la conclusión dice lo que muestra la hoja, con el grado BIAP del proyecto
  y el tipo por la diferencia aéreo-óseo;
- la firma es de un tecnólogo médico inventado y no cambia entre corridas;
- la tarjeta del docente lleva su conclusión si la escribió;
- el SVG lo lee Qt (sin <svg> anidados).
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(RAIZ, "src"))
os.chdir(RAIZ)

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from core import ficha, informe_previo as IP  # noqa: E402
from PySide6.QtCore import QByteArray  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402


def _tabla(od, oi):
    return [[a, b] for a, b in zip(od, oi)]


def test_audiometria_grado_y_tipo():
    caso = {"Aerea": _tabla([10] * 9, [40, 40, 45, 50, 55, 60, 65, 70, 70]),
            "Osea": _tabla([5] * 9, [10, 10, 10, 10, 15, 15, 15, 15, 15]),
            "UMD": [{"int": 40, "percentage": 100}, {"int": 85, "percentage": 92}]}
    od, oi = IP.conclusion_audiometria(caso)
    assert od.startswith("OD: Audición dentro de rangos normales") and "100 % a 40 dB HL" in od
    # 500/1k/2k/4k = 45, 50, 55, 65 -> 53,75 moderada; óseo 12,5: de conducción
    assert oi.startswith("OI: Hipoacusia de conducción moderada (promedio 53,8 dB HL)"), oi
    caso["Osea"] = _tabla([5] * 9, [30, 30, 40, 45, 50, 55, 60, 60, 60])
    assert "mixta" not in IP.conclusion_audiometria(caso)[1]
    assert "sensorioneural moderada" in IP.conclusion_audiometria(caso)[1]
    caso["Osea"] = _tabla([5] * 9, [20, 20, 25, 30, 35, 40, 45, 45, 45])
    assert "mixta moderada" in IP.conclusion_audiometria(caso)[1]


def test_grados_biap():
    assert [IP.grado(v) for v in (20, 21, 40, 41, 70, 71, 90, 91)] == \
        ["normal", "leve", "leve", "moderada", "moderada", "severa", "severa", "profunda"]


def test_impedancia_y_reflejos():
    caso = {"Z_OD": "A", "Z_OI": "B",
            "Reflex": {"ipsi": [[90, 130], [85, 130], [90, 130], [130, 130]],
                       "contra": [[95, 130], [95, 130], [100, 130], [105, 130]]}}
    od, oi = IP.conclusion_impedancia(caso)
    assert od == ("OD: Timpanograma tipo A; reflejos ipsilaterales presentes en 500 Hz, 1 kHz, "
                  "2 kHz, ausentes en 4 kHz; contralaterales (estímulo en OI) presentes."), od
    assert oi.startswith("OI: Timpanograma tipo B (plana); reflejos ipsilaterales ausentes")
    caso["Z_OI"] = "NR"
    od, oi = IP.conclusion_impedancia(caso)
    assert oi == "OI: No realizable." and "contralaterales" not in od


def test_eoa_peatc_tamizaje():
    assert IP.conclusion_eoa({"OD": (True, True), "OI": (True, False)}) == [
        "OD: Emisiones transitorias y productos de distorsión presentes (pasa).",
        "OI: Emisiones transitorias presentes; productos de distorsión ausentes."]
    lineas = IP.conclusion_peatc({"ABR": {"OD": {}, "OI": {"neural": {"iii_v_ms": 0.8}}}},
                                 [80, 60, 40], {"OD": 25, "OI": None})
    assert lineas[0].startswith("OD: Onda V identificable hasta 40 dB nHL (menor nivel explorado)")
    assert lineas[1].startswith("OI: Sin respuesta identificable a 80 dB nHL")
    assert IP.conclusion_tamizaje("EOA", "Pasa", "pasa") == ["Pasa en ambos oídos."]
    assert IP.conclusion_tamizaje("EOA", "Pasa", "Refiere") == ["OD: Pasa.", "OI: Refiere."]


def test_firma_fija_e_inventada():
    a = IP.firmante("34", "EOA")
    assert a == IP.firmante("34", "EOA")
    assert a[0] in [n for n, _ in IP.TECNOLOGOS]
    assert len({IP.firmante(str(f), "PEATC")[0] for f in range(40)}) > 1   # no firma siempre el mismo


def test_rut_con_digito_verificador():
    assert IP.formato_rut("12345678") == "12.345.678-5"
    assert IP.formato_rut("12.345.678-5") == "12.345.678-5"


def test_la_hoja_la_lee_qt_y_lleva_conclusion_y_firma():
    svg = IP.informe(ficha.tarjeta_previo("EOA", "Pasa", "Refiere", titulo=False), "EOA",
                     {"nombre": "Ana Pérez", "edad": "3 meses", "rut": "12345678", "fecha": "01-11-2026"},
                     ["OD: Pasa.", "OI: Refiere."], IP.firmante("1", "EOA"), prueba="Tamizaje al alta")
    assert "<svg" not in svg[5:], "sin svg anidados: Qt no los dibuja"
    for texto in ("Tamizaje al alta", "Ana Pérez", "12.345.678-5", "Conclusión", "OI: Refiere.", "TM "):
        assert texto in svg, texto
    r = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    assert r.isValid() and r.defaultSize().width() >= IP.ANCHO_MIN


def test_tarjeta_del_docente_con_su_conclusion():
    class Fila:
        nombre, apellido, rut, fecha, case_id = "Luis", "Soto", "19620254", "05-11-26", 7
    previo = {"dias": -30, "prueba": "Retamizaje", "OD": "Pasa", "OI": "Refiere",
              "conclusion": "Refiere OI: se deriva a PEATC."}
    svg = ficha.informe_del_docente({"id": 7}, Fila(), previo, 0)
    assert "Refiere OI: se deriva a PEATC." in svg and "Luis Soto" in svg and "06-10-2026" in svg
    previo["conclusion"] = ""
    assert "OD: Pasa." in ficha.informe_del_docente({"id": 7}, Fila(), previo, 0)


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
