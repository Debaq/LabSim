# -*- coding: utf-8 -*-
"""Despierto o dormido: cuánto ruido mete el paciente en los potenciales.

El paciente llega despierto. Despierto, el EEG y la actividad muscular
ensucian el registro (más ruido por barrido y más tramos de movimiento que el
equipo descarta); un bebé despierto es casi imposible de registrar. Para que
baje, el alumno tiene que pedirlo en el chat: a la mamá o a quien acompañe que
haga dormir al bebé, o al paciente (niño o adulto) que se relaje, cierre los
ojos e intente dormir. Cuando el modelo acepta y lo hace, el chat avisa
(marca [DUERME], ver LlmConfig::sueno en el backend) y main llama a dormir().

Dormido queda el ruido que declara el caso (CASE_REFERENCE_DEFAULT ya es "un
paciente típico dormido"): esto no cambia los casos, cambia el punto de
partida.

Sin chat (sin cuenta, o un curso sin el módulo) no hay a quién pedírselo: el
paciente está dormido desde el principio (`por_chat`, lo pone main al iniciar
sesión, igual que core.ficha.entrega_por_chat).

Lo usan ABR_Curve, ECochG_Curve (y con ellos el AABR), el ASSR y el monitor
de EEG. Los corticales no: su estado lo fija el docente en el bloque Central,
porque dormir cambia las respuestas mismas y no solo el ruido.

Los factores son SIN FUENTE numérica: órdenes de magnitud para que despierto
se note en el monitor y en el FSP, más en el bebé que en el adulto.
"""

por_chat = False
_dormidos = set()       # ficha (case_id) del paciente dormido en esta atención

# (desde años, ruido por barrido, inquietud mínima) mientras está despierto
DESPIERTO = (
    (0.0, 3.0, 0.8),    # bebé: llora, succiona, se mueve
    (3.0, 2.0, 0.45),   # niño
    (13.0, 1.5, 0.2),   # adolescente o adulto despierto, tenso
)


def _clave(patient):
    case_id = (patient or {}).get("id") if isinstance(patient, dict) else None
    return str(case_id) if case_id not in (None, "") else None


def dormido(patient):
    """True si este paciente ya está dormido (o si no hay chat para pedirlo)."""
    clave = _clave(patient)
    return not por_chat or clave is None or clave in _dormidos


def dormir(case_id):
    _dormidos.add(str(case_id))


def despertar(case_id):
    """Atención nueva: el paciente vuelve a llegar despierto."""
    _dormidos.discard(str(case_id))


def _edad(patient):
    try:
        edad = float((patient or {}).get("edad") or 0)
    except (TypeError, ValueError):
        edad = 0.0
    return max(edad, 0.0)


def factores(patient):
    """(ruido, inquietud mínima): 1.0 y 0.0 dormido."""
    if dormido(patient):
        return 1.0, 0.0
    edad = _edad(patient)
    ruido, inquietud = DESPIERTO[0][1:]
    for desde, r, i in DESPIERTO:
        if edad >= desde:
            ruido, inquietud = r, i
    return ruido, inquietud


def ruido(patient):
    return factores(patient)[0]


def inquietud(patient, del_caso):
    """La inquietud del caso, o la de estar despierto si es mayor."""
    try:
        del_caso = float(del_caso or 0.0)
    except (TypeError, ValueError):
        del_caso = 0.0
    return max(del_caso, factores(patient)[1])


def es_bebe(patient):
    return _edad(patient) < DESPIERTO[1][0]
