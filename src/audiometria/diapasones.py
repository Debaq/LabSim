"""Lo que oye el paciente con un diapasón, sin interfaz (Acumetria.py lo usa).

El diapasón golpeado parte con un nivel y se apaga de a poco (NIVEL_*,
CAIDA_DB_S). Cada posición se oye mientras el nivel esté sobre el umbral de
esa vía en el audiograma del caso (Aerea/Osea, en 500 y 1000 Hz: los
diapasones de 512 y 1024 Hz):

- frente al pabellón (aire): el umbral aéreo de ese oído;
- apoyado en la mastoides (hueso): vibra todo el cráneo y responde la mejor
  cóclea, la de ese lado o la del otro (ATENUACION_OSEA_DB). Así sale solo
  el falso negativo de un oído muerto: por aire nada, por hueso sí (lo oye
  el otro).

Lo que manda es lo que marcó el docente en el caso (cases.data.Rinne y
Weber, ver CaseBuilder.php): si el audiograma da otro Rinne, se ajustan los
tiempos para que el paciente conteste lo del caso. Sin Rinne ni Weber en el
caso no hay diapasón que sirva: suena con armónicos (disponible() False),
igual que el otoscopio sin batería cuando el caso no trae fotos. No se
inventa una respuesta normal.

Los niveles y la caída son del modelo, no de una norma: dan tiempos del
orden de los que se ven en la consulta (decenas de segundos) y el orden
correcto entre aire y hueso.
"""
import math

FRECUENCIAS = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000]
DIAPASONES = (("500", "512 Hz"), ("1000", "1024 Hz"))
INDICE = {"500": FRECUENCIAS.index(500), "1000": FRECUENCIAS.index(1000)}
NIVEL_AIRE_DB = 70.0       # frente al pabellón, recién golpeado
NIVEL_HUESO_DB = 45.0      # apoyado en el hueso, recién golpeado
CAIDA_DB_S = 1.5           # cuánto se apaga por segundo
ATENUACION_OSEA_DB = 5.0   # del hueso a la cóclea del otro lado
POSITIVO_MIN = 1.3         # en un Rinne positivo el aire dura al menos esto más
NEGATIVO_MAX = 0.7         # en uno negativo, como mucho esto


def _umbral(lista, i, oido):
    """Umbral (dB HL) de esa frecuencia y oído; None si no hay."""
    try:
        valor = lista[i][0 if oido == "od" else 1]
    except (IndexError, TypeError):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _segundos(nivel, umbral):
    if umbral is None:
        return 0.0
    return max(0.0, (nivel - umbral) / CAIDA_DB_S)


class ModeloDiapasones:

    def __init__(self, caso):
        self.caso = caso or {}

    def disponible(self):
        """Hay Rinne y Weber en el caso: si no, el diapasón suena con armónicos."""
        return bool(self.caso.get("Rinne")) and bool(self.caso.get("Weber"))

    def rinne(self, hz, oido):
        return ((self.caso.get("Rinne") or {}).get(hz) or {}).get(oido)

    def weber(self, hz):
        return (self.caso.get("Weber") or {}).get(hz)

    def tiempos(self, hz, oido):
        """(segundos por aire, segundos por hueso) de ese oído con el
        diapasón recién golpeado, ajustados al Rinne del caso."""
        i = INDICE[hz]
        otro = "oi" if oido == "od" else "od"
        aerea = self.caso.get("Aerea") or []
        osea = self.caso.get("Osea") or []
        t_aire = _segundos(NIVEL_AIRE_DB, _umbral(aerea, i, oido))
        candidatos = [u for u in (_umbral(osea, i, oido),) if u is not None]
        otro_umbral = _umbral(osea, i, otro)
        if otro_umbral is not None:
            candidatos.append(otro_umbral + ATENUACION_OSEA_DB)
        t_hueso = _segundos(NIVEL_HUESO_DB, min(candidatos) if candidatos else None)
        valor = self.rinne(hz, oido)
        if valor == "falso_negativo":
            # Por aire no lo oye; por hueso sí, con el otro oído
            t_aire = 0.0
            t_hueso = t_hueso or 15.0
        elif valor == "positivo" and t_aire < t_hueso * POSITIVO_MIN:
            t_hueso = t_hueso or 10.0
            t_aire = max(t_aire, t_hueso * 1.5)
        elif valor == "negativo" and t_aire > t_hueso * NEGATIVO_MAX:
            t_hueso = max(t_hueso, 10.0)
            t_aire = min(t_aire, t_hueso * 0.5)
        return round(t_aire, 1), round(t_hueso, 1)

    def tiempo_weber(self, hz):
        """Segundos que se oye apoyado en la línea media: lo que dura en el
        mejor de los dos huesos."""
        return max(self.tiempos(hz, "od")[1], self.tiempos(hz, "oi")[1])


def oye(segundos_que_dura, segundos_desde_golpe):
    """¿Lo sigue oyendo? (el diapasón ya lleva ese tiempo apagándose)."""
    return segundos_desde_golpe < segundos_que_dura


def vibracion(segundos_desde_golpe):
    """0-1: cuánto vibra todavía el diapasón (para la barra), con la misma
    caída: llega a 0 cuando bajó NIVEL_AIRE_DB."""
    return max(0.0, 1.0 - segundos_desde_golpe * CAIDA_DB_S / NIVEL_AIRE_DB)


def segundos_que_quedan(dura, desde_golpe):
    return max(0.0, dura - desde_golpe)


def redondear(segundos):
    return int(math.floor(segundos + 0.5))
