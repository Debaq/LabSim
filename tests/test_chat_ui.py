"""
Chat con el paciente (agenda/ChatPaciente.py): cómo se ve y cómo se porta.

Antes era un QTextEdit con tablas HTML: las burbujas no se redondeaban, el
ancho máximo no lo respetaba nadie y a 480x280 no se podía leer. Ahora son
widgets, y estos tests cubren lo que se rompió o podía romperse al cambiarlo:
ancho de las burbujas con la ventana, palabras larguísimas, scroll al último
mensaje, cambio de paciente, reintentos y respuesta que llega tarde.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.base import context  # crea la QApplication
import agenda.ChatPaciente as C

SALA = [
    {"id": "p1", "nombre": "Juan", "rol": "paciente", "etiqueta": "Juan", "es_paciente": True, "informante": False},
    {"id": "p2", "nombre": "Rosa", "rol": "madre", "etiqueta": "Rosa (Madre)", "es_paciente": False, "informante": True},
]


def _sincrono(fn, *args, dueno=None, listo=None, fallo=None, nombre=None, **kw):
    """hilos.en_fondo sin hilo: el resultado llega en el acto."""
    try:
        r = fn(*args)
    except Exception as exc:  # noqa: BLE001
        if fallo:
            fallo(exc)
        return None
    if listo:
        listo(r)
    return None


def _chat(respuesta=None, ancho=520, alto=560):
    C.hilos.en_fondo = _sincrono
    C.sala_del_caso = lambda *a, **k: SALA
    C.foto_paciente = lambda *a, **k: None
    C.chat_con_paciente = respuesta or (lambda *a, **k: {
        "sala": SALA, "respuestas": [{"persona_id": "p1", "etiqueta": "Juan", "texto": "Hola"}]})
    w = C.ChatPacienteWidget("Ana Alumna")
    w.set_paciente("c1", "Juan Pérez", 67, "Audiometría", 5)
    w.resize(ancho, alto)
    w.show()
    context.app.processEvents()
    return w


def _filas(w):
    return [w.lista.fila.itemAt(i).widget() for i in range(w.lista.fila.count())
            if w.lista.fila.itemAt(i).widget() is not None and w.lista.fila.itemAt(i).widget() is not w.vacio]


def test_arranca_vacio_con_el_aviso():
    w = _chat()
    # set_paciente pide la sala en el acto y el chat sigue vacío
    assert w.vacio.isVisibleTo(w) and not _filas(w)


def test_enviar_agrega_las_dos_burbujas_y_devuelve_el_foco():
    w = _chat()
    w.input.setText("Buenos días")
    w._enviar()
    assert len(_filas(w)) == 2, len(_filas(w))
    assert not w.vacio.isVisibleTo(w)
    assert w.input.isEnabled() and w.btn_enviar.isEnabled()
    assert w._history[0] == {"role": "user", "content": "Buenos días"}


def test_las_burbujas_se_achican_con_la_ventana():
    w = _chat(ancho=520)
    largo = "palabra " * 60
    w._burbuja_usuario(largo)
    context.app.processEvents()
    burbuja = w.lista._burbujas[0]
    ancho_grande = burbuja.width()
    w.resize(320, 560)
    context.app.processEvents()
    assert burbuja.width() < ancho_grande, (burbuja.width(), ancho_grande)
    assert burbuja.width() <= w.lista.viewport().width() * C.FRACCION_BURBUJA + 1


def test_una_palabra_larguisima_no_se_sale_de_la_burbuja():
    w = _chat(ancho=360)
    w._burbuja_persona("p1", "Juan", "x" * 300)
    context.app.processEvents()
    burbuja = w.lista._burbujas[0]
    assert burbuja.cuerpo.height() > 3 * burbuja.cuerpo.fontMetrics().height(), "no se partió"
    assert burbuja.width() <= w.lista.viewport().width()


def test_sin_hueco_bajo_el_ultimo_mensaje():
    """Un QLabel que parte líneas pide el alto de su peor caso: la lista
    quedaba con scroll y un hueco debajo del último mensaje."""
    w = _chat()
    for _ in range(3):
        w._burbuja_usuario("Pregunta corta")
        w._burbuja_persona("p1", "Juan", "Una respuesta de largo medio para que ocupe un par de líneas "
                                          "dentro de la burbuja y se vea cómo se acomoda.")
    context.app.processEvents()
    barra = w.lista.verticalScrollBar()
    contenido = w.lista.contenido
    ultimo = _filas(w)[-1]
    sobrante = contenido.height() - (ultimo.geometry().bottom() + w.lista.fila.contentsMargins().bottom())
    assert sobrante < 30 or barra.maximum() == 0 or sobrante < w.lista.viewport().height(), sobrante
    assert barra.maximum() == 0 or barra.value() == barra.maximum()


def test_conversacion_larga_queda_pegada_al_final():
    w = _chat(ancho=360, alto=440)
    for i in range(40):
        w._burbuja_usuario(f"Pregunta {i}")
        w._burbuja_persona("p1", "Juan", "Respuesta " * 12)
    for _ in range(3):   # el layout se termina de calcular en la vuelta siguiente
        context.app.processEvents()
    barra = w.lista.verticalScrollBar()
    assert barra.maximum() > 0 and barra.value() == barra.maximum()


def test_cambiar_de_paciente_limpia_la_conversacion():
    w = _chat()
    w._burbuja_usuario("hola")
    w.set_paciente("c2", "María Soto", 30, "ABR", 6)
    context.app.processEvents()
    assert not _filas(w) and w.vacio.isVisibleTo(w)
    assert "María Soto" in w.lbl_paciente.text() or "Juan" in w.lbl_paciente.text()
    w._burbuja_usuario("otra vez")
    assert len(_filas(w)) == 1


def test_con_acompanantes_el_encabezado_los_nombra_y_cada_uno_tiene_su_cara():
    w = _chat()
    w._burbuja_persona("p2", "Rosa (Madre)", "Hace dos años")
    assert "Rosa" in w.lbl_paciente.text()
    assert "p2" in w._caras and "p1" in w._caras


def test_la_foto_que_llega_despues_cambia_la_cara_ya_mostrada():
    from PySide6.QtGui import QColor, QPixmap
    w = _chat()
    w._burbuja_persona("p2", "Rosa (Madre)", "Hola")
    etiqueta, _ = w._etiquetas_cara["p2"][0]
    antes = etiqueta.pixmap().toImage().pixelColor(16, 16).name()
    foto = QPixmap(32, 32)
    foto.fill(QColor("#00ff00"))
    w._set_avatar("p2", foto)
    despues = etiqueta.pixmap().toImage().pixelColor(16, 16).name()
    assert antes != despues and despues == "#00ff00", (antes, despues)


def test_un_fallo_reintenta_solo_una_vez_y_despues_ofrece_reintentar():
    llamadas = []

    def falla(*a, **k):
        llamadas.append(1)
        raise RuntimeError("sin red")

    w = _chat(respuesta=falla)
    w.REINTENTOS_AUTOMATICOS = 0   # sin esperar el temporizador de 1,5 s
    w.input.setText("¿Escucha bien?")
    w._enviar()
    assert len(llamadas) == 1
    assert w.btn_reintentar.isVisibleTo(w) and w.lbl_estado.text().startswith("No hubo respuesta")
    assert w.input.isEnabled()
    assert len(_filas(w)) == 1     # solo la burbuja del alumno, no se duplica al reintentar
    w._reintentar_manual()
    assert len(llamadas) == 2 and len(_filas(w)) == 1


def test_una_respuesta_de_otro_paciente_se_descarta():
    w = _chat()
    w._on_respuesta("otro_caso", "hola", {"respuestas": [{"persona_id": "p1", "etiqueta": "Juan", "texto": "x"}]})
    assert not _filas(w)


def test_el_texto_del_modelo_no_se_interpreta_como_html():
    w = _chat()
    w._burbuja_persona("p1", "Juan", "<b>negrita</b> <img src='x'> y <script>")
    cuerpo = w.lista._burbujas[0].cuerpo
    assert "<b>" in cuerpo.text() and cuerpo.textFormat() == C.Qt.TextFormat.PlainText


def test_tamanos_de_pantalla_chicos_no_rompen_nada():
    for ancho, alto in ((520, 560), (480, 400), (360, 320), (300, 260)):
        w = _chat(ancho=ancho, alto=alto)
        for i in range(6):
            w._burbuja_usuario("¿Desde cuándo lo nota? " * (i + 1))
            w._burbuja_persona("p2" if i % 2 else "p1", "Rosa (Madre)" if i % 2 else "Juan", "Hace un tiempo " * (i + 1))
        context.app.processEvents()
        for b in w.lista._burbujas:
            assert b.width() <= w.lista.viewport().width(), (ancho, alto, b.width())
        w.close()


def test_el_paciente_entrega_sus_informes_en_el_chat():
    """Lo que el backend marca como entregado sale como papeles en la
    conversación y avisa (main lo pone en la ficha). Solo lo que trae."""
    w = _chat(lambda *a, **k: {"sala": SALA, "entrega": ["Audiometría", "VEMP"],
                               "respuestas": [{"persona_id": "p1", "etiqueta": "Juan", "texto": "Tome."}]})
    w.set_paciente("c1", "Juan Pérez", 67, "PEATC", 5, ["Audiometría", "Impedanciometría"])
    avisos = []
    w.entrego.connect(lambda caso, examenes: avisos.append((caso, examenes)))
    w.input.setText("¿Me muestra los exámenes que trae?")
    w._enviar()
    assert avisos == [("c1", ["Audiometría"])], avisos
    papeles = _filas(w)[-1].findChild(C.QFrame, "papelesChat")
    assert papeles is not None
    assert [b.text() for b in papeles.findChildren(C.BotonAccion)] == ["Audiometría"]


if __name__ == "__main__":
    pruebas = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    fallos = 0
    for nombre, fn in pruebas:
        try:
            fn()
            print("ok  ", nombre)
        except Exception as exc:  # noqa: BLE001
            fallos += 1
            import traceback
            traceback.print_exc()
            print("FAIL", nombre, repr(exc))
    sys.exit(1 if fallos else 0)
