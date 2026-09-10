# -*- coding: utf-8 -*-
#################################################################
#                                                               #
#                  NOMBRE PROYECTO : LabSim                     #
#                    VER. 0.2 - DebugMkg                        #
#                                                               #
#################################################################
"""Panel de depuración de enmascaramiento (solo admin/docente).

El panel contesta, en este orden, las preguntas que uno se hace cuando el
paciente simulado no responde lo que el docente esperaba:

  1. AHORA: qué está haciendo el equipo, qué contesta el paciente y POR QUÉ
     (por su propio oído o por cruce al contralateral).
  2. ¿Hace falta enmascarar?: la regla es fisiológica, no de tabla -- el
     estímulo cruza cuando el nivel que llega a la cóclea contralateral
     (presentado menos la atenuación interaural) alcanza su umbral óseo.
     Vía ósea la atenuación interaural es ~0 dB, así que siempre cruza.
  3. Rango de ruido útil [mínimo efectivo .. máximo tolerable] con los
     términos desglosados, para poder auditar el número, y aviso de dilema
     de enmascaramiento cuando el mínimo supera al máximo (gaps grandes
     bilaterales: no existe ruido que sirva).
  4. Perfil audiométrico: gap aéreo-óseo y tipo de pérdida por frecuencia.
  5. Logoaudiometría: las dos vías por las que le puede llegar el habla.
  6. Coherencia del caso: contradicciones fisiopatológicas de la ficha
     (óseo peor que el aéreo, gap sobre el techo de transmisión, reflejo
     presente con gap, Weber/Rinne que no cuadran con el gap, LDL bajo el
     umbral, SDT lejos del promedio tonal...).

Las tablas que audita son las *_mkg: son las que consulta el motor de
respuestas, y pueden diferir de las que ve el alumno en el audiograma.

El reporte se arma en build_report(), que es una función pura sobre los
objetos del motor (sin Qt) para poder testearla.
"""

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (QCheckBox, QDialog, QHBoxLayout, QPlainTextEdit,
                               QPushButton, QVBoxLayout)

from audiometria.masking_params import (CE_LOGO, CE_TONAL, NOMBRE_RUIDO,
                                        RUIDOS_ENMASCARANTES, STIM_NBN,
                                        ce_logo)
from core.helpers import Preferences
from core.ui_helpers import style_dialog

class_pref = Preferences()
output_list = class_pref.get("output_list")
stim_list = class_pref.get("stim_list")
trans_list = class_pref.get("trans_list")

# Las tablas de umbrales del caso traen 15 filas: las 9 frecuencias del
# audiograma clásico + las 6 de alta frecuencia (ver h_audio.threshold_basic
# y config_audiometer.json:frecuency_dict).
FRECUENCIAS = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000,
               9000, 10000, 11200, 12500, 14000, 16000]

SIN_CASO = "No hay un caso cargado en el audiómetro (nadie siendo atendido)."

# Techo de transmisión: sobre este gap la pérdida ya no puede ser puramente
# de conducción (ver catálogo de cuadros, GAP_MAX_DB).
GAP_MAX_DB = 60
# Un gap de 10 dB o menos entra en el error de medición: no es patológico.
GAP_SIGNIFICATIVO = 15
# Atenuación interaural del habla (logoaudiometría), fija, no depende de
# frecuencia a diferencia de la tonal.
AT_LOGO = 45

OIDO = {0: "OD", 1: "OI"}

# Indices de stim_list (config_audiometer.json). Los cuatro ruidos enmascaran;
# cada uno con su CE, porque lo que tapa un tono es la energia que cae dentro
# de su banda critica (ver response.CE_TONAL).
NBN = STIM_NBN
RUIDOS = RUIDOS_ENMASCARANTES


def _oi(side):
    return OIDO.get(side, str(side))


def _fmt_par(par, suf=""):
    """[od, oi] -> 'OD 40 | OI 15'."""
    try:
        return f"OD {par[0]}{suf} | OI {par[1]}{suf}"
    except (TypeError, IndexError, KeyError):
        return f"?? ({par!r})"


def _fmt_umd(umd):
    """UMD es [{'int': dB, 'percentage': %}, ...] por oído."""
    try:
        return " | ".join(
            f"{_oi(i)} {o['percentage']}% @ {o['int']} dB"
            for i, o in enumerate(umd))
    except (TypeError, IndexError, KeyError):
        return f"?? ({umd!r})"


def _tipo_perdida(aereo, oseo):
    """Clasificación por frecuencia a partir del gap y del óseo."""
    gap = aereo - oseo
    if aereo <= 15:
        return "normal"
    if gap >= GAP_SIGNIFICATIVO:
        return "transmisiva" if oseo <= 15 else "mixta"
    return "sensorioneural"


def _grado(db):
    """Grado de la pérdida (clasificación clínica por promedio)."""
    if db <= 20:
        return "normal"
    if db <= 40:
        return "leve"
    if db <= 55:
        return "moderada"
    if db <= 70:
        return "moderada-severa"
    if db <= 90:
        return "severa"
    return "profunda"


def _pta(tabla, side):
    """Promedio de Fletcher (500/1000/2000 Hz), el mismo criterio que usa
    el motor para SDT/SRT."""
    try:
        vals = [tabla[i][side] for i in (2, 3, 4)]
    except (IndexError, TypeError, KeyError):
        return None
    return sum(sorted(vals)[:2]) / 2


def _fila_frec(case):
    """Frecuencias con datos reales: corta el relleno de alta frecuencia que
    repite la última fila del audiograma clásico."""
    aerea = case.get('Aerea_mkg') or []
    n = min(len(aerea), len(FRECUENCIAS))
    ultimo = 9
    for idx in range(9, n):
        if aerea[idx] != aerea[8]:
            ultimo = idx + 1
    return list(range(min(n, max(9, ultimo))))


# --------------------------------------------------------------------------
# 1. AHORA: el veredicto de lo que está pasando en este instante
# --------------------------------------------------------------------------

def _logo_vias(logo, side, inten, ruido, stim_mkg=None):
    """Las dos vías por las que el habla le puede llegar al paciente, con el
    mismo modelo que CalculateLogo.get(): su propio oído (que el ruido puede
    tapar si cruza de vuelta) y el cruce al contralateral (que sólo existe
    si la intensidad supera la atenuación interaural)."""
    other = 1 - side
    bone = logo._bone_sdt()
    gap = logo._air_bone_gap()
    ce = ce_logo(stim_mkg)
    efectivo = ruido - ce if ruido else 0
    shift_e = max(0, (efectivo - AT_LOGO) - bone[side])
    shift_ne = max(0, (efectivo - gap[other]) - bone[other])
    nivel_cruce = inten - AT_LOGO
    return {
        'other': other, 'bone': bone, 'gap': gap, 'ce': ce,
        'efectivo': efectivo,
        'shift_e': shift_e, 'shift_ne': shift_ne,
        'nivel_cruce': nivel_cruce,
        'hay_cruce': nivel_cruce >= bone[other],
        'propio': logo._curve(side, inten - shift_e),
        'cruce': logo._curve(other, nivel_cruce + gap[other] - shift_ne),
    }


def _zona_logo(logo, side, inten, ruido, stim_mkg=None):
    """Zona del plateau para el habla. A diferencia de la tonal, primero
    pregunta si el cruce es posible: bajo la atenuación interaural no hay
    nada que enmascarar y el ruido sólo puede estorbar."""
    v = _logo_vias(logo, side, inten, ruido, stim_mkg)
    r = logo._masking_range(side, 1 - side, inten, stim_mkg)
    # el sobre-enmascaramiento manda: aunque no hubiera nada que enmascarar,
    # un ruido excesivo igual cruza de vuelta y tapa al oído estudiado
    if ruido > r['mkg_max']:
        return ("SOBRE-ENMASCARADO -> el ruido cruzó de vuelta y tapa el "
                "oído estudiado")
    if not v['hay_cruce']:
        return ("SIN CRUCE POSIBLE -> el habla no llega a la cóclea "
                f"contralateral ({v['nivel_cruce']:g} dB vs óseo "
                f"{v['bone'][v['other']]:g}), enmascarar es innecesario")
    if ruido < r['mkg_min']:
        return ("SUB-ENMASCARADO -> el % puede venir del oído contralateral "
                "(curva sombra)")
    return "MESETA -> el % es del oído estudiado"


def _veredicto_logo(logo, logo_state):
    """Explica el % que contesta el paciente separando las dos vías que
    calcula CalculateLogo.get(): su propio oído y el cruce al contralateral."""
    (playable, inten, side, with_mkg, int_mkg,
     stim_mkg) = (list(logo_state) + [None] * 6)[:6]
    if logo is None or side not in (0, 1) or inten is None:
        return ["Logoaudiometría: las listas de palabras no tienen estado "
                "(nadie dictando todavía)."]

    ruido = int_mkg if (with_mkg and int_mkg is not None) else 0
    v = _logo_vias(logo, side, inten, ruido, stim_mkg)
    other, propio, cruce = v['other'], v['propio'], v['cruce']
    pct = max(propio, cruce)

    quien = "su propio oído" if propio >= cruce else f"CRUCE al {_oi(other)}"
    lineas = [
        f"Habla a {inten} dB en {_oi(side)}, "
        + (f"ruido {ruido} dB en {_oi(other)}" if ruido
           else "SIN ruido contralateral"),
        f"  -> el paciente entiende {pct}% ({int(pct / 4)} de 25 palabras), "
        f"por {quien}",
        f"     {_oi(side)} propio: {propio}%"
        + (f"  (el ruido le cruza de vuelta y le sube el umbral "
           f"{v['shift_e']:g} dB)" if v['shift_e'] else ""),
        f"     {_oi(other)} por cruce: {cruce}%  "
        f"(habla {inten} - AI {AT_LOGO} = {v['nivel_cruce']:g} dB en su cóclea, "
        f"óseo {v['bone'][other]:g} dB"
        + (f", el ruido lo tapa {v['shift_ne']:g} dB)" if v['shift_ne'] else ")"),
        f"     {_zona_logo(logo, side, inten, ruido, stim_mkg)}",
    ]
    if ruido:
        nombre = NOMBRE_RUIDO.get(stim_mkg, "ruido sin identificar")
        if v['ce']:
            lineas.insert(3, f"     {nombre}: CE +{v['ce']} dB sobre el habla, "
                             f"de los {ruido} dB puestos enmascaran {v['efectivo']:g}")
        else:
            lineas.insert(3, f"     {nombre}: es el ruido que corresponde "
                             "(CE 0, enmascara lo que marca el dial)")
    if cruce > propio:
        lineas.append(f"     ATENCIÓN: está midiendo el {_oi(other)}, no el "
                      f"{_oi(side)}. Falta enmascarar (curva sombra).")
    return lineas


def _veredicto_tonal(response, audio):
    """Explica si el paciente levanta la mano con el tono que hay puesto."""
    stim = audio['stim']
    freq_idx = audio['freq']
    encendidos = [ch for ch in (0, 1) if audio['stimOn'][ch]]
    tonos = [ch for ch in encendidos if stim[ch] == 0]
    if not tonos:
        return ["No hay tono presentándose (nada que evaluar)."]

    lineas = []
    for ch_tone in tonos:
        via = 'osea' if audio['trans'][ch_tone] == 1 else 'aerea'
        o_e = audio['output'][ch_tone]
        o_n = 1 - o_e
        int_ = audio['int'][ch_tone]
        ruidos = [ch for ch in encendidos
                  if ch != ch_tone and stim[ch] in RUIDOS
                  and audio['output'][ch] == o_n]
        ch_ruido = ruidos[0] if ruidos else None
        int_mkg = audio['int'][ch_ruido] if ruidos else 0
        ce = CE_TONAL.get(stim[ch_ruido], 0) if ruidos else 0
        try:
            calc = response._masking_calc(via, freq_idx, o_e, o_n, ce)
            umbral = response._resolve_masked_threshold(via, freq_idx, o_e, o_n,
                                                        int_mkg, ce)
        except (IndexError, KeyError, TypeError) as exc:
            lineas.append(f"Tono {via} en {_oi(o_e)}: no se pudo calcular ({exc})")
            continue

        responde = umbral <= int_
        nombre = (stim_list[stim[ch_ruido]] if ruidos and stim[ch_ruido] < len(stim_list)
                  else "ruido")
        lineas.append(
            f"Tono {via} {int_} dB en {_oi(o_e)}, "
            + (f"{nombre} {int_mkg} dB en {_oi(o_n)}" if ruidos
               else "SIN ruido contralateral")
            + f"  -> {'RESPONDE' if responde else 'no responde'} "
              f"(umbral aparente {umbral:g} dB)")
        if ce:
            lineas.append(
                f"     {nombre} enmascara peor que el NBN: CE +{ce} dB, "
                f"el mínimo efectivo sube a {calc['mkg_min']:g} dB "
                "(la energía fuera de la banda crítica del tono no tapa nada)")
        lineas.append(f"     {_zona(calc, int_mkg)}")
        if calc['shadow'] < calc['real'] and int_mkg < calc['mkg_min']:
            lineas.append(
                f"     el umbral aparente {calc['shadow']:g} dB NO es del "
                f"{_oi(o_e)} (real {calc['real']:g}): lo está oyendo con el "
                f"{_oi(o_n)}")
    return lineas


def _bloque_ahora(response, audio, logo, logo_state):
    test = audio['test']
    try:
        hz = response.frecuency[audio['freq']]
    except (IndexError, TypeError):
        hz = "?"
    lineas = ["#" * 72,
              f"### AHORA -- {test} @ {hz} Hz",
              "#" * 72]
    if str(test).startswith("Logo"):
        lineas += _veredicto_logo(logo, logo_state)
    else:
        lineas += _veredicto_tonal(response, audio)
    return lineas


def _zona(rango, int_mkg):
    """Zona del plateau en la que cae el ruido puesto. El sub-enmascarado no
    implica que el paciente responda mal: implica que el umbral/porcentaje
    que se está midiendo puede no ser del oído estudiado."""
    if rango['mkg_min'] > rango['mkg_max']:
        return ("DILEMA DE ENMASCARAMIENTO: el mínimo efectivo supera al "
                "máximo tolerable, no existe ruido válido")
    if int_mkg < rango['mkg_min']:
        return ("SUB-ENMASCARADO -> el resultado puede venir del oído "
                "contralateral (curva sombra)")
    if int_mkg > rango['mkg_max']:
        return ("SOBRE-ENMASCARADO -> el ruido cruzó de vuelta y tapa el "
                "oído estudiado")
    return "MESETA -> el resultado es del oído estudiado"


# --------------------------------------------------------------------------
# 2. ¿Hace falta enmascarar? y 3. rango de ruido útil
# --------------------------------------------------------------------------

def _terminos(response, via, freq, o_e, o_n, ce=0):
    """Los términos de la fórmula de enmascaramiento, sin ordenar el rango.

    _masking_calc devuelve el rango ya ordenado (sorted), lo que esconde el
    dilema de enmascaramiento: acá se conserva el mínimo y el máximo tal
    como salen de la fórmula para poder avisar cuando el mínimo supera al
    máximo (no existe ruido que sirva).
    """
    aerea = response.dbdata['Aerea_mkg']
    osea = response.dbdata['Osea_mkg']
    uae, uane = aerea[freq][o_e], aerea[freq][o_n]
    uoe, uone = osea[freq][o_e], osea[freq][o_n]
    if via == 'aerea':
        at = response.attenuations[freq]
        eo = 0
        estim = uae
        mkg_min = uae - at - uone + uane + ce
    else:
        at = 0
        # el oido ocluido por el auricular del ruido es el no estudiado
        eo = response.oclusive_efect(freq, o_n) or 0
        estim = uoe
        mkg_min = uoe - uone + uane + ce + eo
    # el ruido siempre entra por auricular: para volver a tapar al oido
    # estudiado tiene que cruzar por via aerea, tambien en la via osea
    at_ruido = response.attenuations[freq]
    return {'uae': uae, 'uane': uane, 'uoe': uoe, 'uone': uone, 'at': at,
            'at_ruido': at_ruido, 'eo': eo, 'estim': estim, 'mkg_min': mkg_min,
            'mkg_max': uoe + at_ruido,
            # el estímulo cruza cuando lo que llega a la cóclea del otro
            # oído alcanza su umbral óseo
            'nivel_cruce': estim - at, 'cruza': (estim - at) >= uone}


def _bloque_cruce(response, audio):
    freq = audio['freq']
    try:
        hz = response.frecuency[freq]
        at_a = response.attenuations[freq]
    except (IndexError, TypeError):
        return ["", f"=== ¿HACE FALTA ENMASCARAR? === frecuencia fuera de rango "
                    f"(índice {freq}: alta frecuencia, sin atenuación tabulada)"]

    lineas = ["", f"=== ¿HACE FALTA ENMASCARAR? ({hz} Hz) ===",
              "Regla: cruza si (nivel en el oído probado - atenuación interaural)",
              f"       alcanza el umbral ÓSEO del contralateral.  "
              f"AI aérea {at_a} dB | AI ósea 0 dB (siempre cruza)"]
    for via in ('aerea', 'osea'):
        for o_e in (0, 1):
            o_n = 1 - o_e
            try:
                t = _terminos(response, via, freq, o_e, o_n)
            except (IndexError, KeyError, TypeError) as exc:
                lineas.append(f"{via} {_oi(o_e)}: no se pudo calcular ({exc})")
                continue
            veredicto = ("SÍ, enmascarar" if t['cruza']
                         else "no hace falta enmascarar")
            lineas.append(
                f"  {via.upper():6} {_oi(o_e)} (umbral {t['estim']:g} dB): "
                f"{t['estim']:g} - {t['at']} = {t['nivel_cruce']:g} dB en la "
                f"cóclea {_oi(o_n)} (óseo {t['uone']:g}) -> {veredicto}")
    return lineas


def _bloque_tonal(response, audio):
    """Rango de ruido útil por vía y oído, con los términos a la vista."""
    freq = audio['freq']
    lineas = ["", "=== ENMASCARAMIENTO TONAL (rango de ruido útil) ===",
              "  aérea: mín = UAE - AI - UONE + UANE      máx = UOE + AI",
              "  ósea:  mín = UOE - UONE + UANE + EfOcl   máx = UOE + AI",
              "  (el ruido entra por auricular: para tapar al oído estudiado "
              "cruza con la AI aérea en ambas vías)"]
    for via in ('aerea', 'osea'):
        for o_e in (0, 1):
            o_n = 1 - o_e
            try:
                r = response._masking_calc(via, freq, o_e, o_n)
                t = _terminos(response, via, freq, o_e, o_n)
            except (IndexError, KeyError, TypeError) as exc:
                lineas.append(f"{via} estudiando {_oi(o_e)}: "
                              f"no se pudo calcular ({exc})")
                continue
            if via == 'aerea':
                cuenta = (f"{t['uae']:g} - {t['at']} - {t['uone']:g} + "
                          f"{t['uane']:g}")
            else:
                cuenta = (f"{t['uoe']:g} - {t['uone']:g} + {t['uane']:g}"
                          + (f" + {t['eo']:g}(oclusivo)" if t['eo'] else ""))
            meseta = t['mkg_max'] - t['mkg_min']
            aviso = ""
            if meseta < 0:
                # el motor ordena el rango (sorted) y lo termina aceptando:
                # el alumno "enmascara bien" en un caso donde clínicamente
                # no se puede, por eso conviene verlo señalado
                aviso = ("   <<< DILEMA: la fórmula no deja rango válido "
                         "(el motor lo invierte y lo acepta igual)")
            elif meseta < 15:
                aviso = f"   <<< meseta estrecha ({meseta:g} dB)"
            lineas.append(
                f"  {via.upper():6} estudio {_oi(o_e)}, enmascaro {_oi(o_n)}: "
                f"rango {r['mkg_min']:g} .. {r['mkg_max']:g} dB"
                f"   (real={r['real']:g}, sombra={r['shadow']:g}){aviso}")
            lineas.append(f"         mín = {cuenta} = {t['mkg_min']:g} dB   "
                          f"máx = {t['uoe']:g} + {t['at_ruido']} = "
                          f"{t['mkg_max']:g} dB")
    return lineas


# --------------------------------------------------------------------------
# 4. Perfil audiométrico: gap y tipo de pérdida por frecuencia
# --------------------------------------------------------------------------

def _bloque_caso(case):
    lineas = ["", "=== CASO ===",
              f"id: {case.get('id')}   sector: {case.get('sector')}   "
              f"género: {case.get('gender')}   edad: {case.get('edad')}"]
    aerea = case.get('Aerea_mkg') or []
    for side in (0, 1):
        pta = _pta(aerea, side)
        if pta is None:
            continue
        tipos = {_tipo_perdida(aerea[i][side],
                               (case.get('Osea_mkg') or aerea)[i][side])
                 for i in _fila_frec(case)}
        tipos.discard("normal")
        resumen = "/".join(sorted(tipos)) if tipos else "normal"
        lineas.append(f"{_oi(side)}: PTA {pta:g} dB ({_grado(pta)})   {resumen}")
    if 'SDT' in case:
        lineas.append(f"SDT (perfil):      {_fmt_par(case['SDT'], ' dB')}")
    if 'SRT' in case:
        lineas.append(f"SRT (perfil):      {_fmt_par(case['SRT'], ' dB')}")
    if 'UMD' in case:
        lineas.append(f"UMD (máx. discr.): {_fmt_umd(case['UMD'])}")
    if 'recruit' in case:
        lineas.append(f"Reclutamiento:     {_fmt_par(case['recruit'])}")
    lineas.extend(_tabla_umbrales(case))
    return lineas


ANCHO_TIPO = 14


def _celda_umbral(a, o, marca):
    return f"{a:>5}{o:>6}{a - o:>5}{marca} {_tipo_perdida(a, o):<{ANCHO_TIPO}}"


def _tabla_umbrales(case):
    """Aereo/oseo/gap/tipo por oido, sobre las tablas Aerea_mkg / Osea_mkg
    (las que consulta el motor). La columna de la izquierda marca con ! las
    filas donde esas tablas no coinciden con las que ve el alumno, y con *
    las que son fisiologicamente imposibles."""
    aerea = case.get('Aerea') or []
    aerea_m = case.get('Aerea_mkg') or []
    osea = case.get('Osea') or []
    osea_m = case.get('Osea_mkg') or []
    ancho = len(_celda_umbral(0, 0, " "))
    cab = f"{'aér':>5}{'óseo':>6}{'gap':>5}  {'tipo':<{ANCHO_TIPO}}"
    lineas = ["",
              "Umbrales del motor: Aerea_mkg / Osea_mkg -- gap = aéreo - óseo",
              f"        |{'OD (motor)'.center(ancho)}|{'OI (motor)'.center(ancho)}|",
              f"    Hz  |{cab}|{cab}|",
              f"  ------+{'-' * ancho}+{'-' * ancho}+"]
    difs, raros = [], []
    for idx in _fila_frec(case):
        if idx >= len(aerea_m) or idx >= len(osea_m):
            break
        hz = FRECUENCIAS[idx]
        celdas = []
        for side in (0, 1):
            a, o = aerea_m[idx][side], osea_m[idx][side]
            gap = a - o
            marca = "*" if (gap < -5 or gap > GAP_MAX_DB) else " "
            if marca == "*":
                raros.append((hz, _oi(side), gap))
            celdas.append(_celda_umbral(a, o, marca))
        dif = ((idx < len(aerea) and aerea[idx] != aerea_m[idx])
               or (idx < len(osea) and osea[idx] != osea_m[idx]))
        if dif:
            difs.append(hz)
        lineas.append(f"{'!' if dif else ' '} {hz:>5} |{celdas[0]}|{celdas[1]}|")
    if difs:
        lineas.append(f"  ! Aerea/Osea != *_mkg en: {difs} Hz "
                      "(el paciente responde según *_mkg)")
    for hz, oido, gap in raros:
        if gap < -5:
            lineas.append(f"  * {hz} Hz {oido}: óseo {abs(gap)} dB PEOR que el "
                          "aéreo -- imposible, la vía ósea saltea el oído medio")
        else:
            lineas.append(f"  * {hz} Hz {oido}: gap {gap} dB sobre el techo de "
                          f"transmisión ({GAP_MAX_DB} dB)")
    return lineas


# --------------------------------------------------------------------------
# 5. Logoaudiometría
# --------------------------------------------------------------------------

def _bloque_logo(logo, case, logo_state):
    lineas = ["", "=== LOGOAUDIOMETRÍA ==="]
    if logo is None:
        lineas.append("Listas de palabras sin caso cargado: no hay CalculateLogo.")
        return lineas
    bone = logo._bone_sdt()
    gap = logo._air_bone_gap()
    lineas.append(f"SDT calculado por CalculateLogo (Fletcher aéreo): "
                  f"{_fmt_par(logo.sdt, ' dB')}")
    lineas.append(f"SDT del perfil (el que usa response.py):          "
                  f"{_fmt_par(case.get('SDT', ['-', '-']), ' dB')}")
    lineas.append(f"Óseo de Fletcher: {_fmt_par(bone, ' dB')}   "
                  f"gap de habla: {_fmt_par(gap, ' dB')}   "
                  f"atenuación interaural: {logo.logo_attenuation} dB")

    (playable, inten, side, with_mkg, int_mkg,
     stim_mkg) = (list(logo_state) + [None] * 6)[:6]
    lineas.append(f"Estado recibido en Listas: dictando={bool(playable)}  "
                  f"oído={_oi(side) if side in (0, 1) else side}  "
                  f"habla={inten} dB  con_mkg={with_mkg}  ruido={int_mkg} dB "
                  f"({NOMBRE_RUIDO.get(stim_mkg, '-')}, CE +{ce_logo(stim_mkg)})")
    lineas.append("CE del habla por ruido: "
                  + ", ".join(f"{NOMBRE_RUIDO[k]} +{v}"
                              for k, v in sorted(CE_LOGO.items(), key=lambda x: x[1])))

    for side_i in (0, 1):
        try:
            inten_calc = inten if (side_i == side and inten is not None) else 0
            r = logo._masking_range(side_i, 1 - side_i, inten_calc, stim_mkg)
        except (IndexError, KeyError, TypeError) as exc:
            lineas.append(f"{_oi(side_i)}: no se pudo calcular el rango ({exc})")
            continue
        lineas.append(f"{_oi(side_i)}: rango de mkg para habla a {inten_calc} dB: "
                      f"{r['mkg_min']:g} .. {r['mkg_max']:g} dB")

    if side in (0, 1) and inten is not None:
        try:
            usado = int_mkg if (with_mkg and int_mkg is not None) else 0
            pct = logo.get(side, with_mkg, inten, int_mkg, stim_mkg)
            lineas.append(f"AHORA: ruido usado {usado} dB -> "
                          f"{_zona_logo(logo, side, inten, usado, stim_mkg)}")
            lineas.append(f"       discriminación que responde el paciente: {pct}% "
                          f"({int(pct / 4)} de 25 palabras)")
        except (KeyError, IndexError, TypeError) as exc:
            lineas.append(f"AHORA: no se pudo calcular el % ({exc})")

    escala = sorted(logo.data[0], key=int)
    lineas.append("")
    lineas.append("Curva de discriminación (dB HL -> %)")
    lineas.append("  dB " + "".join(f"{db:>5}" for db in escala))
    for side_i in (0, 1):
        lineas.append(f"  {_oi(side_i)} "
                      + "".join(f"{logo.data[side_i][db]:>5}" for db in escala))
    return lineas


# --------------------------------------------------------------------------
# 6. Coherencia fisiopatológica de la ficha
# --------------------------------------------------------------------------

def _gap_en(case, hz, side):
    try:
        idx = FRECUENCIAS.index(int(hz))
        return case['Aerea_mkg'][idx][side] - case['Osea_mkg'][idx][side]
    except (ValueError, IndexError, KeyError, TypeError):
        return None


def _chk_sdt(case, avisos):
    """El SDT/SRT sigue al promedio tonal: si se aparta más de 10 dB, el
    paciente contesta el habla en un nivel que no cuadra con su audiograma."""
    aerea = case.get('Aerea_mkg') or []
    for clave in ('SDT', 'SRT'):
        valores = case.get(clave)
        if not valores:
            continue
        for side in (0, 1):
            pta = _pta(aerea, side)
            if pta is None:
                continue
            dif = valores[side] - pta
            if abs(dif) > 10:
                avisos.append(("?", f"{clave} {_oi(side)} {valores[side]:g} dB vs "
                                    f"promedio tonal {pta:g} dB ({dif:+g}): el habla "
                                    "debería seguir al audiograma +-10 dB"))


def _chk_umd(case, avisos):
    """Discriminación vs tipo de pérdida: la transmisiva pura llega al 100%
    (el oído interno está sano, solo hay que subir el volumen); la coclear
    rola; la retrococlear desproporciona."""
    umd = case.get('UMD') or []
    aerea = case.get('Aerea_mkg') or []
    osea = case.get('Osea_mkg') or []
    for side in (0, 1):
        try:
            pct, inten = umd[side]['percentage'], umd[side]['int']
        except (IndexError, KeyError, TypeError):
            continue
        pta_a, pta_o = _pta(aerea, side), _pta(osea, side)
        if pta_a is None or pta_o is None:
            continue
        gap = pta_a - pta_o
        if gap >= GAP_SIGNIFICATIVO and pta_o <= 15 and pct < 90:
            avisos.append(("?", f"UMD {_oi(side)} {pct}% con pérdida de "
                                f"transmisión pura (gap {gap:g} dB, óseo "
                                f"{pta_o:g} dB): el oído interno está sano, "
                                "se espera 90-100%"))
        sdt = (case.get('SDT') or [None, None])[side]
        if sdt is not None and inten <= sdt:
            avisos.append(("!", f"UMD {_oi(side)} a {inten} dB pero el SDT es "
                                f"{sdt:g} dB: la máxima discriminación no puede "
                                "estar en el umbral o debajo"))


def _chk_ldl(case, avisos):
    """El umbral de disconfort no puede caer bajo el umbral auditivo, y un
    campo dinámico menor a 25 dB implica reclutamiento."""
    ldl = case.get('LDL') or []
    aerea = case.get('Aerea_mkg') or []
    recruit = case.get('recruit') or [False, False]
    for side in (0, 1):
        for idx in (2, 3, 4):
            try:
                umbral, molesta = aerea[idx][side], ldl[idx][side]
            except (IndexError, TypeError, KeyError):
                continue
            if molesta < umbral:
                avisos.append(("!", f"{FRECUENCIAS[idx]} Hz {_oi(side)}: LDL "
                                    f"{molesta} dB bajo el umbral {umbral} dB"))
            elif molesta - umbral < 25 and not recruit[side]:
                avisos.append(("?", f"{FRECUENCIAS[idx]} Hz {_oi(side)}: campo "
                                    f"dinámico {molesta - umbral} dB sin marcar "
                                    "reclutamiento"))


def _chk_reflejo(case, avisos):
    """Un gap de transmisión bloquea el reflejo estapedial de ese lado (no
    se transmite el movimiento, y la sonda no lo mide)."""
    reflex = case.get('Reflex')
    if not isinstance(reflex, dict):
        return
    aerea, osea = case.get('Aerea_mkg') or [], case.get('Osea_mkg') or []
    for side in (0, 1):
        pta_a, pta_o = _pta(aerea, side), _pta(osea, side)
        if pta_a is None or pta_o is None:
            continue
        gap = pta_a - pta_o
        try:
            niveles = [f[side] for f in reflex.get('ipsi') or []]
        except (IndexError, TypeError, KeyError):
            continue
        presentes = [n for n in niveles if n < 105]
        if gap >= GAP_SIGNIFICATIVO and presentes:
            avisos.append(("!", f"reflejo ipsi {_oi(side)} presente a "
                                f"{min(presentes)} dB con gap {gap:g} dB: una "
                                "pérdida de transmisión abole el reflejo"))
        if gap < GAP_SIGNIFICATIVO and pta_o <= 20 and not presentes and niveles:
            avisos.append(("?", f"reflejo ipsi {_oi(side)} ausente con oído "
                                f"normal (óseo {pta_o:g} dB, sin gap)"))


def _chk_timpano(case, avisos):
    """Curva timpanométrica vs gap: una curva A con gap grande solo se
    explica por patología de cadena con oído medio aireado (otoesclerosis,
    disyunción); una B/C sin gap es rara."""
    for side, clave in ((0, 'Z_OD'), (1, 'Z_OI')):
        curva = str(case.get(clave) or "")
        aerea, osea = case.get('Aerea_mkg') or [], case.get('Osea_mkg') or []
        pta_a, pta_o = _pta(aerea, side), _pta(osea, side)
        if not curva or pta_a is None or pta_o is None:
            continue
        gap = pta_a - pta_o
        if curva.startswith('A') and gap >= 25 and curva not in ('Ad', 'As'):
            avisos.append(("?", f"timpanograma {curva} en {_oi(side)} con gap "
                                f"{gap:g} dB: oído medio aireado y normotenso, "
                                "solo cuadra con cadena (otoesclerosis/disyunción)"))
        if curva.startswith(('B', 'C')) and gap < 10:
            avisos.append(("?", f"timpanograma {curva} en {_oi(side)} sin gap "
                                f"({gap:g} dB): una curva plana/negativa suele "
                                "dar algo de transmisión"))


def _chk_acumetria(case, avisos):
    """Weber lateraliza al oído con más gap (o al mejor oído si la pérdida
    es sensorioneural); Rinne se hace negativo con gap significativo."""
    weber = case.get('Weber')
    if isinstance(weber, dict):
        for hz, lado in weber.items():
            g_od, g_oi = _gap_en(case, hz, 0), _gap_en(case, hz, 1)
            if g_od is None or g_oi is None:
                continue
            if abs(g_od - g_oi) >= GAP_SIGNIFICATIVO:
                esperado = 'od' if g_od > g_oi else 'oi'
                if str(lado).lower() not in (esperado, 'central'):
                    avisos.append(("!", f"Weber {hz} Hz lateraliza a "
                                        f"{str(lado).upper()} pero el gap mayor "
                                        f"está en {esperado.upper()} "
                                        f"(OD {g_od:g} / OI {g_oi:g} dB)"))
    rinne = case.get('Rinne')
    if isinstance(rinne, dict):
        for hz, lados in rinne.items():
            if not isinstance(lados, dict):
                continue
            for lado, valor in lados.items():
                side = 0 if str(lado).lower() == 'od' else 1
                gap = _gap_en(case, hz, side)
                if gap is None:
                    continue
                valor = str(valor).lower()
                if valor.startswith('neg') and gap < 10:
                    avisos.append(("!", f"Rinne negativo en {_oi(side)} a {hz} Hz "
                                        f"con gap {gap:g} dB: sin gap el Rinne "
                                        "es positivo"))
                elif valor.startswith('pos') and gap >= 25:
                    avisos.append(("!", f"Rinne positivo en {_oi(side)} a {hz} Hz "
                                        f"con gap {gap:g} dB: ese gap da Rinne "
                                        "negativo"))


def _chk_eoas(case, avisos):
    """Las otoemisiones exigen oído medio permeable y células ciliadas
    externas sanas: no pueden estar normales con gap o con pérdida coclear."""
    eoas = case.get('EOAS')
    if not isinstance(eoas, dict):
        return
    aerea, osea = case.get('Aerea_mkg') or [], case.get('Osea_mkg') or []
    for side, clave in ((0, 'OD'), (1, 'OI')):
        bloque = eoas.get(clave)
        if not isinstance(bloque, dict):
            continue
        pta_a, pta_o = _pta(aerea, side), _pta(osea, side)
        if pta_a is None or pta_o is None:
            continue
        if bloque.get('type') == 'normal' and (pta_a - pta_o) >= GAP_SIGNIFICATIVO:
            avisos.append(("!", f"EOA {clave} normales con gap "
                                f"{pta_a - pta_o:g} dB: el oído medio no deja "
                                "salir la emisión"))
        if bloque.get('type') == 'normal' and pta_o > 30:
            avisos.append(("!", f"EOA {clave} normales con óseo {pta_o:g} dB: "
                                "sobre 30-35 dB de pérdida coclear no hay CCE "
                                "funcionantes"))


def _bloque_coherencia(case):
    avisos = []
    for chk in (_chk_sdt, _chk_umd, _chk_ldl, _chk_reflejo, _chk_timpano,
                _chk_acumetria, _chk_eoas):
        try:
            chk(case, avisos)
        except Exception as exc:  # una ficha vieja no puede voltear el panel
            avisos.append(("?", f"{chk.__name__}: no se pudo revisar ({exc!r})"))
    lineas = ["", "=== COHERENCIA DE LA FICHA ===",
              "  !  contradice la fisiología    ?  posible pero infrecuente"]
    if not avisos:
        lineas.append("  sin contradicciones detectadas")
        return lineas
    for marca, texto in sorted(avisos, key=lambda a: a[0]):
        lineas.append(f"  {marca}  {texto}")
    return lineas


# --------------------------------------------------------------------------
# Equipo y armado final
# --------------------------------------------------------------------------

def _bloque_equipo(response, audio):
    freq_idx = audio['freq']
    try:
        hz = response.frecuency[freq_idx]
    except (IndexError, TypeError):
        hz = "?"
    lineas = ["", "=== EQUIPO (estado actual) ===",
              f"Prueba: {audio['test']}   Frecuencia: {hz} Hz (índice {freq_idx})"]
    for ch in (0, 1):
        stim = audio['stim'][ch]
        lineas.append(
            f"ch{ch}: {stim_list[stim] if stim < len(stim_list) else stim:<18}"
            f"{output_list[audio['output'][ch]]:<11}"
            f"{trans_list[audio['trans'][ch]]:<13}"
            f"{audio['int'][ch]:>4} dB HL   "
            f"{'ESTIMULANDO' if audio['stimOn'][ch] else 'en silencio'}   "
            f"{audio['contin'][ch]}")
    if response.history_command:
        lineas.append(f"Último comando de voz: {response.history_command[0]}")
    return lineas


def build_report(response, logo=None, logo_state=(), case=None):
    """Arma el texto del panel. response = ResponseAudiometry del audiómetro,
    logo = CalculateLogo de las listas de palabras (o None), logo_state = el
    'playable' de ListWords ([dictando, dB, oído, con_mkg, dB ruido])."""
    case = case if case is not None else getattr(response, 'dbdata', None)
    if not case:
        return SIN_CASO
    audio = response.data['audio']
    lineas = _bloque_ahora(response, audio, logo, logo_state)
    lineas += _bloque_equipo(response, audio)
    lineas += _bloque_cruce(response, audio)
    lineas += _bloque_tonal(response, audio)
    lineas += _bloque_logo(logo, case, logo_state)
    lineas += _bloque_caso(case)
    lineas += _bloque_coherencia(case)
    return "\n".join(lineas)


class DebugMkgDialog(QDialog):
    """Ventana no modal con el reporte. Se refresca a mano o cada segundo,
    para poder mover perillas del audiómetro y ver el efecto al toque."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Depuración de enmascaramiento (docente)")
        self.resize(900, 640)
        style_dialog(self)

        self.texto = QPlainTextEdit(self)
        self.texto.setReadOnly(True)
        self.texto.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        fuente = QFont("Monospace")
        fuente.setStyleHint(QFont.StyleHint.TypeWriter)
        fuente.setPointSize(9)
        self.texto.setFont(fuente)

        self.btn_refresh = QPushButton("Actualizar", self)
        self.btn_refresh.clicked.connect(self.refresh)
        self.chk_auto = QCheckBox("Auto (1 s)", self)
        self.chk_auto.setChecked(True)
        self.chk_auto.toggled.connect(self._toggle_auto)
        self.btn_copy = QPushButton("Copiar", self)
        self.btn_copy.clicked.connect(self._copiar)

        barra = QHBoxLayout()
        barra.addWidget(self.btn_refresh)
        barra.addWidget(self.chk_auto)
        barra.addWidget(self.btn_copy)
        barra.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(barra)
        layout.addWidget(self.texto)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def _toggle_auto(self, activo):
        self.timer.start() if activo else self.timer.stop()

    def _copiar(self):
        QGuiApplication.clipboard().setText(self.texto.toPlainText())

    def refresh(self):
        # Conservar el scroll: con auto-refresh, saltar al inicio cada
        # segundo haría inservible la tabla de umbrales.
        barra = self.texto.verticalScrollBar()
        pos = barra.value()
        self.texto.setPlainText(self._reporte())
        barra.setValue(min(pos, barra.maximum()))

    def _reporte(self):
        subw = getattr(self.main_window, 'subw', None) or {}
        aud = subw.get("A")
        if aud is None:
            return SIN_CASO
        listas = subw.get("W")
        logo = getattr(listas.obj, 'prev', None) if listas is not None else None
        estado = getattr(listas.obj, 'playable', ()) if listas is not None else ()
        try:
            return build_report(aud.obj.response, logo, estado,
                                self.main_window.data_current)
        except Exception as exc:  # panel de depuración: nunca voltear la app
            return f"No se pudo armar el reporte: {exc!r}"
