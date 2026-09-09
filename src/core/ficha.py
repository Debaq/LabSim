# -*- coding: utf-8 -*-
"""Ficha clínica del paciente: render HTML compartido entre la agenda
(agenda.Agenda._ver_ficha_paciente) y el historial propio del alumno
(core.mis_pacientes) -- ambos parten de la misma fila de agenda + caso, solo
cambia de dónde sacan `shedule` (en memoria vs. recién pedido al backend)."""

import html
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


# Fecha ya resuelta al principio de una línea de la historia clínica.
HISTORIA_LINEA_RE = re.compile(r"^(\d{2}-\d{2}-\d{4})\s*(.*)$", re.S)

# Claves de orden para lo que no trae fecha legible: una línea de la historia
# clínica va al principio (el docente la escribió antes de todo lo demás) y
# una atención sin fecha es la de ahora, así que va al final.
_ORDEN_PRIMERO = QDateTime(QDate(1, 1, 1), QTime(0, 0))
_ORDEN_ULTIMO = QDateTime(QDate(9999, 12, 31), QTime(23, 59))


def linea_tiempo(historia_clinica, fecha_cita, historial):
    """Atenciones previas del caso + atenciones cerradas, en un solo orden.

    Devuelve dicts {fecha, hora, alumno, texto}: `alumno` vacío en las
    entradas que vienen de la historia clínica del caso, que no son de
    nadie en particular.
    """
    entradas = []

    for linea in resolver_fechas_historia_clinica(historia_clinica or "", fecha_cita).splitlines():
        linea = linea.strip()
        if not linea:
            continue
        match = HISTORIA_LINEA_RE.match(linea)
        fecha = match.group(1) if match else ""
        texto = match.group(2).strip() if match else linea
        orden = QDateTime(QDate.fromString(fecha, "dd-MM-yyyy"), QTime(0, 0)) if fecha else None
        entradas.append((orden if orden and orden.isValid() else _ORDEN_PRIMERO,
                         {"fecha": fecha, "hora": "", "alumno": "", "texto": texto}))

    for fecha, hora_real, alumno, nota in historial:
        fecha_q = parse_fecha_agenda(fecha)
        orden = QDateTime(
            fecha_q,
            QTime.fromString(hora_real, "HH:mm:ss") if hora_real else QTime(0, 0),
        )
        # La agenda guarda "dd-MM-yy" y la historia clínica queda en
        # "dd-MM-yyyy": mezclados en una misma lista se leen como si fueran
        # formatos distintos de fechas distintas.
        fecha_txt = fecha_q.toString("dd-MM-yyyy") if fecha_q.isValid() else fecha
        entradas.append((orden if fecha_q.isValid() else _ORDEN_ULTIMO,
                         {"fecha": fecha_txt, "hora": hora_real, "alumno": alumno, "texto": nota}))

    # sorted es estable: a igual fecha, la historia del caso queda antes que
    # las atenciones, que es el orden en que se cargaron.
    entradas.sort(key=lambda par: par[0])
    return [dato for _, dato in entradas]


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

    # Una sola línea de tiempo: lo que le hicieron al paciente antes de
    # llegar (historia clínica del caso) y las atenciones cerradas, en orden.
    # La evolución que escribió el alumno tiene que quedar DESPUÉS de las
    # atenciones previas, que es como se lee una ficha de verdad.
    historia_clinica = caso.get("historia_clinica", "") if isinstance(caso, dict) else ""
    entradas = linea_tiempo(historia_clinica, row.fecha,
                            historial_atenciones(shedule, rut, username, is_admin))

    partes.append("<h3>Historial del paciente</h3>")
    if entradas:
        # Escapado: son textos libres (historia del caso, nota del alumno) y
        # un "<" suelto rompía el resto de la ficha sin dejar rastro de por
        # qué -- una otoscopia que dice "conducto <2 mm", por ejemplo.
        # El alumno ve todas las entradas IGUAL: una ficha real no distingue
        # "lo que traía el paciente" de "lo que escribí yo", y marcarlo rompe
        # el realismo que la ficha aporta. El docente sí ve quién escribió
        # cada nota -- ahí la ficha es una herramienta de corrección, no el
        # registro que el alumno está aprendiendo a leer.
        items = "".join(
            "<li><b>{fecha}{hora}</b>{quien} — {texto}</li>".format(
                fecha=html.escape(e["fecha"] or "sin fecha"),
                # Las entradas del caso no tienen hora: sin esto quedaba un
                # espacio colgando dentro del <b>.
                hora=f" {html.escape(e['hora'])}" if e["hora"] else "",
                quien=f" {html.escape(e['alumno'])}" if (is_admin and e["alumno"]) else "",
                texto=html.escape(e["texto"] or "sin comentario"),
            )
            for e in entradas
        )
        partes.append(f"<ul>{items}</ul>")
    else:
        partes.append("<p>Sin historial registrado para este paciente.</p>")

    return "".join(partes)
