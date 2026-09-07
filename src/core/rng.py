"""Semillas reproducibles para los generadores sintéticos.

Vivía en oae/generators/base.py; se movió acá cuando ABR pasó a necesitar
lo mismo (ver ABR_generator.ABR_Curve). oae/generators/base.py las
reexporta, así que los generadores OAE siguen importando de donde siempre.
"""
import hashlib


def stable_seed(*parts) -> int:
    """Seed reproducible ENTRE ejecuciones de la app (0 .. 2**32-1).

    hash() de Python saltea el hash de str/bytes con PYTHONHASHSEED, que es
    aleatorio por proceso: con hash() el mismo paciente y los mismos
    parámetros dan otra captura cada vez que se abre LabSim. Eso no es
    "otra realización de ruido" para el alumno -- puede mover un PASS/REFER
    borderline, y en SOAE cambiaba directamente si el oído tenía emisiones.
    blake2b es determinística en cualquier proceso y máquina; digest_size=4
    ya deja el entero en el rango que acepta np.random.default_rng.
    """
    raw = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(raw, digest_size=4).digest(), "big")


def case_fingerprint(case: dict | None) -> str:
    """Clave estable del perfil del oído, ordenada y en texto.

    El caso llega como dict (no se puede hashear directo) y se ordena para
    que el mismo caso dé siempre la misma clave y dos casos distintos den
    capturas distintas.
    """
    if not case:
        return ""
    partes = []
    for k, v in sorted(case.items()):
        if isinstance(v, dict):
            v = ";".join(f"{a}={b}" for a, b in sorted(v.items()))
        partes.append(f"{k}={v}")
    return "|".join(partes)
