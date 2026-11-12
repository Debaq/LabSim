"""Botón junto al número de versión: busca una versión nueva a mano y
lanza el mismo sistema de actualización del arranque. Con una sesión
abierta la cierra antes (sube los informes): instalar reinicia sin guardar."""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import main  # noqa: E402
from core import updater  # noqa: E402

APP = main.context.app
UPDATE = {"tag": "pyinstaller-v9.9.9-rabc", "build_id": "9.9.9-rabc", "mode": "full", "url": "x"}


def _esperar():
    for _ in range(5):
        APP.processEvents()


def _ventana(monkey, respuesta, sesion=False, frozen=True, acepta=True):
    w = main.MainWindow()
    w.show()
    avisos, instalados, logouts = [], [], []
    monkey.append((sys, "frozen", getattr(sys, "frozen", None)))
    sys.frozen = frozen
    w._aviso_update = lambda icono, titulo, texto: avisos.append(texto)
    main.hilos.en_fondo = lambda fn, *a, listo=None, fallo=None, **k: (
        fallo(respuesta) if isinstance(respuesta, Exception) else listo(respuesta))
    main._preguntar_update = lambda update, con_sesion=False, parent=None: (
        avisos.append(f"pregunta con_sesion={con_sesion}") or acepta)
    main._download_and_apply = lambda update, silencioso=False: instalados.append(update)
    if sesion:
        w.data_login = {"user": "alumno"}
        w.logout = lambda: (logouts.append(1), setattr(w, "data_login", None))
    _esperar()
    return w, avisos, instalados, logouts


def _limpiar(monkey):
    for obj, attr, valor in monkey:
        if valor is None:
            delattr(obj, attr)
        else:
            setattr(obj, attr, valor)


def _caso(respuesta, **kw):
    monkey = []
    en_fondo, preguntar, bajar = main.hilos.en_fondo, main._preguntar_update, main._download_and_apply
    try:
        w, avisos, instalados, logouts = _ventana(monkey, respuesta, **kw)
        w.btn_buscar_update.click()
        _esperar()
        return w, avisos, instalados, logouts
    finally:
        main.hilos.en_fondo, main._preguntar_update, main._download_and_apply = en_fondo, preguntar, bajar
        _limpiar(monkey)


def test_boton_junto_a_la_version():
    w = main.MainWindow()
    fila = w.horizontalLayout_4
    assert fila.indexOf(w.btn_buscar_update) == fila.indexOf(w.lbl_title) + 1
    assert w.btn_buscar_update.toolTip() == "Buscar actualizaciones"


def test_desde_el_codigo_fuente_no_busca():
    w, avisos, instalados, _ = _caso(UPDATE, frozen=False)
    assert "código fuente" in avisos[0] and not instalados


def test_al_dia():
    w, avisos, instalados, _ = _caso(None)
    assert "al día" in avisos[0] and not instalados
    assert w.btn_buscar_update.isEnabled()


def test_sin_red_avisa_y_rehabilita_el_boton():
    w, avisos, instalados, _ = _caso(updater.UpdateCheckError("sin red"))
    assert "No se pudo consultar" in avisos[0] and not instalados
    assert w.btn_buscar_update.isEnabled() and not w._buscando_update


def test_hay_version_nueva_sin_sesion_instala():
    w, avisos, instalados, logouts = _caso(UPDATE)
    assert avisos == ["pregunta con_sesion=False"]
    assert instalados == [UPDATE] and not logouts


def test_no_acepta_no_instala():
    w, avisos, instalados, _ = _caso(UPDATE, acepta=False)
    assert not instalados


def test_con_sesion_cierra_sesion_antes_de_instalar():
    w, avisos, instalados, logouts = _caso(UPDATE, sesion=True)
    assert avisos == ["pregunta con_sesion=True"]
    assert logouts == [1] and instalados == [UPDATE]
