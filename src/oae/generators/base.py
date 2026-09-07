"""Base para los generadores sintéticos OAE.

Carga el JSON normativo por defecto desde resources/oae/normative_data.json.
Si hay override del curso en core.app_config_store[normative_data.<tipo>] lo
mezcla con los defaults (los overrideados ganan, pero las keys que falten
caen al default bundled -- mismo patrón que ABR).
"""
import json

import numpy as np

from core.base import context
from core.rng import case_fingerprint, stable_seed  # noqa: F401


# Recursos empaquetados: context.get_resource resuelve tanto en dev como en
# PyInstaller. Buscamos resources/oae/normative_data.json desde la raíz del
# proyecto; context ya maneja el caso frozen.
_NORMATIVE_PATH = "oae/normative_data.json"


# stable_seed/case_fingerprint viven en core.rng desde que ABR tambien los
# usa (ver ABR_generator). Se reexportan aca para no tocar los imports de
# los 4 generadores OAE ni los tests que los importan desde este modulo.

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
    """Devuelve dict normativo efectivo para `kind` ∈ {"teoae","dpoae","soae","sfoae"}.

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
    """Síntesis TEOAE/DPOAE/SOAE/SFOAE 100% sintética (sin audio device).

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


# Tope de la atenuación por patología. Una emisión normal ronda 8-15 dB
# sobre un piso de ruido de -20: 45 dB de atenuación ya la deja muy por
# debajo del piso (AUSENTE en cualquier prueba), y más que eso no cambia
# nada en pantalla.
MAX_PATHOLOGY_ATTEN_DB = 45.0


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
    que las cuatro pruebas (bandas TEOAE, f2 del DP-grama, sintonía SFOAE y
    los picos SOAE) lean el MISMO perfil aunque midan en frecuencias
    distintas: una muesca en 4 kHz aparece en todas, como en un paciente
    real.
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

    None = el caso no lo trae (caso viejo, guardado antes del perfil por
    oído): el probe check sortea un sello bueno como antes y no se
    penaliza el nivel.
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
       - coclear: daño de células ciliadas externas. 1.2 dB de atenuación
         por dB de umbral sobre 15 dB HL, así la OEA sale presente pero
         reducida en 20-25 dB HL, parcial en 30, y ausente sobre 35-40 dB
         HL (que es donde la clínica la da por perdida). Con los 3 dB/dB
         anteriores el salto de "presente" a "ausente" ocurría en 7 dB de
         umbral (20->27): no había forma de armar una coclear leve,
         moderada y severa que se vieran distintas en pantalla.
       - transmission: la pérdida conductiva atenúa la ida Y la vuelta del
         sonido por el oído medio (2 dB/dB sobre 8 dB HL): una conductiva
         mínima deja la OEA presente y chica, una de 20+ dB la borra.
       - neural: cóclea intacta (neuropatía/retrococlear) -> la OEA se
         mantiene normal aunque el umbral conductual esté elevado. Es el
         contraste clínico clave con ABR (que sí sale alterado en 'neural').
    2) `atten_db`: atenuación pareja extra que el docente puede fijar a mano,
       más la pérdida por sello de sonda (ver oae_probe_loss_db).
    3) El perfil por frecuencia, si el llamador pasa `freq_hz` (ver
       oae_freq_delta_db) -- así una muesca en 4 kHz no aplana toda la curva.

    La atenuación por patología se topa en MAX_PATHOLOGY_ATTEN_DB: pasado
    ese punto la OEA ya está bajo el piso de ruido, y seguir restando solo
    daba números irreales (un umbral de 70 daba 150 dB de atenuación).
    """
    if not case_ear:
        return 0.0
    tipo = case_ear.get("type", "normal")
    umbral = float(case_ear.get("umbral", 20) or 0)
    if tipo == "coclear":
        patologia = min(max(0.0, umbral - 15.0) * 1.2, MAX_PATHOLOGY_ATTEN_DB)
    elif tipo == "transmission":
        patologia = min(max(0.0, umbral - 8.0) * 2.0, MAX_PATHOLOGY_ATTEN_DB)
    else:
        patologia = 0.0
    return (patologia
            + _case_num(case_ear, "atten_db", 0.0)
            + oae_probe_loss_db(case_ear)
            + oae_freq_delta_db(case_ear, freq_hz))
