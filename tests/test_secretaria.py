"""Karime, la secretaria (core/secretaria.py): avisos emergentes dentro del
MDI durante la atención, para apurar al alumno.

Se prueba qué paciente nombra (una cita real pendiente del mismo día, nunca
uno inventado), los minutos por curso sobre el default, y el ciclo del
aviso: aparece dentro del MDI, se cancela al cerrar la atención y se va
solo.
"""

import os
import random
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMdiArea

from core.base import context  # crea la QApplication
from core import secretaria as sec
from backend.shedule_sync import AgendaEntry

APP = context.app


def _cita(hora, nombre="Ana", apellido="Rojas", fecha="07-10-26", **kw):
    return AgendaEntry(fecha=fecha, hora=hora, nombre=nombre, apellido=apellido, **kw)


def _agenda():
    return {
        "1": _cita("09:00", "Juan", "Pérez"),          # la que se atiende
        "2": _cita("10:30", "Rosa", "Muñoz"),
        "3": _cita("09:45", "Luis", "Soto"),
        "4": _cita("08:00", "Ya", "Atendido", atencion={"alumno": {"estado": "atendido"}}),
        "5": _cita("08:30", "Otro", "Día", fecha="08-10-26"),
        "6": AgendaEntry(nombre="Sin", apellido="Cita", sin_cita=True),
    }


def test_siguiente_es_la_pendiente_mas_temprana_del_mismo_dia():
    assert sec.siguiente_paciente(_agenda(), "1", "alumno") == {"nombre": "Luis Soto", "hora": "09:45"}


def test_lo_que_otro_alumno_atendio_no_cuenta_para_este():
    agenda = _agenda()
    agenda["3"].atencion["otro_alumno"] = {"estado": "atendido"}
    assert sec.siguiente_paciente(agenda, "1", "alumno")["nombre"] == "Luis Soto"
    agenda["3"].atencion["alumno"] = {"estado": "no_show"}
    assert sec.siguiente_paciente(agenda, "1", "alumno")["nombre"] == "Rosa Muñoz"


def test_sin_cita_pendiente_no_se_inventa_paciente():
    agenda = {k: v for k, v in _agenda().items() if k in ("1", "4", "5", "6")}
    assert sec.siguiente_paciente(agenda, "1", "alumno") is None
    # un caso sin agendar (prueba del docente) no tiene día: nadie espera
    assert sec.siguiente_paciente(_agenda(), "6", "alumno") is None


def test_en_practica_libre_nadie_espera():
    """Un intento de práctica deliberada (el alumno en su casa) no tiene
    pacientes en la sala de espera, y un intento tampoco es un paciente
    esperando durante un práctico."""
    agenda = _agenda()
    agenda["9"] = _cita("09:05", "Prac", "Tica", practice_id=3)
    assert sec.siguiente_paciente(agenda, "9", "alumno") is None
    agenda["9"].hora = "09:10"
    agenda["3"].atencion["alumno"] = {"estado": "atendido"}
    assert sec.siguiente_paciente(agenda, "1", "alumno")["nombre"] == "Rosa Muñoz"


def test_hora_con_segundos_se_muestra_hh_mm():
    agenda = {"1": _cita("09:00"), "2": _cita("10:30:00", "Rosa", "Muñoz")}
    assert sec.siguiente_paciente(agenda, "1", "alumno")["hora"] == "10:30"


def _minutos(override=None):
    return [a["min"] for a in sec.config_avisos(override)]


def test_textos_nombran_al_siguiente_o_hablan_del_tiempo():
    avisos = sec.config_avisos()
    siguiente = {"nombre": "Luis Soto", "hora": "09:45"}
    for aviso in avisos:
        for _ in range(30):
            texto = sec.texto_aviso(aviso, aviso["min"], siguiente)
            assert "Luis Soto" in texto and "{" not in texto, texto
            sin = sec.texto_aviso(aviso, 30.0, None)
            assert "Luis Soto" not in sin and "{" not in sin, sin


def test_variacion_grande_y_sin_repetir_seguido():
    avisos = sec.config_avisos()
    for aviso in avisos:
        assert len(aviso["con_paciente"]) >= 10 and len(aviso["sin_paciente"]) >= 10
    rng = random.Random(1)
    siguiente = {"nombre": "Luis Soto", "hora": "09:45"}
    anterior, vistas = None, set()
    for _ in range(60):
        texto = sec.texto_aviso(avisos[0], 20, siguiente, rng=rng, evitar=anterior)
        assert texto != anterior
        vistas.add(texto)
        anterior = texto
    assert len(vistas) >= 8


def test_minutos_default_y_override_del_curso():
    assert _minutos() == [20.0, 30.0, 40.0]
    override = {"avisos": {"aviso_2": {"min": 25.0}, "aviso_3": {"min": 0}}}
    assert _minutos(override) == [20.0, 25.0, 0.0]
    assert _minutos({"avisos": {"aviso_1": {"min": "basura"}}})[0] == 20.0


def test_textos_del_curso_reemplazan_al_default():
    override = {"avisos": {"aviso_1": {"con_paciente": ["Llegó {nombre} ({hora}) {sin_cerrar"]}}}
    avisos = sec.config_avisos(override)
    assert avisos[0]["con_paciente"] == ["Llegó {nombre} ({hora}) {sin_cerrar"]
    assert avisos[0]["sin_paciente"] == sec.config_avisos()[0]["sin_paciente"]
    # llave suelta del docente: no revienta, se deja tal cual
    assert sec.texto_aviso(avisos[0], 20, {"nombre": "Rosa", "hora": "10:30"}) == "Llegó Rosa (10:30) {sin_cerrar"
    # lista vacía o con basura: queda el default, el aviso no sale mudo
    vacio = sec.config_avisos({"avisos": {"aviso_1": {"con_paciente": ["  ", 3]}}})
    assert vacio[0]["con_paciente"] == sec.config_avisos()[0]["con_paciente"]


def test_plantilla_sin_dato_disponible_se_descarta():
    aviso = {"min": 20, "con_paciente": [], "sin_paciente": ["{nombre} espera", "Van {minutos} min"]}
    for _ in range(20):
        assert sec.texto_aviso(aviso, 20, None) == "Van 20 min"
    solo_nombre = {"min": 20, "con_paciente": [], "sin_paciente": ["{nombre} espera"]}
    assert sec.texto_aviso(solo_nombre, 20, None) == "Ya van 20 minutos de atención."


class _Parche:
    """Reemplaza atributos y los restaura al salir (sin pytest)."""

    def __init__(self, **cambios):
        self._cambios = cambios

    def __enter__(self):
        self._previos = {}
        for ruta, valor in self._cambios.items():
            obj, attr = ruta.rsplit("__", 1) if "__" in ruta else ("sec", ruta)
            destino = sec if obj == "sec" else getattr(sec, obj)
            self._previos[(destino, attr)] = getattr(destino, attr)
            setattr(destino, attr, valor)

    def __exit__(self, *exc):
        for (destino, attr), valor in self._previos.items():
            setattr(destino, attr, valor)


def _area():
    area = QMdiArea()
    area.resize(900, 600)
    area.show()
    QTest.qWaitForWindowExposed(area)
    return area


def test_aviso_aparece_dentro_del_mdi_y_se_va_solo():
    with _Parche(DURACION_MS=200, FADE_MS=50):
        _aviso_aparece_y_se_va()


def _aviso_aparece_y_se_va():
    area = _area()
    karime = sec.Secretaria(area)
    aviso = karime.avisar("Llegó Luis Soto")
    assert aviso.isVisible()
    assert area.viewport().geometry().contains(aviso.geometry())
    QTest.qWait(500)
    assert karime._avisos == []
    area.close()


def test_iniciar_programa_solo_los_avisos_encendidos_y_detener_los_cancela():
    with _Parche(app_config_store__get=lambda key, default=None: {"avisos": {"aviso_2": {"min": 0}}}):
        _iniciar_y_detener()


def _iniciar_y_detener():
    area = _area()
    karime = sec.Secretaria(area)
    karime.iniciar(None)
    assert [t.interval() for t in karime._timers] == [20 * 60_000, 40 * 60_000]
    karime.avisar("hola")
    karime.detener()
    assert karime._timers == []
    QTest.qWait(sec.FADE_MS + 200)
    assert karime._avisos == []
    area.close()


def test_avisos_simultaneos_se_apilan_sin_taparse():
    area = _area()
    karime = sec.Secretaria(area)
    a = karime.avisar("uno")
    b = karime.avisar("dos")
    assert not a.geometry().intersects(b.geometry())
    assert b.y() > a.y()  # el más nuevo abajo
    karime.detener()
    area.close()


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
