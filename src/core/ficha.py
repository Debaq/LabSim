# -*- coding: utf-8 -*-
"""Ficha clínica del paciente: render HTML compartido entre la agenda
(agenda.Agenda._ver_ficha_paciente) y el historial propio del alumno
(core.mis_pacientes) -- ambos parten de la misma fila de agenda + caso, solo
cambia de dónde sacan `shedule` (en memoria vs. recién pedido al backend)."""

import re

from PySide6.QtCore import QDate, QTime, QDateTime

from core.helpers import obtener_hora_real_atencion

# Llaves {{N}} dentro de historia_clinica (N = offset en días respecto a la
# fecha de la cita, puede ser negativo). Ej.: "{{-5}} atendido por ORL" se
# resuelve a la fecha real 5 días antes de la cita agendada.
HISTORIA_CLINICA_FECHA_RE = re.compile(r"\{\{([+-]?\d+)\}\}")


def parse_fecha_agenda(texto):
    """Parsea una fecha en formato "dd-MM-yy" (año de 2 dígitos, como se
    guarda en la agenda). QDate::fromString con formato "yy" interpreta
    00-99 como 1900-1999, así que corregimos al siglo 2000 manualmente."""
    fecha = QDate.fromString(texto, "dd-MM-yy") if texto else QDate()
    if fecha.isValid() and fecha.year() < 2000:
        fecha = fecha.addYears(100)
    return fecha


def resolver_fechas_historia_clinica(texto, fecha_cita_str):
    """Reemplaza cada {{N}} en texto por la fecha N días respecto a
    fecha_cita_str (formato "dd-MM-yy", mismo que row.fecha). Si la fecha de
    la cita no es válida, deja la llave tal cual (mejor eso que una fecha
    inventada)."""
    if not texto:
        return texto
    fecha_cita = parse_fecha_agenda(fecha_cita_str)

    def _reemplazar(match):
        if not fecha_cita.isValid():
            return match.group(0)
        return fecha_cita.addDays(int(match.group(1))).toString("dd-MM-yyyy")

    return HISTORIA_CLINICA_FECHA_RE.sub(_reemplazar, texto)


def historial_atenciones(shedule, rut, username, is_admin):
    """
    Recopila, para todas las citas (filas de agenda) del mismo paciente (mismo rut),
    las atenciones cerradas por cada alumno, ordenadas cronológicamente.
    Devuelve lista de tuplas (fecha, hora_real, alumno, nota).

    Alumno (is_admin=False): solo ve sus propias notas -- mismo criterio que
    admin/student.php le da al docente sobre cada alumno individual, pero acá
    aplicado a "cada alumno sobre sí mismo".
    """
    historial = []
    for otra_row in shedule.get("agenda_1", {}).values():
        if otra_row.rut != rut:
            continue
        atencion = otra_row.atencion
        fecha = otra_row.fecha
        for alumno, datos in atencion.items():
            if not isinstance(datos, dict) or datos.get("estado") != "atendido":
                continue
            if not is_admin and alumno != username:
                continue
            nota = datos.get("nota", "")
            hora_real = datos.get("hora_real", "")
            historial.append((fecha, hora_real, alumno, nota))

    def _orden(item):
        fecha, hora_real = item[0], item[1]
        dt = QDateTime(
            parse_fecha_agenda(fecha),
            QTime.fromString(hora_real, "HH:mm:ss") if hora_real else QTime(),
        )
        return dt

    historial.sort(key=_orden)
    return historial


def render_ficha_html(row, caso, shedule, username, is_admin):
    """Arma el HTML de la ficha clínica para `row` (AgendaEntry) + `caso`
    (dict del caso clínico) -- datos del paciente, puntualidad de esta cita
    puntual y el historial de atenciones cerradas del paciente."""
    rut = row.rut
    nombre = row.nombre
    apellidos = row.apellido
    fecha_nac = row.fecha_nac
    procedimiento = row.procedimiento
    fecha_hora = f"{row.fecha} {row.hora}".strip()

    partes = ["<h3>Datos del paciente</h3>"]
    partes.append(f"<p><b>Nombre:</b> {nombre} {apellidos}<br>"
                   f"<b>Rut:</b> {rut}<br>"
                   f"<b>Fecha de nacimiento:</b> {fecha_nac}<br>"
                   f"<b>Procedimiento:</b> {procedimiento}<br>"
                   f"<b>Cita agendada:</b> {fecha_hora or 'sin agendar'}</p>")

    hora_real = obtener_hora_real_atencion(row, username)
    if hora_real:
        partes.append("<h3>Puntualidad</h3>")
        hora_agendada = QTime.fromString(row.hora, "HH:mm")
        hora_inicio = QTime.fromString(hora_real, "HH:mm:ss")
        if hora_agendada.isValid() and hora_inicio.isValid():
            minutos = hora_agendada.secsTo(hora_inicio) // 60
            if minutos <= 0:
                resumen = "a tiempo"
            else:
                resumen = f"{minutos} min de atraso"
        else:
            resumen = ""
        partes.append(f"<p><b>Hora agendada:</b> {row.hora}<br>"
                       f"<b>Inicio real:</b> {hora_real} ({resumen})</p>")

    partes.append("<h3>Historial de atenciones</h3>")
    items = ""

    historia_clinica = caso.get("historia_clinica", "") if isinstance(caso, dict) else ""
    if historia_clinica:
        historia_resuelta = resolver_fechas_historia_clinica(historia_clinica, row.fecha)
        items += f"<li><b>Historia clínica:</b> {historia_resuelta}</li>"

    historial = historial_atenciones(shedule, rut, username, is_admin)
    items += "".join(
        f"<li><b>{fecha or 'sin fecha'} {hora}</b> — {alumno}: "
        f"{nota or 'sin comentario'}</li>"
        for fecha, hora, alumno, nota in historial
    )

    if items:
        partes.append(f"<ul>{items}</ul>")
    else:
        partes.append("<p>Sin atenciones cerradas registradas para este paciente.</p>")

    return "".join(partes)
