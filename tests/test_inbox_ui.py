"""Bandeja de entrada: se lee como un correo, sin abrir mensaje por mensaje.

- Al cargar se abre el primer no leído (y queda leído).
- ↑ / ↓ pasan de un mensaje a otro.
- "Marcar todo como leído" marca los que quedan, en el servidor también.
- "Sin leer" deja solo los nuevos.
- El contador del botón no consulta la red: usa lo que ya se sabe.
"""
import os
import sys
from datetime import date

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # noqa: E402,F401  (crea el QApplication)
from core import inbox  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

MARCADOS = []
inbox.inbox_marcar_leido = MARCADOS.append


class _Sincrono:
    """hilos.en_fondo sin hilo: corre y avisa en el acto."""
    @staticmethod
    def en_fondo(funcion, *args, listo=None, **_kw):
        r = funcion(*args)
        if listo:
            listo(r)


inbox.hilos = _Sincrono


def _items():
    return [
        {'id': 3, 'remitente': 'OIRS (simulada)', 'asunto': 'Sugerencia', 'cuerpo': 'a',
         'leido': 1, 'created_at': '2026-10-27 10:00:00'},
        {'id': 2, 'remitente': 'Docente', 'asunto': 'Ficha', 'cuerpo': 'b',
         'leido': 0, 'created_at': '2026-10-26 10:00:00'},
        {'id': 1, 'remitente': 'Sistema', 'asunto': 'Hola', 'cuerpo': 'c',
         'leido': 0, 'created_at': '2026-01-02 10:00:00'},
    ]


def _bandeja():
    MARCADOS.clear()
    w = inbox.InboxWidget(None)
    w._cargar(_items())
    return w


def test_fechas_cortas():
    hoy = date(2026, 10, 27)
    assert inbox.fecha_corta('2026-10-27 14:32:05', hoy) == '14:32'
    assert inbox.fecha_corta('2026-10-26 09:00:00', hoy) == 'ayer'
    assert inbox.fecha_corta('2026-10-12 09:00:00', hoy) == '12 oct'
    assert inbox.fecha_corta('2025-12-01 09:00:00', hoy) == '1 dic 2025'
    assert inbox.fecha_corta('basura', hoy) == 'basura'


def test_abre_el_primer_no_leido():
    w = _bandeja()
    assert w._actual.it['id'] == 2
    assert MARCADOS == [2]
    assert w._no_leidos() == 1


def test_flechas():
    w = _bandeja()
    QTest.keyClick(w, Qt.Key.Key_Down)
    assert w._actual.it['id'] == 1 and MARCADOS == [2, 1]
    QTest.keyClick(w, Qt.Key.Key_Down)          # ya en el último: se queda
    assert w._actual.it['id'] == 1
    QTest.keyClick(w, Qt.Key.Key_Up)
    QTest.keyClick(w, Qt.Key.Key_Up)
    assert w._actual.it['id'] == 3


def test_marcar_todo():
    w = _bandeja()
    assert w.btn_todo_leido.isEnabled()
    w.marcar_todo_leido()
    assert MARCADOS == [2, 1]
    assert w._no_leidos() == 0 and not w.btn_todo_leido.isEnabled()


def test_solo_sin_leer():
    w = _bandeja()                      # el 2 ya quedó leído al abrirlo
    w.btn_sin_leer.click()
    assert [f.it['id'] for f in w._filas] == [1]
    w.marcar_todo_leido()
    w.btn_sin_leer.click()
    assert w._filas == [] and not w.vacio.isHidden()


def test_contador_sin_red():
    class Ventana:
        pass
    v = Ventana()
    llamadas = []
    inbox.inbox_list = lambda: llamadas.append(1) or []
    inbox.actualizar_badge(v)           # sin dato: no pregunta, no hace nada
    assert llamadas == [] and not hasattr(v, '_inbox_no_leidos')
    inbox.actualizar_badge(v, no_leidos=3)
    assert v._inbox_no_leidos == 3


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print(f"  {nombre} OK")
    print("TODOS LOS TESTS PASARON")
