"""Módulos que se arman después del login (core/subventanas.py).

Armar todos los módulos de examen en el login congelaba la ventana unos
2,6 s. Ahora quedan pendientes y se arman de a uno; si algo pide uno antes
(un clic en su botón), se arma en ese momento.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.subventanas import Subventanas


def _subw():
    armados, despues = [], []
    s = Subventanas({"AGENDA": "agenda"})
    for nombre in ("A", "ABR", "EOAS"):
        s.pendiente(nombre, lambda n=nombre: armados.append(n) or f"frame {n}",
                    lambda frame, n=nombre: despues.append((n, s[n] == frame)))
    return s, armados, despues


def test_pedir_uno_pendiente_lo_arma_una_sola_vez():
    s, armados, despues = _subw()
    assert "ABR" in s and s.get("ABR") is None      # get no arma
    assert s["ABR"] == "frame ABR"
    assert s["ABR"] == "frame ABR"
    assert armados == ["ABR"] and despues == [("ABR", True)]   # despues ya lo ve guardado
    assert s.faltan() == ["A", "EOAS"]


def test_de_a_uno_en_orden_y_todo_de_una():
    s, armados, _ = _subw()
    assert s.construir_siguiente() is True and armados == ["A"]
    s.construir_todo()
    assert armados == ["A", "ABR", "EOAS"] and not s.faltan()
    assert s.construir_siguiente() is False


def test_lo_que_no_existe_sigue_siendo_keyerror():
    s, _, _ = _subw()
    try:
        s["NADA"]
    except KeyError:
        pass
    else:
        raise AssertionError("debía lanzar KeyError")
    assert "NADA" not in s and s.get("NADA", 1) == 1


def test_cancelar_al_cerrar_sesion():
    s, armados, _ = _subw()
    s.cancelar()
    assert not s.faltan() and "ABR" not in s and armados == []


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
