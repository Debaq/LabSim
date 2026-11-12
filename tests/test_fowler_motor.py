"""Motor del Fowler (audiometria.Fowler): la curva de igual sonoridad de
cada patrón y que la respuesta no dependa del orden en que se prueban los
niveles. Antes, tras la primera igualación en la zona de reclutamiento, el
paciente decía "iguales" a ese mismo nivel del afectado para cualquier
nivel del sano, y el reclutamiento completo nunca igualaba al mismo nivel.

Corre con `python tests/test_fowler_motor.py` (o pytest)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from audiometria.Fowler import FOWLER_PATTERNS, Fowler  # noqa: E402

OD, OI = 0, 1


def motor(th_od, th_oi, patron):
    f = Fowler()
    f.set_th(th_od, th_oi)
    f.set_cut(*FOWLER_PATTERNS[patron])
    return f


def iguales_para(f, ref, ref_es_od=True, hasta=120):
    """Niveles del afectado que el paciente da por iguales al sano en `ref`."""
    out = []
    for est in range(-10, hasta + 1, 5):
        par = (ref, est) if ref_es_od else (est, ref)
        if f.evaluate(*par)[0]:
            out.append(est)
    return out


def test_un_solo_nivel_igual_por_escalon():
    """El bug: OD 5 / OI 25 completo, OI 40 salía igual a OD 25, 45, 65..."""
    for patron in FOWLER_PATTERNS:
        f = motor(5, 25, patron)
        for ref in range(5, 106, 5):
            assert len(iguales_para(f, ref)) <= 1, (patron, ref, iguales_para(f, ref))
    f = motor(5, 25, "complete")
    sanos = [ref for ref in range(5, 106, 5) if f.evaluate(ref, 40)[0]]
    assert len(sanos) <= 1, sanos


def test_sin_estado():
    """Mismas preguntas en otro orden, mismas respuestas."""
    niveles = [(r, e) for r in range(5, 106, 10) for e in range(25, 121, 5)]
    for patron in FOWLER_PATTERNS:
        a = motor(5, 25, patron)
        ida = [a.evaluate(*p) for p in niveles]
        b = motor(5, 25, patron)
        vuelta = [b.evaluate(*p) for p in reversed(niveles)][::-1]
        assert ida == vuelta, patron


def test_sin_reclutamiento_paralelas():
    f = motor(5, 25, "none")
    for ref in (5, 25, 45, 65, 85):
        assert iguales_para(f, ref) == [ref + 20]


def test_parcial_achica_sin_cerrar():
    f = motor(5, 25, "partial")
    assert iguales_para(f, 5) == [25]          # en umbral
    assert iguales_para(f, 85) == [95]         # queda la mitad de la diferencia
    for ref in range(5, 101, 5):
        est = iguales_para(f, ref)[0]
        assert est > ref, (ref, est)           # nunca cierra


def test_completo_iguala_al_mismo_nivel():
    f = motor(5, 25, "complete")
    assert iguales_para(f, 25) == [45]         # todavía paralelas bajo el inicio
    assert iguales_para(f, 65) == [65]
    assert iguales_para(f, 85) == [85]


def test_sobre_reclutamiento_5_db_bajo_el_sano():
    f = motor(5, 25, "over")
    assert iguales_para(f, 85) == [80]
    assert iguales_para(f, 105) == [100]


def test_referencia_oi():
    f = motor(40, 10, "complete")              # OI sano, OD afectado
    assert iguales_para(f, 10, ref_es_od=False) == [40]
    assert iguales_para(f, 90, ref_es_od=False) == [90]


def test_que_oido_suena_mas_fuerte():
    f = motor(5, 25, "complete")
    assert f.evaluate(65, 50)[:2] == (False, OD)   # afectado bajo: el sano más fuerte
    assert f.evaluate(65, 80)[:2] == (False, OI)
    assert f.evaluate(65, 65)[:2] == (True, None)
    assert f.evaluate(30, 20)[:2] == (False, OD)   # afectado bajo su umbral
    assert f.evaluate(0, 20)[:2] == (False, None)  # no oye ninguno


def test_curva_creciente():
    """El afectado nunca baja cuando el sano sube: la escalera se puede
    seguir de abajo hacia arriba."""
    for patron in FOWLER_PATTERNS:
        for th in ((5, 25), (10, 50), (0, 40), (45, 20)):
            f = motor(*th, patron)
            ref0 = min(th)
            vals = [f.igual_a(r) for r in range(ref0, 121)]
            assert all(b >= a for a, b in zip(vals, vals[1:])), (patron, th)


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print("ok", nombre)
