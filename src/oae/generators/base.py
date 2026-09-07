"""Base para los generadores sintéticos OAE.

Carga el JSON normativo por defecto desde resources/oae/normative_data.json.
Si hay override del curso en core.app_config_store[normative_data.<tipo>] lo
mezcla con los defaults (los overrideados ganan, pero las keys que falten
caen al default bundled -- mismo patrón que ABR).
"""
import json
from pathlib import Path

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


def oae_attenuation_db(case_ear: dict | None) -> float:
    """Atenuación (dB) a restar de la amplitud/nivel esperado de la OEA
    según la patología que el docente configuró para ese oído en el caso
    (cases.data['EOAS']['OD'/'OI'], mismo shape que 'type'/'umbral' de ABR).

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
    """
    if not case_ear:
        return 0.0
    tipo = case_ear.get("type", "normal")
    umbral = float(case_ear.get("umbral", 20) or 0)
    if tipo == "coclear":
        return max(0.0, umbral - 20.0) * 3.0
    if tipo == "transmission":
        return max(0.0, umbral) * 2.5
    return 0.0
