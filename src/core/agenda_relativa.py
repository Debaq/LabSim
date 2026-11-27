"""Agenda relativa al ingreso del alumno (docs/decisiones.md, "Agenda
relativa al ingreso del alumno").

El docente arma el día en orden y con la duración de cada atención
(appointments.duracion_min). La hora que pone solo ordena. Cuando el alumno
ingresa ese día, su horario se calcula desde ahí:

- el primer turno parte en el próximo múltiplo de 5 minutos después del
  ingreso, pero nunca antes de la hora que puso el docente al primero (un
  paciente citado a las 14:30 no llega a las 8 porque el alumno entró
  temprano a otra cosa);
- cada turno siguiente empieza donde termina el anterior, sumando las
  duraciones en el orden de las horas (empate: el id de la cita);
- cada paciente llega a la sala de espera en un momento al azar dentro de
  los 15 minutos antes de su turno. El azar sale de una semilla fija por
  alumno, cita y día: el mismo alumno ve siempre la misma llegada.

El ingreso del día es el primero que cae en la fecha local de hoy entre las
sesiones vigentes que manda el servidor (sync.php, "ingresos", en UTC): no
cambia si reinicia la app ni si se pasa a otro PC. Sin ninguno de hoy (una
sesión de anoche todavía vigente) vale el momento en que esta app calculó la
agenda por primera vez hoy.

Funciones puras salvo el recuerdo de los ingresos y el respaldo local; sin
Qt para poder testearlas.
"""

import random
import zlib
from datetime import date, datetime, timedelta, timezone

LLEGADA_MAX_ANTES_MIN = 15
PASO_MIN = 5

_ingresos_utc: list[str] = []
_ingreso_local: dict = {}   # {date: datetime} respaldo sin sesión de hoy


def recordar_ingresos(ingresos):
    """Guarda los ingresos que mandó el sync (None = el servidor no los manda)."""
    global _ingresos_utc
    if ingresos is not None:
        _ingresos_utc = [str(x) for x in ingresos]


def _utc_a_local(texto):
    try:
        utc = datetime.strptime(texto[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return utc.astimezone().replace(tzinfo=None)


def ingreso_del_dia(ingresos_utc, hoy: date):
    """Primer ingreso (hora local, sin tz) que cae en `hoy`, o None."""
    locales = [d for d in (_utc_a_local(t) for t in ingresos_utc) if d is not None and d.date() == hoy]
    return min(locales) if locales else None


def _ingreso(ahora: datetime):
    ingreso = ingreso_del_dia(_ingresos_utc, ahora.date())
    if ingreso is not None:
        return ingreso
    return _ingreso_local.setdefault(ahora.date(), ahora)


def _hora_de(fecha: date, hora: str):
    try:
        h, m = hora.strip()[:5].split(":")
        return datetime(fecha.year, fecha.month, fecha.day, int(h), int(m))
    except (ValueError, AttributeError):
        return None


def primer_turno(ingreso: datetime) -> datetime:
    """Próximo múltiplo de PASO_MIN estrictamente después del ingreso."""
    base = ingreso.replace(second=0, microsecond=0)
    resto = base.minute % PASO_MIN
    return base + timedelta(minutes=PASO_MIN - resto)


def _semilla(username, key, fecha_txt):
    return zlib.crc32(f"{username}|{key}|{fecha_txt}".encode("utf-8"))


def es_relativa(entry) -> bool:
    return bool(getattr(entry, "duracion_min", None)) and getattr(entry, "practice_id", None) is None \
        and not getattr(entry, "sin_cita", False)


def calcular(agenda: dict, username: str, ingreso: datetime, fecha_txt: str):
    """Pone turno_inicio / turno_fin / llegada (datetime local) en las citas
    con duración de `fecha_txt` ('dd-MM-yy'). Las demás quedan en None."""
    for entry in agenda.values():
        entry.turno_inicio = entry.turno_fin = entry.llegada = None
    try:
        fecha = datetime.strptime(fecha_txt, "%d-%m-%y").date()
    except ValueError:
        return
    del_dia = [(k, e) for k, e in agenda.items() if es_relativa(e) and e.fecha == fecha_txt
               and _hora_de(fecha, e.hora) is not None]
    if not del_dia:
        return

    def orden(par):
        k, e = par
        try:
            n = int(k)
        except ValueError:
            n = 0
        return (_hora_de(fecha, e.hora), n)

    del_dia.sort(key=orden)
    inicio = max(primer_turno(ingreso), _hora_de(fecha, del_dia[0][1].hora))
    for key, entry in del_dia:
        entry.turno_inicio = inicio
        entry.turno_fin = inicio + timedelta(minutes=int(entry.duracion_min))
        antes = random.Random(_semilla(username, key, fecha_txt)).uniform(0, LLEGADA_MAX_ANTES_MIN)
        entry.llegada = (inicio - timedelta(minutes=antes)).replace(microsecond=0)
        inicio = entry.turno_fin


def aplicar(agenda: dict, user: dict | None, ahora: datetime | None = None):
    """Calcula los turnos de hoy para el alumno conectado. El docente ve las
    horas que él puso: a él no se le calcula nada."""
    user = user or {}
    if user.get("role") == "admin":
        return
    ahora = ahora or datetime.now()
    calcular(agenda, user.get("username", ""), _ingreso(ahora), ahora.strftime("%d-%m-%y"))


def hora_vista(entry) -> str:
    """La hora que ve el alumno: su turno si la cita es relativa, la del docente si no."""
    inicio = getattr(entry, "turno_inicio", None)
    return inicio.strftime("%H:%M") if inicio is not None else (entry.hora or "")


def momento_vista(entry):
    """datetime del turno (relativa) o de la cita (fija); None si no se sabe."""
    inicio = getattr(entry, "turno_inicio", None)
    if inicio is not None:
        return inicio
    try:
        fecha = datetime.strptime(entry.fecha, "%d-%m-%y").date()
    except (ValueError, TypeError):
        return None
    return _hora_de(fecha, entry.hora or "")


def todavia_no_llega(entry, ahora: datetime | None = None) -> bool:
    llegada = getattr(entry, "llegada", None)
    return llegada is not None and (ahora or datetime.now()) < llegada
