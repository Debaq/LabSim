"""Curva de logoaudiometría (desempeño-intensidad) y rollover del caso.

Es LA curva: la misma función está en el backend
(labsim_backend/src/CaseCharts.php::pctLogo, para el PDF) y en el editor
(labsim_backend/public/js/case/logogram.js). El rollover (RI) sale del
perfil del caso igual que en CaseProfile::rolloverIndex/rolloverDeCaso.
Si se cambia algo acá, se cambia en los otros dos: tests/test_logo_curva.py
y labsim_backend/tests/test_case_profile.php comparten los números de los
pacientes de práctica 33-42. Ver docs/decisiones.md, "Logoaudiometría: la
curva anclada al SRT" (2026-10-15).

Forma, sobre el máximo del caso (UMD: percentage a int dB HL):
  - el SRT del caso es donde la curva pasa la MITAD de su máximo (50 % en un
    oído que llega a 100): el SRT que mide el alumno con palabras cae sobre
    el de la ficha, que es el promedio tonal;
  - pie: 0 % hasta PIE_DB bajo el SRT (o desde el SDT, si viene más abajo);
  - dos tramos cúbicos (Hermite) que se juntan en el SRT con pendiente
    PENDIENTE (fracción del máximo por dB) y llegan al máximo planos;
  - pasado el máximo, meseta, o rollover si RI > 0: baja suave hasta
    máximo * (1 - RI) en ROLL_DB dB, o en el techo del canal de habla.
"""

# --- Constantes de la curva: las mismas de CaseCharts (LOGO_*) ---------
PIE_DB = 10.0
PENDIENTE = 0.05
ROLL_DB = 25.0
TECHO_DB = 100.0

# --- Constantes del rollover: las mismas de CaseProfile ----------------
FREQUENCIES = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000]
CORE_FREQS = [500, 1000, 2000, 4000]
SPEECH_WEIGHTS = {500: 0.15, 1000: 0.25, 2000: 0.30, 4000: 0.30}
SN_NORMAL_DB = 25.0
SIN_RESPUESTA_DB = 130.0
MAX_AUDIOMETRO_DB = 120.0
LOGO_CCE_SLOPE = 0.8
LOGO_CCE_KNEE_DB = 20.0
LOGO_RETRO_SLOPE = 1.8
LOGO_RETRO_KNEE_DB = 10.0
LOGO_RI_COCLEAR = 0.15
LOGO_RI_RETRO_DB = 80.0
LOGO_RI_RETRO_MAX = 0.75
LOGO_RI_MAX = 0.9
DEFAULT_CCE_PCT = 100.0
# CaseBuilder::ABR_NEURAL_DEFAULTS == NEURAL_PARAM_DEFAULTS del generador ABR
NEURAL_DEFAULTS = {
    'i_iii_ms': 0.2,
    'iii_v_ms': 0.2,
    'global_delay_ms': 0.0,
    'bloqueo': 'ninguno',
    'v_i_factor': 0.45,
    'microfonica': 'normal',
    'desincronia': 'ninguna',
    'sensibilidad_tasa': 'severa',
}


def pct_logo(cfg, db):
    """% de palabras a `db` dB HL. Espejo exacto de CaseCharts::pctLogo.

    cfg: {'sdt', 'srt', 'umd_int', 'umd_pct', 'ri'} de un oído.
    """
    pmax = max(0.0, min(100.0, float(cfg['umd_pct'])))
    if pmax <= 0.0:
        return 0.0
    lmax = float(cfg['umd_int'])
    l50 = min(float(cfg['srt']), lmax - 5.0)
    lon = min(float(cfg['sdt']), l50 - PIE_DB)
    h_a = l50 - lon
    h_b = lmax - l50
    k = min(PENDIENTE, 1.5 / h_a, 1.5 / h_b)

    if db <= lon:
        s = 0.0
    elif db <= l50:
        t = (db - lon) / h_a
        s = 0.5 * (3 * t ** 2 - 2 * t ** 3) + h_a * k * (t ** 3 - t ** 2)
    elif db <= lmax:
        t = (db - l50) / h_b
        s = (0.5 * (2 * t ** 3 - 3 * t ** 2 + 1) + h_b * k * (t ** 3 - 2 * t ** 2 + t)
             + (3 * t ** 2 - 2 * t ** 3))
    else:
        s = 1.0
        ri = max(0.0, min(1.0, float(cfg.get('ri', 0.0) or 0.0)))
        ltop = min(lmax + ROLL_DB, TECHO_DB)
        if ri > 0.0 and ltop > lmax:
            t = min(1.0, (db - lmax) / (ltop - lmax))
            s = 1.0 - ri * (3 * t ** 2 - 2 * t ** 3)
    return pmax * max(0.0, min(1.0, s))


def _par(lista, side, default=None):
    try:
        valor = lista[side]
    except (TypeError, IndexError, KeyError):
        return default
    return default if valor is None else valor


def fletcher(aerea, side):
    """Mejores 2 de 500/1000/2000 Hz, al piso de 5 (CaseBuilder::fletcherAvg)."""
    valores = sorted(float(p[side]) for p in (aerea or [])[2:5])[:2]
    if not valores:
        return None
    return (sum(valores) / len(valores)) // 5 * 5


def cfg_oido(data, side, ri):
    """La configuración de la curva de un oído desde cases.data.

    Lo que guarda la ficha manda (SDT, SRT, UMD). Un caso sin SRT usa el
    SDT y, sin ninguno de los dos, el promedio de Fletcher de su propio
    audiograma: es un dato del caso, no un valor normal inventado.
    """
    umd = (data.get('UMD') or [{}, {}])[side] or {}
    srt = _par(data.get('SRT'), side)
    sdt = _par(data.get('SDT'), side)
    if srt is None:
        srt = sdt
    if srt is None:
        srt = fletcher(data.get('Aerea') or data.get('Aerea_mkg'), side)
    if sdt is None:
        sdt = srt
    return {
        'sdt': float(sdt),
        'srt': float(srt),
        'umd_int': float(umd['int']),
        'umd_pct': float(umd['percentage']),
        'ri': float(ri),
    }


# --- Rollover: espejo de CaseProfile ------------------------------------

def _normalize_retro(retro):
    retro = retro if isinstance(retro, dict) else {}
    out = {}
    for clave, default in NEURAL_DEFAULTS.items():
        valor = retro.get(clave, default)
        if valor is None:
            valor = default
        out[clave] = str(valor) if isinstance(default, str) else float(valor)
    return out


def _infer_cce(abr, eoas):
    if eoas.get('type') == 'neural':
        return 0.0
    if abr.get('type') == 'neural' and 'type' not in eoas:
        return 0.0
    return DEFAULT_CCE_PCT


def _perfil(data, lado):
    """cce_pct y retro de un oído, como CaseProfile::normalize."""
    perfil = data.get('Perfil') if isinstance(data.get('Perfil'), dict) else {}
    lado_p = perfil.get(lado) if isinstance(perfil.get(lado), dict) else {}
    abr = (data.get('ABR') or {}).get(lado) if isinstance(data.get('ABR'), dict) else None
    eoas = (data.get('EOAS') or {}).get(lado) if isinstance(data.get('EOAS'), dict) else None
    abr = abr if isinstance(abr, dict) else {}
    eoas = eoas if isinstance(eoas, dict) else {}
    cce = lado_p.get('cce_pct')
    cce = max(0.0, min(100.0, float(cce))) if cce is not None else _infer_cce(abr, eoas)
    retro = lado_p.get('retro') if isinstance(lado_p.get('retro'), dict) else None
    if retro is None:
        retro = abr.get('neural') if isinstance(abr.get('neural'), dict) else {}
    return cce, _normalize_retro(retro)


def _retro_activo(r):
    if r['bloqueo'] != 'ninguno' or r['desincronia'] != 'ninguna' or r['microfonica'] != 'normal':
        return True
    for clave in ('i_iii_ms', 'iii_v_ms', 'global_delay_ms'):
        if r[clave] > NEURAL_DEFAULTS[clave] + 1e-9:
            return True
    return r['v_i_factor'] < NEURAL_DEFAULTS['v_i_factor'] - 1e-9


def _decompose_sn(air_pairs, bone_pairs, side):
    """Componente sensorioneural por Hz y frecuencias sin respuesta aérea
    (la parte de CaseProfile::decompose que usa el rollover)."""
    sn = {}
    sin_resp = []
    for i, hz in enumerate(FREQUENCIES):
        air = float(_par(air_pairs[i] if i < len(air_pairs) else None, side, 0) or 0)
        bone_raw = _par(bone_pairs[i] if i < len(bone_pairs) else None, side)
        bone = air if bone_raw is None else float(bone_raw)
        if air >= SIN_RESPUESTA_DB:
            sin_resp.append(hz)
            air = MAX_AUDIOMETRO_DB
        if bone >= SIN_RESPUESTA_DB:
            bone = air
        sn[hz] = min(bone, air)
    return sn, sin_resp


def rollover_index(sn, sin_resp, cce_pct, retro):
    """RI del oído. Espejo de CaseProfile::rolloverIndex."""
    if len(set(sin_resp) & {500, 1000, 2000}) >= 2:
        return 0.0
    cce_pct = max(0.0, min(100.0, cce_pct))
    sn_discrim = (sum(sn[hz] * w for hz, w in SPEECH_WEIGHTS.items())
                  / sum(SPEECH_WEIGHTS.values()))
    cce = sn_discrim * cce_pct / 100.0
    retro_sn = sn_discrim - cce
    por_retro = max(0.0, retro_sn - LOGO_RETRO_KNEE_DB) * LOGO_RETRO_SLOPE
    if _retro_activo(retro):
        por_retro += 20.0
    coclear = (LOGO_RI_COCLEAR * cce_pct / 100.0
               if max(sn[hz] for hz in CORE_FREQS) > SN_NORMAL_DB else 0.0)
    retro_ri = min(LOGO_RI_RETRO_MAX, por_retro / LOGO_RI_RETRO_DB)
    ri = min(LOGO_RI_MAX, coclear + retro_ri)
    # round() de PHP: la mitad se va para arriba (el de Python no)
    return int(ri * 100 + 0.5 + 1e-9) / 100.0


def rollover_de_caso(data):
    """[RI OD, RI OI] de un cases.data. Espejo de CaseProfile::rolloverDeCaso."""
    air = data.get('Aerea') if isinstance(data.get('Aerea'), list) else []
    bone = data.get('Osea') if isinstance(data.get('Osea'), list) else []
    out = []
    for side, lado in enumerate(('OD', 'OI')):
        cce, retro = _perfil(data, lado)
        sn, sin_resp = _decompose_sn(air, bone, side)
        out.append(rollover_index(sn, sin_resp, cce, retro))
    return out


def ri_medido(curva, desde_db):
    """RI que mide quien recorre la curva {dB: %}: (máx - mín) / máx desde
    el máximo hacia arriba (hasta donde llegue la curva)."""
    niveles = sorted(db for db in curva if db >= desde_db)
    if not niveles:
        return 0.0
    pmax = max(curva[db] for db in niveles)
    if pmax <= 0:
        return 0.0
    imax = min(db for db in niveles if curva[db] == pmax)
    pmin = min(curva[db] for db in niveles if db >= imax)
    return (pmax - pmin) / pmax
