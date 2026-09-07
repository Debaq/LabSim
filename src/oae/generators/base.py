"""Base para los generadores sintéticos OAE.

Carga el JSON normativo por defecto desde resources/oae/normative_data.json.
Si hay override del curso en core.app_config_store[normative_data.<tipo>] lo
mezcla con los defaults (los overrideados ganan, pero las keys que falten
caen al default bundled -- mismo patrón que ABR).
"""
import json

import numpy as np

from core.base import context


# Recursos empaquetados: context.get_resource resuelve tanto en dev como en
# PyInstaller. Buscamos resources/oae/normative_data.json desde la raíz del
# proyecto; context ya maneja el caso frozen.
_NORMATIVE_PATH = "oae/normative_data.json"


def _deep_merge(base: dict, override: dict) -> dict:
    """Override gana, recursivo en dicts. Override NO es mutado."""
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_normative(kind: str):
    """Devuelve dict normativo efectivo para `kind` ∈ {"teoae","dpoae","sfoae"}.

    1) Lee bundled: resources/oae/normative_data.json[kind]["default"]
    2) Si app_config_store tiene "normative_data.<kind>", mergea sobre default.
    3) Si ni siquiera bundled se puede cargar, raise -- los widgets deben
       cortar antes de pedir capturas (memoria no_synthetic_fallback_data:
       sin datos reales, no generar nada).
    """
    from core import app_config_store

    resource = context.get_resource(_NORMATIVE_PATH)
    with open(resource, "r", encoding="utf-8") as f:
        bundled = json.load(f)
    if kind not in bundled or "default" not in bundled[kind]:
        raise RuntimeError(
            f"normative_data.json no tiene sección '{kind}'. Revisar "
            f"{resource}."
        )
    defaults = bundled[kind]["default"]
    override = app_config_store.get(f"normative_data.{kind}")
    return _deep_merge(defaults, override or {})


class OaeGeneratorBase:
    """Síntesis TEOAE/DPOAE/SFOAE 100% sintética (sin audio device).

    Decisión de diseño: la respuesta varía por oído y por nivel de estímulo
    vía seed derivado de esos parámetros (no usamos el mismo "caso normal"
    fijo en cada captura - memoria no_fixed_teaching_defaults).
    """

    SAMPLE_RATE = 44100

    def __init__(self, kind: str, seed: int | None = None):
        self.normative = load_normative(kind)
        self.kind = kind
        # Seed para que la misma config dé la misma curva dentro de una
        # sesión (consistente entre sweeps) pero cambie entre oídos/niveles.
        self._seed = seed if seed is not None else self._seed_from_params()


def _case_num(case: dict | None, key: str, default: float) -> float:
    """Lee un número del perfil EOA del caso, tolerando casos viejos.

    Un caso guardado antes del perfil por frecuencia solo trae type/umbral:
    ahí cada clave nueva cae a su default y el comportamiento es el de
    antes (atenuación solo por patología).
    """
    if not case:
        return default
    try:
        value = case.get(key)
        return default if value is None else float(value)
    except (AttributeError, TypeError, ValueError):
        return default


def oae_freq_delta_db(case: dict | None, freq_hz: float | None) -> float:
    """dB de caída extra en `freq_hz` según el perfil por frecuencia que el
    docente cargó en el caso (cases.data['EOAS'][oido]['desviaciones'],
    {Hz: dB}). Positivo = OEA más chica en esa zona.

    Interpolado en log-frecuencia y extendido plano fuera del rango, para
    que las tres pruebas (bandas TEOAE, f2 del DP-grama, sintonía SFOAE)
    lean el MISMO perfil aunque midan en frecuencias distintas: una muesca
    en 4 kHz aparece en las tres, como en un paciente real.
    """
    if not case or freq_hz is None:
        return 0.0
    try:
        perfil = case.get("desviaciones") or {}
    except AttributeError:
        return 0.0
    puntos = []
    for k, v in perfil.items():
        try:
            puntos.append((float(k), float(v)))
        except (TypeError, ValueError):
            continue
    if not puntos:
        return 0.0
    puntos.sort()
    freqs = np.array([p[0] for p in puntos], dtype=float)
    deltas = np.array([p[1] for p in puntos], dtype=float)
    return float(np.interp(np.log2(float(freq_hz)), np.log2(freqs), deltas))


def oae_probe_fit(case: dict | None) -> float | None:
    """Sello de sonda objetivo (0-1) configurado para este oído, o None.

    None = el caso no lo trae (caso viejo o modo demo): el probe check
    sortea un sello bueno como antes y no se penaliza el nivel.
    """
    if not case:
        return None
    try:
        pct = case.get("sello_pct")
    except AttributeError:
        return None
    if pct is None:
        return None
    try:
        return float(min(100.0, max(5.0, float(pct)))) / 100.0
    except (TypeError, ValueError):
        return None


def oae_probe_loss_db(case: dict | None) -> float:
    """Pérdida de nivel por sello imperfecto (dB, >= 0).

    Mismo 20*log10(fit) que muestra el probe check: con la sonda floja
    entra menos estímulo y vuelve menos emisión, así que el registro sale
    peor sin que la cóclea tenga nada.
    """
    fit = oae_probe_fit(case)
    return 0.0 if fit is None else float(-20.0 * np.log10(fit))


def oae_noise_offset_db(case: dict | None) -> float:
    """dB a sumar al piso de ruido: paciente inquieto, llanto, deglución.

    Sube el piso sin tocar la emisión -- es el REFER "por ruido" que el
    alumno tiene que distinguir del REFER coclear.
    """
    return _case_num(case, "ruido_db", 0.0)


def oae_variability_db(case: dict | None, default: float) -> float:
    """Estructura fina / variabilidad biológica (dB) de este oído."""
    return max(0.0, _case_num(case, "variabilidad_db", default))


def oae_attenuation_db(case_ear: dict | None, freq_hz: float | None = None) -> float:
    """Atenuación (dB) a restar de la amplitud/nivel esperado de la OEA
    según lo que el docente configuró para ese oído en el caso
    (cases.data['EOAS']['OD'/'OI']).

    Suma tres cosas:

    1) Patología (`type` + `umbral`, mismo shape que ABR):
       - normal: sin atenuación.
       - coclear: daño de células ciliadas externas -> clínicamente la OEA
         ya no es rescatable por sobre ~35-40 dB HL, así que la pendiente es
         pronunciada (3 dB de atenuación por dB de umbral sobre 20 dB HL)
         para que el REFER aparezca en ese rango, no recién a 55+ dB HL.
       - transmission: la pérdida conductiva atenúa la ida Y la vuelta del
         sonido por el oído medio (~2.5x el umbral aprox.).
       - neural: cóclea intacta (neuropatía/retrococlear) -> la OEA se
         mantiene normal aunque el umbral conductual esté elevado. Es el
         contraste clínico clave con ABR (que sí sale alterado en 'neural').
    2) `atten_db`: atenuación pareja extra que el docente puede fijar a mano,
       más la pérdida por sello de sonda (ver oae_probe_loss_db).
    3) El perfil por frecuencia, si el llamador pasa `freq_hz` (ver
       oae_freq_delta_db) -- así una muesca en 4 kHz no aplana toda la curva.
    """
    if not case_ear:
        return 0.0
    tipo = case_ear.get("type", "normal")
    umbral = float(case_ear.get("umbral", 20) or 0)
    if tipo == "coclear":
        patologia = max(0.0, umbral - 20.0) * 3.0
    elif tipo == "transmission":
        patologia = max(0.0, umbral) * 2.5
    else:
        patologia = 0.0
    return (patologia
            + _case_num(case_ear, "atten_db", 0.0)
            + oae_probe_loss_db(case_ear)
            + oae_freq_delta_db(case_ear, freq_hz))
