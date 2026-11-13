"""Feedback al feedback en "Mis pacientes" (core/mis_pacientes.py).

Bajo cada comentario del docente sobre la atención va el hilo y una caja
para responderle. La respuesta sale en segundo plano; si falla, el texto
queda en la caja y se avisa (no se pierde lo escrito).
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # noqa: E402,F401  crea la QApplication
from core import mis_pacientes as mp  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402


class _Sincrono:
    """hilos.en_fondo sin hilo: corre y avisa en el acto (o falla)."""
    @staticmethod
    def en_fondo(funcion, *args, listo=None, fallo=None, **_kw):
        try:
            r = funcion(*args)
        except Exception as exc:  # noqa: BLE001
            if fallo:
                fallo(exc)
            return
        if listo:
            listo(r)


def _comentario(**extra):
    c = {"id": 41, "teacher_name": "Nicolás", "created_at": "2026-11-12 18:00:00",
         "comment": "Faltó enmascarar el OD.", "respuestas": [], "responder": True}
    c.update(extra)
    return c


def _textos(hilo):
    return [w.text() for w in hilo.findChildren(mp.QLabel) if w.isVisibleTo(hilo)]


def test_responder_agrega_al_hilo_y_vacia_la_caja():
    mp.hilos = _Sincrono
    enviados = []

    def responder(cid, texto):
        enviados.append((cid, texto))
        return [{"id": 1, "autor": "alumno", "author_name": "Alumna", "texto": texto,
                 "created_at": "2026-11-12 19:00:00", "leido": False}]

    mp.responder_comentario = responder
    c = _comentario()
    hilo = mp._HiloComentario(c)
    hilo.texto.setPlainText("  Entendí: la próxima vez enmascaro antes de subir a 100.  ")
    QTest.mouseClick(hilo.btn, Qt.MouseButton.LeftButton)
    assert enviados == [(41, "Entendí: la próxima vez enmascaro antes de subir a 100.")]
    assert hilo.texto.toPlainText() == ""
    assert c["respuestas"][0]["texto"].startswith("Entendí")   # queda en el dict de la lista
    assert any("Entendí" in t for t in _textos(hilo))


def test_caja_vacia_no_envia():
    mp.hilos = _Sincrono
    enviados = []
    mp.responder_comentario = lambda cid, t: enviados.append(t) or []
    hilo = mp._HiloComentario(_comentario())
    hilo.texto.setPlainText("   \n ")
    QTest.mouseClick(hilo.btn, Qt.MouseButton.LeftButton)
    assert enviados == []


def test_sin_red_conserva_el_texto_y_avisa():
    mp.hilos = _Sincrono

    def sin_red(cid, texto):
        raise OSError("sin conexión")

    mp.responder_comentario = sin_red
    hilo = mp._HiloComentario(_comentario())
    hilo.texto.setPlainText("Mi respuesta")
    QTest.mouseClick(hilo.btn, Qt.MouseButton.LeftButton)
    assert hilo.texto.toPlainText() == "Mi respuesta"
    assert hilo.btn.isEnabled()
    assert not hilo.aviso.isHidden()


def test_hilo_con_respuesta_del_docente_y_servidor_sin_tabla():
    respuestas = [
        {"id": 1, "autor": "alumno", "author_name": "Alumna", "texto": "¿Por qué masking?",
         "created_at": "2026-11-12 19:00:00", "leido": True},
        {"id": 2, "autor": "docente", "author_name": "Nicolás", "texto": "Por la curva sombra.",
         "created_at": "2026-11-12 19:05:00", "leido": False},
    ]
    hilo = mp._HiloComentario(_comentario(respuestas=respuestas, responder=False))
    textos = _textos(hilo)
    assert "¿Por qué masking?" in textos and "Por la curva sombra." in textos
    assert not hasattr(hilo, "btn")      # sin la tabla en el servidor: solo lectura


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
