"""Agenda relativa al ingreso del alumno (core/agenda_relativa.py).

El docente pone el orden (hora) y la duración de cada paciente; el horario
del alumno parte en el múltiplo de 5 min siguiente a su primer ingreso del
día (nunca antes de la hora del primero) y suma duraciones. Cada paciente
llega al azar dentro de los 15 min previos a su turno, siempre igual para
el mismo alumno.
"""

import os
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from backend.shedule_sync import AgendaEntry, _appointment_fields, backend_state_to_shedule
from core import agenda_relativa as ar

HOY = "30-11-26"


def _agenda():
    # El caso del docente: 30, 45, 15 y 60 min, todos a "todo el curso".
    return {
        "11": AgendaEntry(fecha=HOY, hora="09:00", nombre="Samuel", duracion_min=30),
        "12": AgendaEntry(fecha=HOY, hora="09:30", nombre="Ana", duracion_min=45),
        "13": AgendaEntry(fecha=HOY, hora="10:15", nombre="Luis", duracion_min=15),
        "14": AgendaEntry(fecha=HOY, hora="10:30", nombre="Rosa", duracion_min=60),
        "20": AgendaEntry(fecha=HOY, hora="12:00", nombre="Fija"),
        "21": AgendaEntry(fecha="01-12-26", hora="09:00", nombre="Mañana", duracion_min=30),
    }


def test_turnos_desde_el_ingreso():
    ag = _agenda()
    ar.calcular(ag, "ana.rojas", datetime(2026, 11, 30, 11, 12, 40), HOY)
    turnos = [(ag[k].turno_inicio.strftime("%H:%M"), ag[k].turno_fin.strftime("%H:%M")) for k in "11 12 13 14".split()]
    assert turnos == [("11:15", "11:45"), ("11:45", "12:30"), ("12:30", "12:45"), ("12:45", "13:45")], turnos
    # Hora fija y otro día: sin turno calculado.
    assert ag["20"].turno_inicio is None and ag["21"].turno_inicio is None
    assert ar.hora_vista(ag["20"]) == "12:00" and ar.hora_vista(ag["12"]) == "11:45"


def test_multiplo_justo_pasa_al_siguiente():
    assert ar.primer_turno(datetime(2026, 11, 30, 11, 15, 0)) == datetime(2026, 11, 30, 11, 20)
    assert ar.primer_turno(datetime(2026, 11, 30, 11, 16, 59)) == datetime(2026, 11, 30, 11, 20)


def test_no_antes_de_la_hora_del_docente():
    ag = _agenda()
    ar.calcular(ag, "x", datetime(2026, 11, 30, 7, 50), HOY)
    assert ag["11"].turno_inicio == datetime(2026, 11, 30, 9, 0)
    assert ag["14"].turno_fin == datetime(2026, 11, 30, 11, 30)


def test_llegada_hasta_15_antes_y_estable():
    ag = _agenda()
    ar.calcular(ag, "ana.rojas", datetime(2026, 11, 30, 11, 12), HOY)
    otra = _agenda()
    ar.calcular(otra, "ana.rojas", datetime(2026, 11, 30, 11, 12), HOY)
    for k in "11 12 13 14".split():
        e = ag[k]
        assert e.turno_inicio - timedelta(minutes=15) <= e.llegada <= e.turno_inicio
        assert e.llegada == otra[k].llegada
    distinto = _agenda()
    ar.calcular(distinto, "otro.alumno", datetime(2026, 11, 30, 11, 12), HOY)
    assert any(distinto[k].llegada != ag[k].llegada for k in "11 12 13 14".split())
    e = ag["12"]
    assert ar.todavia_no_llega(e, e.llegada - timedelta(seconds=1))
    assert not ar.todavia_no_llega(e, e.llegada)


def test_ingreso_del_dia_es_el_primero_de_hoy_en_hora_local():
    ahora_local = datetime(2026, 11, 30, 11, 0)
    def utc(local):
        return local.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    ingresos = [utc(datetime(2026, 11, 29, 20, 0)), utc(datetime(2026, 11, 30, 10, 40)),
                utc(datetime(2026, 11, 30, 9, 5))]
    assert ar.ingreso_del_dia(ingresos, date(2026, 11, 30)) == datetime(2026, 11, 30, 9, 5)
    assert ar.ingreso_del_dia(ingresos[:1], ahora_local.date()) is None


def test_docente_no_recalcula():
    ag = _agenda()
    ar.aplicar(ag, {"role": "admin", "username": "profe"}, datetime(2026, 11, 30, 11, 0))
    assert all(e.turno_inicio is None for e in ag.values())


def test_turno_no_viaja_al_backend():
    ag = _agenda()
    ar.calcular(ag, "x", datetime(2026, 11, 30, 11, 0), HOY)
    campos = _appointment_fields(ag["11"])
    assert campos["hora"] == "09:00" and "turno_inicio" not in campos and "duracion_min" not in campos


def test_duracion_llega_del_sync():
    estado = {"appointments": [{"id": 5, "fecha": HOY, "hora": "09:00", "duracion_min": 30},
                               {"id": 6, "fecha": HOY, "hora": "09:30", "duracion_min": None}]}
    ag = backend_state_to_shedule(estado, 1, "x")["agenda_1"]
    assert ag["5"].duracion_min == 30 and ag["6"].duracion_min is None


def test_agenda_del_alumno_espera_la_llegada():
    """En la tabla: 'Aún no llega' con «Atender» apagado, 'En sala de espera'
    y 'Esperando, atrasado' con «Atender» prendido, sin «No se presentó»."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from core.base import context  # crea la QApplication
    import agenda.Agenda as mod
    app = context.app
    ahora = datetime.now().replace(microsecond=0)
    hoy = ahora.strftime("%d-%m-%y")

    def fila(nombre, llega_en, turno_en, hora):
        e = AgendaEntry(fecha=hoy, hora=hora, nombre=nombre, case_id="c" + nombre, duracion_min=30)
        e.llegada = ahora + timedelta(minutes=llega_en)
        e.turno_inicio = ahora + timedelta(minutes=turno_en)
        e.turno_fin = e.turno_inicio + timedelta(minutes=30)
        return e

    agenda = {"1": fila("Atrasado", -40, -20, "08:00"), "2": fila("Espera", -3, 10, "08:30"),
              "3": fila("Lejos", 30, 40, "09:00")}

    class _Shedule:
        def get(self):
            return {"agenda_1": agenda}

    class _Main:
        data_login = {"user": "alumno", "permission": 444}
        data_current_key = None

    mod.Shedule = _Shedule
    ag = mod.Agenda(444, _Main())
    tarea = ag._shedule_fetch
    if tarea is not None:
        assert tarea.esperar(5000)
        for _ in range(50):
            app.processEvents()
            if ag._shedule_fetch is None:
                break
    claves = dict(ag._claves_relativa())
    assert claves == {"1": "espera_atrasada", "2": "en_espera", "3": "aun_no_llega"}, claves
    keys = ag._visible_keys()
    for key, prendido in (("1", True), ("2", True), ("3", False)):
        ag.tableWidget.selectRow(keys.index(key))
        app.processEvents()
        assert ag.btn_atender.isEnabled() is prendido, key
        assert not ag.btn_no_show.isEnabled(), key
    # La hora que ve el alumno es su turno, no la del docente.
    col_hora = ag.tableWidget.item(keys.index("3"), 2).text()
    assert col_hora == agenda["3"].turno_inicio.strftime("%H:%M"), col_hora


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
            print("ok", nombre)
