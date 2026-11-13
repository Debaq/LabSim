"""
Acúfeno del paciente y lo que contesta en la tinnitumetría (técnica T03 de
la Bibliografía, H06 del libro).

El caso trae el bloque `Tinnitus` (ficha 10 del editor): lateralidad, tipo
de ruido, frecuencia, pulsátil, permanente. Lo que la ficha no fija lo
sortea acá, igual en cada apertura (stable_seed por caso): la sonoridad
(dB SL), el nivel mínimo de enmascaramiento (NME, dB SL) y la inhibición
residual. El docente puede fijarlos en la ficha; "auto" o vacío = sorteo.

Las cuatro partes de la técnica tienen su instrucción en el talkback
(comandos_voz.py) y el paciente responde así:

- Tono (`acufeno_cual_se_parece` + `¿Cuál se parece más?`): compara los
  estímulos que oyó desde la última pregunta (los tres últimos) y elige el
  más cercano en octavas a la frecuencia del acúfeno.
- Sonoridad (`acufeno_igual_fuerte`): levanta la mano cuando el estímulo
  llega a su umbral + la sonoridad, en el oído donde suena.
- NME (`acufeno_solo_el_mio`, "Escuche mi pitido. Avíseme cuando solo
  escuche el mío y no el suyo"): el estímulo sube y, cuando llega al NME en
  el oído del acúfeno a una octava o menos de él, dice "Ahora solo escucho
  el suyo". Antes había además "Hasta que no escuche su ruido"
  (`acufeno_deje_de_escuchar`, con la mano): era la misma medida y salió el
  2026-11-13.
- Inhibición residual: el alumno sube 15 dB desde el NME y lo deja un
  minuto (`acufeno_un_minuto`, o sin decir nada más). Con
  `¿Cómo está su ruido?` contesta según la inhibición del caso; pasado otro
  minuto, vuelve a como estaba salvo que la inhibición se mantenga. El
  minuto lo cuenta desde que el estímulo pasa el NME, con cualquiera de las
  dos instrucciones.

Sin acúfeno, el fallo se ve como en un paciente real: al terminar cualquiera
de las cuatro instrucciones reacciona ("¿Qué ruido? Yo no tengo ningún
ruido...", y si se insiste, "Yo no escucho ningún ruido"), a "¿Cuál se
parece más?" dice que no sabe con qué compararlo, y la mano no sube. El
pulsátil y el ocasional responden igual: la técnica dice que el pulsátil no
se iguala (lo marca el indicador), y el ocasional se toma como presente el
día del examen.
"""
import math
import random
import time

from core.rng import stable_seed

FRECUENCIAS = (125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000)

# Claves de la ficha (CaseBuilder::TINNITUS_*). Siseo se iguala con ruido;
# los demás, con tono.
RUIDOS_DE_RUIDO = frozenset({"Siseo"})
INHIBICIONES = ("negativa", "parcial", "total")

# Sorteo cuando la ficha no lo fija. La sonoridad del acúfeno suele quedar a
# pocos dB sobre el umbral; el NME, por encima de la sonoridad.
SONORIDAD_SL = (2, 10)
NME_SOBRE_SONORIDAD = (5, 15)
INHIBICION_PESOS = (("negativa", 25), ("parcial", 50), ("total", 25))
MANTIENE_PROB = 0.2

# Instrucciones y preguntas del talkback (claves de comandos_voz.py).
INSTR_TONO = "acufeno_cual_se_parece"
INSTR_SONORIDAD = "acufeno_igual_fuerte"
INSTR_SOLO_EL_MIO = "acufeno_solo_el_mio"   # el NME, y de ahí la inhibición residual
INSTR_INHIBICION = "acufeno_un_minuto"
INSTRUCCIONES = (INSTR_TONO, INSTR_SONORIDAD, INSTR_SOLO_EL_MIO, INSTR_INHIBICION)
DE_INHIBICION = (INSTR_SOLO_EL_MIO, INSTR_INHIBICION)
PREG_CUAL = "acufeno_cual"
PREG_COMO = "acufeno_como_esta"
PREGUNTAS = (PREG_CUAL, PREG_COMO)

# Lo que dice el paciente (resources/audio/paciente/<voz>/<clave>.mp3).
ORDINALES = ("elprimero", "elsegundo", "eltercero")
NO_TENGO = "notengoruido"
QUE_RUIDO = "queruido"          # la primera instrucción, sin acúfeno
NO_COMPARO = "nosecomparar"     # "¿Cuál se parece más?", sin acúfeno
NO_SE = "nose"
IGUAL = "igualqueantes"
MAS_BAJO = "seescuchamasbajito"
NO_LO_ESCUCHO = "yanoloescucho"
SOLO_EL_SUYO = "ahorasoloescuchoelsuyo"

# Estímulos del audiómetro (masking_params: 0 tono, 1 FM, 2 habla, 3 NBN,
# 4 ruido blanco, 5 speech noise, 6 ruido rosa).
_TONO, _FM, _HABLA, _NBN, _WN, _SN, _PN = range(7)
_DE_TONO = (_TONO, _FM)
_DE_COMPARACION = (_TONO, _FM, _NBN)
_DE_BANDA_ANCHA = (_WN, _SN, _PN)

# Cortes más cortos que esto son el mismo estímulo (el pulsado prende y
# apaga cada medio segundo).
JUNTAR_S = 1.5
# El minuto de la inhibición, con la tolerancia de quien mira el reloj.
MINUTO_S = 60
MINUTO_TOLERANCIA_S = 5
# El estímulo del NME y de la inhibición tapa el acúfeno a una octava o
# menos de él.
INHIBICION_OCTAVAS = 1.0


def presente(t) -> bool:
    """Si el paciente tiene acúfeno. Copia de CaseBuilder::tinnitusPresente:
    los casos de antes de la casilla 'presente' traen siempre un bloque, y
    el que quedó en el default que nadie tocó no era del caso."""
    if not isinstance(t, dict) or not t:
        return False
    if "presente" in t:
        return bool(t["presente"])
    return not (
        (t.get("lateralidad") or "craneal") == "craneal"
        and (t.get("ruido") or "Silbido") == "Silbido"
        and int(t.get("frecuencia") or FRECUENCIAS[0]) == FRECUENCIAS[0]
        and not t.get("pulsatil")
        and not t.get("permanente")
    )


def _fijo(valor, tipo):
    """El valor que fijó el docente, o None si lo dejó en auto."""
    if valor in (None, "", "auto"):
        return None
    try:
        return tipo(valor)
    except (TypeError, ValueError):
        return None


def octavas(f1, f2):
    return abs(math.log2(f1 / f2))


class Acufeno:
    """El acúfeno del caso, con lo que la ficha no fija ya sorteado."""

    def __init__(self, bloque, case_id):
        t = bloque if isinstance(bloque, dict) else {}
        self.presente = presente(t)
        self.pulsatil = bool(t.get("pulsatil"))
        self.permanente = bool(t.get("permanente"))
        self.lateralidad = t.get("lateralidad") or "craneal"
        self.ruido = t.get("ruido") or "Silbido"
        self.tipo = "ruido" if self.ruido in RUIDOS_DE_RUIDO else "tono"
        try:
            self.freq = int(t.get("frecuencia") or 4000)
        except (TypeError, ValueError):
            self.freq = 4000
        if self.freq not in FRECUENCIAS:
            self.freq = min(FRECUENCIAS, key=lambda f: octavas(f, self.freq))
        if self.lateralidad == "unilateral":
            self.oidos = (1,) if t.get("oido") == "oi" else (0,)
        else:
            self.oidos = (0, 1)
        predominio = t.get("predominio") or "igual"
        self.predominio = {"od": 0, "oi": 1}.get(predominio) if self.lateralidad == "bilateral" else None

        rng = random.Random(stable_seed(case_id, "acufeno"))
        sorteo_son = rng.randint(*SONORIDAD_SL)
        sorteo_nme = rng.randint(*NME_SOBRE_SONORIDAD)
        nombres, pesos = zip(*INHIBICION_PESOS)
        sorteo_inh = rng.choices(nombres, weights=pesos)[0]
        sorteo_man = rng.random() < MANTIENE_PROB

        self.sonoridad_sl = _fijo(t.get("sonoridad_sl"), int)
        self.sonoridad_sorteada = self.sonoridad_sl is None
        if self.sonoridad_sl is None:
            self.sonoridad_sl = sorteo_son
        self.nme_sl = _fijo(t.get("nme_sl"), int)
        self.nme_sorteado = self.nme_sl is None
        if self.nme_sl is None:
            self.nme_sl = self.sonoridad_sl + sorteo_nme
        inh = t.get("inhibicion")
        self.inhibicion = inh if inh in INHIBICIONES else sorteo_inh
        self.inhibicion_sorteada = inh not in INHIBICIONES
        man = t.get("inhibicion_mantiene")
        self.mantiene = {"si": True, "no": False}.get(man, sorteo_man)
        self.mantiene_sorteado = man not in ("si", "no")

    def oido_de_comparacion(self):
        """Dónde van los sonidos de comparación: el oído contrario si es de
        un lado, el más débil si es bilateral asimétrico; None = cualquiera."""
        if self.lateralidad == "unilateral":
            return 1 - self.oidos[0]
        if self.predominio is not None:
            return 1 - self.predominio
        return None

    def verdad(self):
        """Lo que el alumno debería encontrar, para el registro."""
        if not self.presente:
            return {"presente": False}
        return {
            "presente": True,
            "pulsatil": self.pulsatil,
            "permanente": self.permanente,
            "lateralidad": self.lateralidad,
            "oidos": list(self.oidos),
            "oido_comparacion": self.oido_de_comparacion(),
            "tipo": self.tipo,
            "ruido": self.ruido,
            "freq": self.freq,
            "sonoridad_sl": self.sonoridad_sl,
            "nme_sl": self.nme_sl,
            "inhibicion": self.inhibicion,
            "mantiene": self.mantiene,
            "sorteados": [k for k, s in (
                ("sonoridad_sl", self.sonoridad_sorteada), ("nme_sl", self.nme_sorteado),
                ("inhibicion", self.inhibicion_sorteada), ("mantiene", self.mantiene_sorteado),
            ) if s],
        }


class Tinnitumetria:
    """Lo que el paciente va notando durante la tinnitumetría.

    `umbral(oido, f_idx)` da su umbral aéreo en dB HL; `oidos(ch, audio)`,
    a qué oídos llega el canal (el Simultáneo llega a los dos). `audio` es
    el estado del audiómetro que arma ResponseAudiometry
    (stimOn/stim/int/output/freq).
    """

    def __init__(self, acufeno, umbral, oidos, reloj=time.monotonic):
        self.acufeno = acufeno
        self._umbral = umbral
        self._oidos = oidos
        self._reloj = reloj
        self.comparados = []    # [(stim, f_idx, oido)] desde la última pregunta
        self._corrida = None    # {'inicio', 'fin'} del estímulo de la inhibición
        self._reclamo = False   # ya dijo "¿qué ruido?"

    # ---- lo que suena ----------------------------------------------------

    def _canales(self, audio, stims):
        return [ch for ch in (0, 1) if audio["stimOn"][ch] and audio["stim"][ch] in stims]

    def _sl(self, audio, ch, oido, f_idx=None):
        f = audio["freq"] if f_idx is None else f_idx
        return audio["int"][ch] - self._umbral(oido, f)

    def nueva_comparacion(self):
        self.comparados = []

    def ante_instruccion(self):
        """Lo que dice al terminar una instrucción de tinnitumetría: nada si
        tiene acúfeno; si no, se extraña la primera vez y después lo repite."""
        if self.acufeno.presente:
            return None
        if not self._reclamo:
            self._reclamo = True
            return QUE_RUIDO
        return NO_TENGO

    def ver(self, audio, instruccion):
        """Cada cambio del equipo con una instrucción de tinnitumetría."""
        if instruccion == INSTR_TONO:
            for ch in self._canales(audio, _DE_COMPARACION):
                for o in self._oidos(ch, audio):
                    if self._sl(audio, ch, o) < 0:
                        continue
                    est = (audio["stim"][ch], audio["freq"], o)
                    if not self.comparados or self.comparados[-1] != est:
                        self.comparados.append(est)
                    break
        if instruccion in DE_INHIBICION:
            self._seguir_corrida(self.inhibe(audio))

    # ---- tono ------------------------------------------------------------

    def cual(self):
        """'¿Cuál se parece más a su ruido?' Vacía la comparación: la
        siguiente pregunta compara lo que se presente después."""
        comparados, self.comparados = self.comparados[-3:], []
        if not self.acufeno.presente:
            return NO_COMPARO, comparados
        if len(comparados) < 2:
            return NO_SE, comparados
        tipo_de = lambda s: "tono" if s in _DE_TONO else "ruido"  # noqa: E731

        def distancia(i):
            stim, f_idx, _ = comparados[i]
            d = octavas(FRECUENCIAS[f_idx], self.acufeno.freq)
            return d + (0.01 if tipo_de(stim) != self.acufeno.tipo else 0)

        mejor = min(range(len(comparados)), key=lambda i: (distancia(i), i))
        return ORDINALES[mejor], comparados

    # ---- sonoridad -------------------------------------------------------

    def iguala(self, audio):
        """El sonido ya suena tan fuerte como su acúfeno."""
        if not self.acufeno.presente:
            return False
        stims = _DE_COMPARACION + (_WN,)
        return any(self._sl(audio, ch, o) >= self.acufeno.sonoridad_sl
                   for ch in self._canales(audio, stims) for o in self._oidos(ch, audio))

    # ---- NME -------------------------------------------------------------

    def _cubre(self, audio, ch, oido, max_octavas, sl_min):
        stim = audio["stim"][ch]
        f_tin = FRECUENCIAS.index(self.acufeno.freq)
        if stim in _DE_BANDA_ANCHA:
            return self._sl(audio, ch, oido, f_tin) >= sl_min
        if octavas(FRECUENCIAS[audio["freq"]], self.acufeno.freq) > max_octavas:
            return False
        return self._sl(audio, ch, oido) >= sl_min

    # ---- inhibición residual ---------------------------------------------

    def inhibe(self, audio):
        """Lo que suena sirve para la inhibición: en cada oído del acúfeno,
        a una octava o menos de él, sobre el NME."""
        if not self.acufeno.presente:
            return False
        canales = self._canales(audio, _DE_COMPARACION + _DE_BANDA_ANCHA)
        return bool(canales) and all(
            any(o in self._oidos(ch, audio)
                and self._cubre(audio, ch, o, INHIBICION_OCTAVAS, self.acufeno.nme_sl)
                for ch in canales)
            for o in self.acufeno.oidos)

    def solo_el_suyo(self):
        """'Avíseme cuando solo escuche el mío': lo dice una vez por
        corrida, cuando el estímulo llega a taparle el acúfeno. Bajar y
        volver a subir (más de JUNTAR_S) es otra corrida y lo vuelve a
        decir; el pulsado no."""
        c = self._corrida
        if not self.acufeno.presente or c is None or c["fin"] is not None or c.get("avisado"):
            return None
        c["avisado"] = True
        return SOLO_EL_SUYO

    def _seguir_corrida(self, sirve):
        ahora = self._reloj()
        c = self._corrida
        if sirve:
            if c is None or (c["fin"] is not None and ahora - c["fin"] > JUNTAR_S):
                self._corrida = {"inicio": ahora, "fin": None}
            elif c["fin"] is not None:
                c["fin"] = None   # un corte del pulsado: sigue la misma
        elif c is not None and c["fin"] is None:
            c["fin"] = ahora

    def como_esta(self, audio):
        """'¿Cómo está su ruido ahora?'"""
        if not self.acufeno.presente:
            return NO_TENGO
        c = self._corrida
        if c is None:
            return IGUAL
        if c["fin"] is None:
            # todavía suena: lo tapa, si llega al NME
            return NO_LO_ESCUCHO if self.inhibe(audio) else IGUAL
        if c["fin"] - c["inicio"] < MINUTO_S - MINUTO_TOLERANCIA_S:
            return IGUAL
        if self._reloj() - c["fin"] >= MINUTO_S and not self.acufeno.mantiene:
            return IGUAL
        return {"negativa": IGUAL, "parcial": MAS_BAJO, "total": NO_LO_ESCUCHO}[self.acufeno.inhibicion]

    def corrida(self):
        """La última corrida del estímulo de la inhibición, para el registro."""
        c = self._corrida
        if c is None:
            return None
        fin = c["fin"] if c["fin"] is not None else self._reloj()
        return {"duracion_s": round(fin - c["inicio"], 1),
                "desde_s": None if c["fin"] is None else round(self._reloj() - c["fin"], 1)}
